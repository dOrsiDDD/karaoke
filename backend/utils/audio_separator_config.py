from dataclasses import dataclass, field
from typing import List

@dataclass
class SeparatorModelConfig:
    name: str
    filename: str
    enabled: bool = True
    priority: int = 0

@dataclass
class AudioSeparatorConfig:
    default_model: SeparatorModelConfig = field(
        default_factory=lambda: SeparatorModelConfig(
            name="MelBand-RoFormer",
            filename="model_mel_band_roformer_ep_3005_sdr_11.4360.ckpt",
        )
    )

    fallback_models: List[SeparatorModelConfig] = field(
        default_factory=lambda: [
            SeparatorModelConfig(
                name="BS-RoFormer",
                filename="model_bs_roformer_ep_317_sdr_12.9755.ckpt",
            ),
            SeparatorModelConfig(
                name="Demucs",
                filename="htdemucs_ft.yaml",
            ),
        ]
    )
    output_format: str = "wav"
    sample_rate: int = 16000
    cleanup_temp_files: bool = True
