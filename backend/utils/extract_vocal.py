from pathlib import Path

from utils.audio_separator_service import AudioSeparatorService


def extract_vocals(input_path: str) -> str:
    """
    Recebe um arquivo de áudio baixado e retorna o caminho para um WAV mono 16 kHz
    contendo apenas os vocais, utilizando a camada de separação configurável.
    """
    input_file = Path(input_path)
    service = AudioSeparatorService()
    output_dir = input_file.parent / "separator_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    return service.separate_vocals(str(input_file), str(output_dir))