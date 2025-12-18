import numpy as np
from dtw import dtw 

def calculate_score(user_pitch: np.ndarray, original_pitch: np.ndarray) -> float:
    """
    Calcula a similaridade entre os pitchs (0-100) usando:
    - Alinhamento temporal com DTW
    - Comparação de notas com tolerância a semitons
    """
    # Pré-processamento: remove silêncios (valores 0)
    user_pitch = user_pitch[user_pitch != 0]
    original_pitch = original_pitch[original_pitch != 0]
    
    # 1. Alinhamento temporal com DTW
    alignment = dtw(user_pitch, original_pitch, keep_internals=True)
    
    # 2. Calcula acertos dentro de ±1 semitom
    user_aligned = user_pitch[alignment.index1]
    original_aligned = original_pitch[alignment.index2]
    
    # Conversão para semitons (evita divisão por zero)
    user_semitones = 12 * np.log2(user_aligned / 440 + 1e-6)
    original_semitones = 12 * np.log2(original_aligned / 440 + 1e-6)
    
    # 3. Porcentagem de notas corretas (com tolerância)
    correct_notes = np.abs(user_semitones - original_semitones) < 1.0
    accuracy = np.mean(correct_notes) * 100
    
    # 4. Ajuste final (suaviza a pontuação)
    return min(100, accuracy * 1.2)  # Bônus de 20% para ser mais generoso