import numpy as np
from dtw import dtw 

def calculate_score(user_pitch, original_pitch, tolerance=1.0):
    """
    Calcula a similaridade entre os pitchs (0-100) usando:
    - Alinhamento temporal com DTW
    - Comparação de notas com tolerância a semitons
    """

    alignment = dtw(user_pitch, original_pitch, keep_internals=True)
    # Pré-processamento: remove silêncios (valores 0)
    u = user_pitch[alignment.index1]
    o = original_pitch[alignment.index2]
    
    mask = (u > 0) & (o > 0)
    if np.sum(mask) < 10:
        return 0.0  # Poucos dados válidos para comparar
     
    u = u[mask]
    o = o[mask]
    
    # Conversão para semitons
    delta_semitones = 12 * np.log2(user_aligned / original_aligned)
    error = np.abs(delta_semitones)

    
    frame_scores = np.clip(1 - error / tolerance, 0, 1)
    score = np.mean(frame_scores) * 100

    return min(100, score)