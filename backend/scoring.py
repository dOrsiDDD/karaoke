import numpy as np
from librosa.sequence import dtw as librosa_dtw


def _run_dtw(user_notes, original_notes):
    cost_matrix = np.where(user_notes[:, None] != original_notes[None, :], 1.0, 0.0)
    _, wp = librosa_dtw(C=cost_matrix, backtrack=True)

    if wp is None:
        return None

    path = np.asarray(wp)
    if path.ndim == 1:
        return np.array([[path[0]], [path[1]]], dtype=int)

    if path.shape[0] == 2:
        path = path.T

    return path[::-1]


def CalculateScore(userNotes, originalNotes, pitchWeight=0.7, rhythmWeight=0.3, rhythmToleranceFrames=20):
    """
    Calcula nota de 0-100 considerando:

    - Afinação baseada na nota musical (ignorando oitava)
    - Penalização por ritmo usando o alinhamento DTW

    Parâmetros
    ----------
    pitchWeight : peso da afinação
    rhythmWeight : peso do ritmo
    rhythmToleranceFrames : Quantos frames de diferença são tolerados antes de receber nota 0 em ritmo.
    """

    userNotes = np.asarray(userNotes, dtype=int).reshape(-1)
    originalNotes = np.asarray(originalNotes, dtype=int).reshape(-1)

    if userNotes.size == 0 or originalNotes.size == 0:
        return 0.0

    alignment = _run_dtw(userNotes, originalNotes)

    if alignment is None or len(alignment) == 0:
        return 0.0

    user_idx = alignment[:, 0]
    original_idx = alignment[:, 1]

    u = userNotes[user_idx]
    o = originalNotes[original_idx]

    mask = (u >= 0) & (o >= 0)

    if np.sum(mask) < 10:
        return 0.0

    u = u[mask]
    o = o[mask]

    alignedUserIdx = user_idx[mask]
    alignedOriginalIdx = original_idx[mask]

    # Afinação
    pitchHits = (u == o)
    pitchScore = np.mean(pitchHits) * 100 if pitchHits.size else 0.0

    # Ritmo
    rhythmError = np.abs(alignedUserIdx - alignedOriginalIdx)
    rhythmFrameScores = np.clip(1 - rhythmError / rhythmToleranceFrames, 0, 1)
    rhythmScore = np.mean(rhythmFrameScores) * 100 if rhythmFrameScores.size else 0.0

    finalScore = pitchWeight * pitchScore + rhythmWeight * rhythmScore
    return float(np.clip(finalScore, 0, 100))