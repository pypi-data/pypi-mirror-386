from typing import Generator, Optional, List, Dict, Any, Union
import queue
import threading
from pathlib import Path

from nexaai.common import ModelConfig, GenerationConfig, MultiModalMessage, PluginID
from nexaai.binds import vlm_bind, common_bind
from nexaai.runtime import _ensure_runtime
from nexaai.vlm import VLM
from nexaai.base import ProfilingData
from nexaai.runtime_error import ContextLengthExceededError, GenerationError

# Error codes from ml.h
ML_SUCCESS = 0
ML_ERROR_LLM_TOKENIZATION_CONTEXT_LENGTH = -200004


class PyBindVLMImpl(VLM):
    def __init__(self, handle: any, m_cfg: ModelConfig = ModelConfig()):
        """Private constructor, should not be called directly."""
        super().__init__(m_cfg)
        self._handle = handle  # This is a py::capsule
        self._profiling_data = None

    @classmethod
    def _load_from(cls,
                   local_path: str,
                   mmproj_path: str = None,
                   model_name: Optional[str] = None,
                   m_cfg: ModelConfig = ModelConfig(),
                   plugin_id: Union[PluginID, str] = PluginID.LLAMA_CPP,
                   device_id: Optional[str] = None
        ) -> 'PyBindVLMImpl':
        """Load VLM model from local path.
        
        Args:
            local_path: Path to the main model file
            mmproj_path: Path to the multimodal projection file
            m_cfg: Model configuration
            plugin_id: Plugin identifier
            device_id: Optional device ID (not used in current binding)
            
        Returns:
            PyBindVLMImpl instance
        """
        _ensure_runtime()

        config = common_bind.ModelConfig()

        config.n_ctx = m_cfg.n_ctx
        if m_cfg.n_threads is not None:
            config.n_threads = m_cfg.n_threads
        if m_cfg.n_threads_batch is not None:
            config.n_threads_batch = m_cfg.n_threads_batch
        if m_cfg.n_batch is not None:
            config.n_batch = m_cfg.n_batch
        if m_cfg.n_ubatch is not None:
            config.n_ubatch = m_cfg.n_ubatch
        if m_cfg.n_seq_max is not None:
            config.n_seq_max = m_cfg.n_seq_max
        config.n_gpu_layers = m_cfg.n_gpu_layers

        # handle chat template strings
        if m_cfg.chat_template_path:
            config.chat_template_path = m_cfg.chat_template_path

        if m_cfg.chat_template_content:
            config.chat_template_content = m_cfg.chat_template_content

        # Create handle : returns py::capsule with automatic cleanup
        # Convert enum to string for C++ binding
        plugin_id_str = plugin_id.value if isinstance(plugin_id, PluginID) else plugin_id
        handle = vlm_bind.create_vlm(
            model_path=local_path,
            mmproj_path=mmproj_path,
            model_name=model_name,
            model_config=config,
            plugin_id=plugin_id_str,
            device_id=device_id
        )
        return cls(handle, m_cfg)

    def eject(self):
        """Release the model from memory."""
        # py::capsule handles cleanup automatically
        del self._handle
        self._handle = None

    def reset(self):
        """
        Reset the VLM model context and KV cache. If not reset, the model will skip the number of evaluated tokens and treat tokens after those as the new incremental tokens.
        If your past chat history changed, or you are starting a new chat, you should always reset the model before running generate.
        """
        vlm_bind.ml_vlm_reset(self._handle)

    def apply_chat_template(
        self,
        messages: List[MultiModalMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        enable_thinking: bool = True
    ) -> str:
        """Apply the chat template to multimodal messages."""
        payload = []
        for msg in messages:
            role   = msg["role"]
            blocks = []

            for c in msg["content"]:
                t = c["type"]
                if t == "text":
                    blocks.append({"type": "text", "text": c.get("text","") or ""})
                else:
                    # Pass through the original structure for image, audio, and any other types
                    # Let vlm-bind.cpp handle field extraction (text/url/path)
                    blocks.append(c)

            payload.append({"role": role, "content": blocks})

        result = vlm_bind.ml_vlm_apply_chat_template(self._handle, payload, tools, enable_thinking)
        return result

    def generate_stream(self, prompt: str, g_cfg: GenerationConfig = GenerationConfig()) -> Generator[str, None, None]:
        """Generate text with streaming."""
        token_queue = queue.Queue()
        exception_container = [None]
        self.reset_cancel()  # Reset cancel flag before generation

        def on_token(token: str, user_data) -> bool:
            if self._cancel_event.is_set():
                token_queue.put(('end', None))
                return False  # Stop generation
            try:
                token_queue.put(('token', token))
                return True  # Continue generation
            except Exception as e:
                exception_container[0] = e
                return False  # Stop generation

        config = self._convert_generation_config(g_cfg)

        # Run generation in thread
        def generate():
            try:
                result = vlm_bind.ml_vlm_generate(
                    handle=self._handle,
                    prompt=prompt,
                    config=config,
                    on_token=on_token,
                    user_data=None
                )
                
                # Check for errors in result
                error_code = result.get("error_code", ML_SUCCESS)
                if error_code != ML_SUCCESS:
                    error_message = result.get("error_message", "Unknown error")
                    if error_code == ML_ERROR_LLM_TOKENIZATION_CONTEXT_LENGTH:
                        exception_container[0] = ContextLengthExceededError(error_message, error_code)
                    else:
                        exception_container[0] = GenerationError(error_message, error_code)
                    token_queue.put(('end', None))
                    return
                
                self._profiling_data = ProfilingData.from_dict(result.get("profile_data", {}))
            except Exception as e:
                exception_container[0] = e
            finally:
                token_queue.put(('end', None))

        thread = threading.Thread(target=generate)
        thread.start()

        # Yield tokens as they come
        try:
            while True:
                msg_type, token = token_queue.get()
                if msg_type == 'token':
                    yield token
                elif msg_type in ('error', 'end'):
                    break
        finally:
            thread.join()

        if exception_container[0]:
            raise exception_container[0]

    def generate(self, prompt: str, g_cfg: GenerationConfig = GenerationConfig()) -> str:
        """
        Generate text without streaming.

        Args:
            prompt (str): The prompt to generate text from. For chat models, this is the chat messages after chat template is applied.
            g_cfg (GenerationConfig): Generation configuration.

        Returns:
            str: The generated text.
        """
        config = self._convert_generation_config(g_cfg)
        result = vlm_bind.ml_vlm_generate(
            handle=self._handle,
            prompt=prompt,
            config=config,
            on_token=None,  # No callback for non-streaming
            user_data=None
        )

        # Check for errors in result
        error_code = result.get("error_code", ML_SUCCESS)
        if error_code != ML_SUCCESS:
            error_message = result.get("error_message", "Unknown error")
            if error_code == ML_ERROR_LLM_TOKENIZATION_CONTEXT_LENGTH:
                raise ContextLengthExceededError(error_message, error_code)
            else:
                raise GenerationError(error_message, error_code)

        self._profiling_data = ProfilingData.from_dict(result.get("profile_data", {}))
        return result.get("text", "")

    def get_profiling_data(self) -> Optional[ProfilingData]:
        """Get profiling data."""
        return self._profiling_data

    def _convert_generation_config(self, g_cfg: GenerationConfig):
        """Convert GenerationConfig to binding format."""
        config = common_bind.GenerationConfig()

        # Set basic generation parameters
        config.max_tokens = g_cfg.max_tokens

        if g_cfg.stop_words:
            config.stop = g_cfg.stop_words

        if g_cfg.image_paths:
            config.image_paths = g_cfg.image_paths

        if g_cfg.audio_paths:
            config.audio_paths = g_cfg.audio_paths

        if g_cfg.sampler_config:
            sampler = common_bind.SamplerConfig()
            sampler.temperature = g_cfg.sampler_config.temperature
            sampler.top_p = g_cfg.sampler_config.top_p
            sampler.top_k = g_cfg.sampler_config.top_k
            sampler.repetition_penalty = g_cfg.sampler_config.repetition_penalty
            sampler.presence_penalty = g_cfg.sampler_config.presence_penalty
            sampler.frequency_penalty = g_cfg.sampler_config.frequency_penalty
            sampler.seed = g_cfg.sampler_config.seed

            if g_cfg.sampler_config.grammar_path:
                sampler.grammar_path = g_cfg.sampler_config.grammar_path

            if g_cfg.sampler_config.grammar_string:
                sampler.grammar_string = g_cfg.sampler_config.grammar_string

            config.sampler_config = sampler

        return config
