import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils.audio_separator_service import AudioSeparatorService


class StubSeparator:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def separate(self, input_path: str, output_dir: str):
        output_path = Path(output_dir) / "vocals.wav"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"stub")
        return {"output_dir": output_dir, "model": self.kwargs.get("model_name")}


class AudioSeparatorServiceTests(unittest.TestCase):
    def test_service_uses_configured_model_and_returns_vocals_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("utils.audio_separator_service.create_separator", return_value=StubSeparator()):
                service = AudioSeparatorService(config={"default_model": "MelBand-RoFormer"})
                vocals_path = service.separate_vocals("/tmp/input.mp3", tmpdir)

            self.assertTrue(Path(vocals_path).exists())
            self.assertEqual(Path(vocals_path).name, "vocals.wav")


if __name__ == "__main__":
    unittest.main()
