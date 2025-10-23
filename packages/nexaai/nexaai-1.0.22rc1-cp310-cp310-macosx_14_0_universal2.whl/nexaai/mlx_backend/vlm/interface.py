from __future__ import annotations

import json
import os
import time
from typing import Any, List, Optional, Sequence, Tuple, Union
import mlx.core as mx
import codecs
from dataclasses import dataclass

# Import configs and callback types from ml.py for API alignment
from ml import (
    VLM as BaseVLM,
    SamplerConfig,
    GenerationConfig,
    ChatMessage,
    EmbeddingConfig,
    TokenCallback,
    Path,
    Tool,  # Add Path alias for type hints
)

# Import profiling module
from profiling import ProfilingMixin, ProfilingData, StopReason

# Import from the actual mlx_vlm structure
from .generate import generate, stream_generate, load
from .generate_qwen3_vl import apply_chat_template_qwen3_vl, stream_generate_qwen3_vl, load_qwen3_vl, ContextLengthExceededError

from .generate_qwen3_vl_moe import apply_chat_template_qwen3_vl as apply_chat_template_qwen3_vl_moe
from .generate_qwen3_vl_moe import stream_generate_qwen3_vl as stream_generate_qwen3_vl_moe
from .generate_qwen3_vl_moe import load_qwen3_vl as load_qwen3_vl_moe

from .modeling.prompt_utils import apply_chat_template

# --------------------------------------------------------------------------------------
# Updated GenerationResult to match the new structure
# --------------------------------------------------------------------------------------

@dataclass
class GenerationResult:
    text: str = ""
    token: Optional[int] = None
    logprobs: Optional[List[float]] = None
    prompt_tokens: int = 0
    generation_tokens: int = 0
    total_tokens: int = 0
    prompt_tps: float = 0.0
    generation_tps: float = 0.0
    peak_memory: float = 0.0
# --------------------------------------------------------------------------------------
# VLM (Vision-Language Model)
# --------------------------------------------------------------------------------------

class VLM(ProfilingMixin):
    """
    Vision-Language Models for mlx-vlm
    API aligned with ml.py VLM abstract base class.
    """

    def __init__(
        self,
        model_name: Optional[str],
        model_path: Path,
        mmproj_path: Path,
        context_length: int,
        device: Optional[str] = None,
    ) -> None:
        # Initialize profiling mixin
        ProfilingMixin.__init__(self)

        # Check if model_path is a file, if so use its parent directory
        if os.path.isfile(model_path):
            model_path = os.path.dirname(model_path)

        self.model_path = model_path
        self.model_name = model_name
        self.mmproj_path = mmproj_path
        self.context_length = context_length
        self.device = device

        if model_name == "qwen3vl-moe":
            load_impl = load_qwen3_vl_moe
        elif model_name in ["qwen3vl", "qwen3vl-4b", "qwen3vl-4b-thinking", "qwen3vl-8b", "qwen3vl-8b-thinking"]:
            load_impl = load_qwen3_vl
        else:
            load_impl = load

        # Pass model_name to the loader for proper configuration
        self.model, self.processor = load_impl(str(model_path), model_name=model_name)

        # Init deafutl sampler config with defualt.
        self.sampler_config = SamplerConfig()
        
        # Track global character position for incremental processing
        self.global_n_past_chars = 0

        # Add conversation state tracking to VLM class
        if model_name in ["qwen3vl", "qwen3vl-4b", "qwen3vl-4b-thinking", "qwen3vl-8b", "qwen3vl-8b-thinking"]:
            # Import here to avoid circular imports
            from .modeling.models.qwen3_vl.llm_common.cache import make_prompt_cache
            import mlx.core as mx
            
            # Initialize conversation state
            self.rope_deltas_total = mx.zeros((1, 1), dtype=mx.int32)
            self.prompt_cache = make_prompt_cache(self.model.llm_model, max_kv_size=4096)
        else:
            self.rope_deltas_total = None
            self.prompt_cache = None

    def destroy(self) -> None:
        """Destroy the model and free resources."""
        self.model = None
        self.processor = None

    def reset(self) -> None:
        """Reset the model state."""
        self._reset_cache()
        self.global_n_past_chars = 0
        
        # Reset conversation state for qwen3vl models
        if self.model_name in ["qwen3vl", "qwen3vl-4b", "qwen3vl-4b-thinking", "qwen3vl-8b", "qwen3vl-8b-thinking"]:
            import mlx.core as mx
            from .modeling.models.qwen3_vl.llm_common.cache import make_prompt_cache
            
            self.rope_deltas_total = mx.zeros((1, 1), dtype=mx.int32)
            self.prompt_cache = make_prompt_cache(self.model.llm_model, max_kv_size=4096)

    def _reset_cache(self) -> None:
        """Reset the KV cache."""
        # If the model has a cache, reset it
        if hasattr(self.model, "cache"):
            self.model.cache = None

    # Tokenization
    def encode(self, text: str) -> List[int]:
        """Encode text to token IDs."""
        return self.processor.encode(text)

    def decode(self, token_ids: Sequence[int]) -> str:
        """Decode token IDs to text."""
        return self.processor.decode(token_ids)

    # Sampler
    def set_sampler(self, config: SamplerConfig) -> None:
        """Set sampler configuration."""
        self.sampler_config = config

    def reset_sampler(self) -> None:
        """Reset sampler to default configuration."""
        self.sampler_config = None

    # Generation
    def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResult:
        """Generate text from prompt.""" 
        # Start profiling
        self._start_profiling()

        gen_kwargs = {}
        if config is not None:
            gen_kwargs = config.__dict__.copy()
            # Remove image_paths and audio_paths from config as they'll be handled separately
            gen_kwargs.pop('image_paths', None)
            gen_kwargs.pop('audio_paths', None)
        if self.sampler_config is not None:
            gen_kwargs.update(self.sampler_config.__dict__)

        # Get image and audio paths from config
        image_paths = config.image_paths if config else None
        audio_paths = config.audio_paths if config else None

        # Convert paths to strings for generate function
        image_list = [str(path) for path in image_paths] if image_paths else None
        audio_list = [str(path) for path in audio_paths] if audio_paths else None

        # Extract incremental portion of the prompt (similar to llama.cpp VLM)
        full_prompt_len = len(prompt)
        incremental_prompt = prompt
          
        # Apply incremental processing only for non-qwen3vl models
        # qwen3vl requires complete JSON conversation structure
        if self.model_name != "qwen3vl":
            if self.global_n_past_chars < full_prompt_len:
                incremental_prompt = prompt[self.global_n_past_chars:]
            else:
                # No new text to process
                incremental_prompt = ""

        # End prompt processing, start decode
        self._prompt_end()
        self._decode_start()

        try:
            # Start timing for generation
            generation_start_time = time.perf_counter()

            text, stats = generate(
                self.model,
                self.processor,
                incremental_prompt,  # Use incremental prompt instead of full prompt
                image=image_list,
                audio=audio_list,
                **gen_kwargs,
            )

            # End timing for generation
            generation_end_time = time.perf_counter()

            # Calculate average time per token and estimate TTFT
            generated_tokens = stats.get("output_tokens", 0)
            if generated_tokens > 0:
                total_generation_time = generation_end_time - generation_start_time
                avg_time_per_token = total_generation_time / generated_tokens
                # TTFT = prompt processing time + first token generation time
                # This provides a more accurate estimate than the previous approximation
                estimated_ttft = (self._profiling_context.prompt_end_time - self._profiling_context.prompt_start_time) + avg_time_per_token
                # Update the profiling context with estimated TTFT
                self._profiling_context.first_token_time = self._profiling_context.prompt_start_time + estimated_ttft
                self._profiling_context.ttft_recorded = True
            else:
                # If no tokens generated, use total generation time as TTFT
                self._record_ttft()

            # Update profiling data
            prompt_tokens = stats.get("input_tokens", 0)
            self._update_prompt_tokens(prompt_tokens)
            self._update_generated_tokens(generated_tokens)
            self._set_stop_reason(StopReason.ML_STOP_REASON_COMPLETED)
            
            # Update global character position (not needed for qwen3vl JSON processing)
            if self.model_name != "qwen3vl":
                old_pos = self.global_n_past_chars
                self.global_n_past_chars = full_prompt_len + len(text)
            
            self._decode_end()
            self._end_profiling()

            result = GenerationResult(
                text=text,
                prompt_tokens=prompt_tokens,
                generation_tokens=generated_tokens,
                total_tokens=stats.get("total_tokens", 0),
                prompt_tps=stats.get("prompt_tps", 0.0),
                generation_tps=stats.get("generation_tps", 0.0),
                peak_memory=stats.get("peak_memory", 0.0),
            )
            
            return result
            
        except ContextLengthExceededError as e:
            self._set_stop_reason(StopReason.ML_STOP_REASON_UNKNOWN)
            self._decode_end()
            self._end_profiling()
            # Re-raise the original exception without wrapping it
            raise e
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._set_stop_reason(StopReason.ML_STOP_REASON_UNKNOWN)
            self._decode_end()
            self._end_profiling()
            raise RuntimeError(f"Generation error: {str(e)}")

    def generate_stream(
        self,
        prompt: str,
        config: Optional[GenerationConfig],
        on_token: Optional[TokenCallback],
    ) -> GenerationResult:
        """Generate text with streaming callback. Unified method for both text and multimodal generation."""
        
        # Start profiling
        self._start_profiling()

        gen_kwargs = {}
        if config is not None:
            gen_kwargs = config.__dict__.copy()
            # Remove image_paths and audio_paths from config as they'll be handled separately
            gen_kwargs.pop('image_paths', None)
            gen_kwargs.pop('audio_paths', None)
        if self.sampler_config is not None:
            gen_kwargs.update(self.sampler_config.__dict__)


        # Get image and audio paths from config
        image_paths = config.image_paths if config else None
        audio_paths = config.audio_paths if config else None

        # Convert paths to strings for stream_generate function
        image_list = [str(path) for path in image_paths] if image_paths else None
        audio_list = [str(path) for path in audio_paths] if audio_paths else None


        # Extract incremental portion of the prompt (similar to llama.cpp VLM)
        full_prompt_len = len(prompt)
        incremental_prompt = prompt
        
        
        # Apply incremental processing only for non-qwen3vl models
        # qwen3vl requires complete JSON conversation structure
        if self.model_name not in ["qwen3vl", "qwen3vl-4b", "qwen3vl-4b-thinking", "qwen3vl-8b", "qwen3vl-8b-thinking", "qwen3vl-moe"]:
            if self.global_n_past_chars < full_prompt_len:
                incremental_prompt = prompt[self.global_n_past_chars:]
            else:
                # No new text to process
                incremental_prompt = ""

        # End prompt processing, start decode
        self._prompt_end()
        self._decode_start()

        text = ""
        last_result = None
        first_token = True

        if self.model_name == "qwen3vl-moe":
            stream_generate_impl = stream_generate_qwen3_vl_moe
        elif self.model_name in ["qwen3vl", "qwen3vl-4b", "qwen3vl-4b-thinking", "qwen3vl-8b", "qwen3vl-8b-thinking"]:
            stream_generate_impl = stream_generate_qwen3_vl
        else:
            stream_generate_impl = stream_generate

        try:
            token_count = 0
            
            # Pass conversation state for qwen3vl models
            if self.model_name in ["qwen3vl", "qwen3vl-4b", "qwen3vl-4b-thinking", "qwen3vl-8b", "qwen3vl-8b-thinking"]:
                for result in stream_generate_impl(
                    self.model,
                    self.processor,
                    incremental_prompt,
                    image=image_list,
                    audio=audio_list,
                    rope_deltas_total=self.rope_deltas_total,  # Pass conversation state
                    prompt_cache=self.prompt_cache,  # Pass KV cache
                    **gen_kwargs,
                ):
                    token_count += 1
                    
                    # Record TTFT on first token
                    if first_token:
                        self._record_ttft()
                        first_token = False

                    # Call the token callback if provided
                    if on_token is not None:
                        if not on_token(result.text):
                            self._set_stop_reason(StopReason.ML_STOP_REASON_USER)
                            break
                    text += result.text
                    last_result = result

                    # Update conversation state after each token
                    # Note: rope_deltas_total is updated inside stream_generate_qwen3_vl

            else:
                for result in stream_generate_impl(
                    self.model,
                    self.processor,
                    incremental_prompt,
                    image=image_list,
                    audio=audio_list,
                    **gen_kwargs,
                ):
                    token_count += 1
                    
                    # Record TTFT on first token
                    if first_token:
                        self._record_ttft()
                        first_token = False

                    # Call the token callback if provided
                    if on_token is not None:
                        if not on_token(result.text):
                            self._set_stop_reason(StopReason.ML_STOP_REASON_USER)
                            break
                    text += result.text
                    last_result = result


            # Set stop reason if not user stop
            if self._profiling_context.stop_reason != StopReason.ML_STOP_REASON_USER:
                self._set_stop_reason(StopReason.ML_STOP_REASON_EOS)

            # Update profiling data
            if last_result:
                self._update_prompt_tokens(last_result.prompt_tokens)
                self._update_generated_tokens(last_result.generation_tokens)

            # Update global character position (not needed for qwen3vl JSON processing)
            if self.model_name not in ["qwen3vl", "qwen3vl-4b", "qwen3vl-4b-thinking", "qwen3vl-8b", "qwen3vl-8b-thinking", "qwen3vl-moe"]:
                old_pos = self.global_n_past_chars
                self.global_n_past_chars = full_prompt_len + len(text)

            self._decode_end()
            self._end_profiling()

            result = GenerationResult(
                text=text,
                token=last_result.token if last_result else None,
                logprobs=last_result.logprobs if last_result else None,
                prompt_tokens=last_result.prompt_tokens if last_result else 0,
                generation_tokens=last_result.generation_tokens if last_result else 0,
                total_tokens=(last_result.prompt_tokens + last_result.generation_tokens) if last_result else 0,
                prompt_tps=last_result.prompt_tps if last_result else 0.0,
                generation_tps=last_result.generation_tps if last_result else 0.0,
                peak_memory=last_result.peak_memory if last_result else 0.0,
            )
            
            return result
            
        except ContextLengthExceededError as e:
            self._set_stop_reason(StopReason.ML_STOP_REASON_UNKNOWN)
            self._decode_end()
            self._end_profiling()
            # Re-raise the original exception without wrapping it
            raise e
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._set_stop_reason(StopReason.ML_STOP_REASON_UNKNOWN)
            self._decode_end()
            self._end_profiling()
            raise RuntimeError(f"Streaming generation error: {str(e)}")

    # Legacy multimodal methods - kept for backward compatibility but delegate to unified method
    def generate_multimodal(
        self,
        prompt: str,
        image_paths: Optional[Sequence[Path]] = None,
        audio_paths: Optional[Sequence[Path]] = None,
        config: Optional[GenerationConfig] = None,
    ) -> str:
        """Generate text from prompt with multiple images and audio."""
        # Create config with media paths if not provided
        if config is None:
            config = GenerationConfig()

        # Update config with provided paths
        if image_paths is not None:
            config.image_paths = image_paths
        if audio_paths is not None:
            config.audio_paths = audio_paths

        # Delegate to unified generate method and extract text
        result = self.generate(prompt, config)
        return result.text

    def generate_stream_multimodal(
        self,
        prompt: str,
        image_paths: Optional[Sequence[Path]] = None,
        audio_paths: Optional[Sequence[Path]] = None,
        config: Optional[GenerationConfig] = None,
        on_token: Optional[TokenCallback] = None,
    ) -> str:
        """Generate text from prompt with multiple images and audio using streaming callback."""
        # Create config with media paths if not provided
        if config is None:
            config = GenerationConfig()

        # Update config with provided paths
        if image_paths is not None:
            config.image_paths = image_paths
        if audio_paths is not None:
            config.audio_paths = audio_paths

        # Delegate to unified generate_stream method and extract text
        result = self.generate_stream(prompt, config, on_token)
        return result.text

    def get_chat_template(self, template_name: str) -> str:
        """Get chat template by name."""
        # This is a stub; actual implementation depends on processor internals
        if hasattr(self.processor, "get_chat_template"):
            return self.processor.get_chat_template(template_name)
        return ""

    def apply_chat_template(self, messages: Sequence[ChatMessage], tools: Optional[str] = None, enable_thinking: bool = True) -> str:
        """Apply chat template to messages with optional tools support."""
        if self.model_name in ["qwen3vl", "qwen3vl-4b", "qwen3vl-4b-thinking", "qwen3vl-8b", "qwen3vl-8b-thinking"]:
            return apply_chat_template_qwen3_vl(messages, num_images=0, num_audios=0, tools=tools, enable_thinking=enable_thinking)
        if self.model_name == "qwen3vl-moe":
            return apply_chat_template_qwen3_vl_moe(messages, num_images=0, num_audios=0, tools=tools, enable_thinking=enable_thinking)
        
        if hasattr(self.processor, "apply_chat_template"):
            messages_dict = [{"role": msg.role, "content": msg.content} for msg in messages]
            
            parsed_tools = None
            if tools is not None and tools.strip():
                parsed_tools = json.loads(tools)
            
            result = apply_chat_template(self.processor, self.model.config, messages_dict, add_generation_prompt=True, enable_thinking=enable_thinking, tools=parsed_tools)
            return result
        return "\n".join([f"{m.role}: {m.content}" for m in messages])

    def apply_chat_template_with_media(self, messages: Sequence[ChatMessage], num_images: int = 0, num_audios: int = 0, tools: Optional[str] = None, enable_thinking: bool = True) -> str:
        """Apply chat template to messages with proper image/audio token insertion and optional tools support."""
        if self.model_name in ["qwen3vl", "qwen3vl-4b", "qwen3vl-4b-thinking", "qwen3vl-8b", "qwen3vl-8b-thinking"]:
            return apply_chat_template_qwen3_vl(messages, num_images=num_images, num_audios=num_audios, tools=tools, enable_thinking=enable_thinking)
        if self.model_name == "qwen3vl-moe":
            return apply_chat_template_qwen3_vl_moe(messages, num_images=num_images, num_audios=num_audios, tools=tools, enable_thinking=enable_thinking)
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in messages]

        parsed_tools = None
        if tools is not None and tools.strip():
            parsed_tools = json.loads(tools)

        # Use the same logic as generate.py
        return apply_chat_template(
            self.processor,
            self.model.config,
            messages_dict,
            num_images=num_images,
            num_audios=num_audios,
            enable_thinking=enable_thinking,
            tools=parsed_tools
        )

    # Embeddings
    def embed(
        self,
        texts: Sequence[str],
        config: Optional[EmbeddingConfig] = None,
    ) -> List[List[float]]:
        """Generate embeddings for texts with profiling."""
        # Start profiling
        self._start_profiling()

        try:
            # If processor/model supports embeddings, use it; otherwise, stub
            if hasattr(self.model, "embed"):
                embed_kwargs = config.__dict__ if config else {}

                # End prompt processing, start decode
                self._prompt_end()
                self._decode_start()

                result = self.model.embed(texts, **embed_kwargs)

                # End timing and finalize profiling data
                self._update_generated_tokens(0)  # No generation in embedding
                self._set_stop_reason(StopReason.ML_STOP_REASON_COMPLETED)
                self._decode_end()
                self._end_profiling()

                return result
            else:
                raise NotImplementedError("Embedding not supported for this model.")

        except Exception as e:
            self._set_stop_reason(StopReason.ML_STOP_REASON_UNKNOWN)
            self._decode_end()
            self._end_profiling()
            raise RuntimeError(f"Error generating embeddings: {str(e)}")
