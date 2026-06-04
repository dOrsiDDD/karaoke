from pathlib import Path
import subprocess
import shutil

from audio_utils import convert_to_wav


def extract_vocals(input_path: str) -> str:
    """
    Recebe um arquivo de áudio baixado do YouTube (webm/mp3/m4a/etc),
    executa separação vocal com Demucs e retorna o caminho para um
    WAV mono 16 kHz contendo apenas os vocais.

    Retorna:
        str: caminho do arquivo vocals_16k.wav
    """

    input_file = Path(input_path)

    # Pasta temporária onde o Demucs vai escrever os stems
    demucs_output_dir = input_file.parent / "demucs_output"

    # Limpa restos de execuções anteriores
    if demucs_output_dir.exists():
        shutil.rmtree(demucs_output_dir)

    # Executa Demucs
    subprocess.run(
        [
            "demucs",
            "--two-stems=vocals",
            "-o",
            str(demucs_output_dir),
            str(input_file),
        ],
        check=True,
    )

    # demucs_output/
    #   htdemucs/
    #       nome_do_arquivo/
    #           vocals.wav
    #           no_vocals.wav
    #

    model_dir = demucs_output_dir / "htdemucs"
    song_dir = model_dir / input_file.stem

    vocals_path = song_dir / "vocals.wav"

    if not vocals_path.exists():
        raise FileNotFoundError(
            f"Demucs não gerou o arquivo esperado: {vocals_path}"
        )
    
    # Converte para mono 16 kHz
    final_vocals_path = convert_to_wav(str(vocals_path), channels=1, sr=16000)

    return final_vocals_path