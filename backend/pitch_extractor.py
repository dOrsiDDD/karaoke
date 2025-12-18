import librosa
import pyworld
import numpy as np

def extract_pitch(audio_path: str, sr=16000):
    y, sr = librosa.load(audio_path, sr=sr, mono=True)
    print(f"[DEBUG] Áudio carregado do WAV: min={y.min()}, max={y.max()}, tamanho={y.size}")

    if y.size == 0:
     raise ValueError("Áudio vazio ou inválido")
    
    y = y.astype(np.float64)

    f0, t = pyworld.dio(y, sr)
    f0 = pyworld.stonemask(y, f0, t, sr)
    return f0  # Vetor de pitch em Hz