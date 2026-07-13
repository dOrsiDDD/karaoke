import logging
import tempfile
import time
from pathlib import Path
from typing import Optional

from utils.audio_separator_config import AudioSeparatorConfig
from utils.audio_utils import convert_to_wav

logger = logging.getLogger(__name__)

try:
    from audio_separator.separator import Separator
except Exception as e:
    logger.exception("Failed to import audio_separator")
    raise


def create_separator(**kwargs):
    if Separator is None:
        raise RuntimeError("audio-separator is not installed")
    return Separator(**kwargs)


class AudioSeparatorService:
    def __init__(self, config: Optional[dict] = None):
        self.config = AudioSeparatorConfig(**(config or {}))

    def separate_vocals(self, input_path: str, output_dir: Optional[str] = None) -> str:
        temp_dir = Path(output_dir or tempfile.mkdtemp(prefix="separator_", dir="."))
        temp_dir.mkdir(parents=True, exist_ok=True)

        models_to_try = [self.config.default_model]
        models_to_try.extend(
            sorted(
                (m for m in self.config.fallback_models if m.enabled),
                key=lambda m: m.priority,
            )
        )

        for model in models_to_try:
            try:
                logger.info("Starting audio separation with model %s", model.name)

                start_time = time.perf_counter()

                separator = create_separator(
                    model_file_dir="/models",
                    output_dir=str(temp_dir),
                    output_format=self.config.output_format.upper())

                separator.load_model(model.filename)

                wav_path = convert_to_wav(input_path, channels=2, sr=44100)

                separator.separate(wav_path)
                duration = time.perf_counter() - start_time
                logger.info("Separation completed for %s in %.2fs", model.name, duration)

                vocals_path = self._find_vocals_file(temp_dir)
                if not vocals_path:
                    raise FileNotFoundError("audio-separator did not produce a vocals stem")

                final_path = convert_to_wav(str(vocals_path), channels=1, sr=self.config.sample_rate)
                return final_path
            except Exception as exc:  # pragma: no cover - exercised via fallback logic
                last_error = exc
                logger.exception("Separation failed for model %s", model.name)

        raise RuntimeError(f"All separator models failed. Last error: {last_error}")

    def cleanup_temp_files(self, path: str):
        if not self.config.cleanup_temp_files:
            return
        if path and Path(path).exists():
            Path(path).unlink(missing_ok=True)

    def _find_vocals_file(self, output_dir: Path) -> Optional[Path]:
        candidates = [
            output_dir / "vocals.wav",
            output_dir / "vocals" / "vocals.wav",
            output_dir / "vocals_16k.wav",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        for path in output_dir.rglob("*.wav"):
            if "vocals" in path.name.lower():
                return path
        return None
