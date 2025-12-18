import os
import tempfile
from pydub import AudioSegment

def save_upload_to_temp(upload_file) -> str:
    """
    Salva o arquivo enviado em disco temporário e retorna o caminho.
    """
    suffix = os.path.splitext(upload_file.filename or "")[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(upload_file.file.read())
    tmp.close()
    return tmp.name

def convert_to_wav(input_path: str) -> str:
    """
    Converte qualquer formato suportado (webm, ogg, wav) para wav normalizado.
    """
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)  # normalização
    wav_path = input_path + ".wav"
    audio.export(wav_path, format="wav")
    return wav_path

def cleanup_files(*paths):
    """
    Remove arquivos temporários.
    """
    for p in paths:
        if p and os.path.exists(p):
            os.remove(p)
