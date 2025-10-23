from typing import List, Optional, Sequence, Tuple, Union
from abc import abstractmethod
from dataclasses import dataclass

from nexaai.base import BaseModel
from nexaai.common import PluginID, ModelConfig


@dataclass
class ASRConfig:
    """Configuration for ASR."""
    timestamps: str = "none"  # "none" | "segment" | "word"
    beam_size: int = 5
    stream: bool = False


@dataclass
class ASRResult:
    """Result from ASR processing."""
    transcript: str
    confidence_scores: Sequence[float]
    timestamps: Sequence[Tuple[float, float]]


class ASR(BaseModel):
    """Abstract base class for Automatic Speech Recognition models."""

    def __init__(self, m_cfg: ModelConfig = ModelConfig()):
        """Initialize base ASR class."""
        self._m_cfg = m_cfg

    @classmethod
    def _load_from(cls,
                   model_path: str,
                   model_name: Optional[str] = None,
                   tokenizer_path: Optional[str] = None,
                   language: Optional[str] = None,
                   m_cfg: ModelConfig = ModelConfig(),
                   plugin_id: Union[PluginID, str] = PluginID.LLAMA_CPP,
                   device_id: Optional[str] = None,
                   **kwargs
        ) -> 'ASR':
        """Load ASR model from local path, routing to appropriate implementation."""
        # Check plugin_id value for routing - handle both enum and string
        plugin_value = plugin_id.value if isinstance(plugin_id, PluginID) else plugin_id
        
        if plugin_value == "mlx":
            from nexaai.asr_impl.mlx_asr_impl import MLXASRImpl
            return MLXASRImpl._load_from(model_path, model_name, tokenizer_path, language, m_cfg, plugin_id, device_id)
        else:
            from nexaai.asr_impl.pybind_asr_impl import PyBindASRImpl
            return PyBindASRImpl._load_from(model_path, model_name, tokenizer_path, language, m_cfg, plugin_id, device_id)


    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
        config: Optional[ASRConfig] = None,
    ) -> ASRResult:
        """Transcribe audio file to text."""
        pass

    @abstractmethod
    def list_supported_languages(self) -> List[str]:
        """List supported languages."""
        pass
