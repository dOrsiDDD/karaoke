import librosa
import pyworld
import numpy as np

def remove_silence(y, threshold=0.01):
    energy = np.abs(y)
    mask = energy > threshold
    return y[mask]

def extract_pitch(audio_path: str, sr=16000):
    y, sr = librosa.load(audio_path, sr=sr, mono=True)
    y = remove_silence(y)
    print(f"[DEBUG] Áudio carregado do WAV: min={y.min()}, max={y.max()}, tamanho={y.size}")

    if y.size == 0:
     raise ValueError("Áudio vazio ou inválido")
    
    f0, voiced_flag, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz("C2"),
        fmax=librosa.note_to_hz("C6"),
        sr=sr
    )

    # Remove NaNs
    f0 = np.nan_to_num(f0)

    return f0