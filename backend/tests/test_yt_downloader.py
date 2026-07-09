import unittest
from pathlib import Path
from unittest.mock import patch

from utils.yt_downloader import download_audio


class FakeYoutubeDL:
    calls = 0

    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def download(self, urls):
        FakeYoutubeDL.calls += 1
        if FakeYoutubeDL.calls == 1:
            raise RuntimeError("first attempt failed")

        output_path = Path(self.opts["outtmpl"].replace("%(ext)s", "m4a"))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"audio")


class DownloadAudioTests(unittest.TestCase):
    def setUp(self):
        FakeYoutubeDL.calls = 0

    def test_download_audio_retries_with_fallback_format(self):
        with patch("utils.yt_downloader.YoutubeDL", FakeYoutubeDL):
            output_path = download_audio("https://example.com/video")

        self.assertTrue(Path(output_path).exists())
        self.assertTrue(output_path.endswith("temp_audio.m4a"))
        self.assertEqual(FakeYoutubeDL.calls, 2)


if __name__ == "__main__":
    unittest.main()
