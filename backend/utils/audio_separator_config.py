from dataclasses import dataclass, field
from typing import List


@dataclass
class SeparatorModelConfig:
    name: str
    enabled: bool = True
    priority: int = 0
    kwargs: dict = field(default_factory=dict)


@dataclass
class AudioSeparatorConfig:
    default_model: str = "MelBand-RoFormer"
    fallback_models: List[SeparatorModelConfig] = field(
        default_factory=lambda: [
            SeparatorModelConfig(name="Demucs", enabled=True, priority=10, kwargs={"model_name": "htdemucs_ft"}),
        ]
    )
    output_format: str = "wav"
    sample_rate: int = 16000
    cleanup_temp_files: bool = True
