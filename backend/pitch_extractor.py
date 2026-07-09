import librosa
import numpy as np
import soundfile as sf
import pyworld as pw
from scipy.signal import medfilt


def _remove_short_runs(mask: np.ndarray, min_frames: int) -> np.ndarray:
    if min_frames <= 1 or mask.size == 0:
        return mask

    cleaned = mask.copy()
    current_start = None
    for i, value in enumerate(mask):
        if value and current_start is None:
            current_start = i
        elif not value and current_start is not None:
            run_length = i - current_start
            if run_length < min_frames:
                cleaned[current_start:i] = False
            current_start = None
    if current_start is not None:
        run_length = mask.size - current_start
        if run_length < min_frames:
            cleaned[current_start:] = False
    return cleaned


def extract_pitch(
    audioPath: str,
    sr=16000,
    frame_length=2048,
    hop_length=512,
    fmin_note="C2",
    fmax_note="C6",
    rms_percentile=5,
    median_filter_ms=75,
    split_top_db=30,
    min_voiced_run_frames=3,
):
    """
    Extrai F0 usando pyworld.harvest + stonemask (mais robusto para voz cantada),
    aplica máscara por RMS, segmentação de silêncio e run-length filtering.

    Retorna:
        pitch: np.ndarray (Hz) com 0.0 em frames sem f0 confiavel
        timestamps: np.ndarray (s) correspondendo a cada frame
    """

    y, file_sr = sf.read(audioPath, dtype="float32")
    if y.ndim > 1:
        y = np.mean(y, axis=1)
    if file_sr != sr:
        y = librosa.resample(y, orig_sr=file_sr, target_sr=sr)
    print(f"[DEBUG] Audio carregado do WAV: min={y.min()}, max={y.max()}, tamanho={y.size}, sr={sr}")

    if y.size == 0:
        raise ValueError("Audio vazio ou invalido")

    fmin_hz = librosa.note_to_hz(fmin_note)
    fmax_hz = librosa.note_to_hz(fmax_note)

    frame_period_ms = hop_length / float(sr) * 1000.0
    x = y.astype(np.float64)
    f0, times = pw.harvest(
        x,
        sr,
        frame_period=frame_period_ms,
        f0_floor=fmin_hz,
        f0_ceil=fmax_hz,
    )
    f0 = pw.stonemask(x, f0, times, sr)

    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length, center=True)[0]
    non_silent_intervals = librosa.effects.split(
        y,
        top_db=split_top_db,
        frame_length=frame_length,
        hop_length=hop_length,
    )

    frame_count = min(len(f0), len(rms), len(times))
    f0 = f0[:frame_count]
    times = times[:frame_count]
    rms = rms[:frame_count]

    frame_samples = np.round(times * sr).astype(int)
    non_silent_mask = np.zeros(frame_count, dtype=bool)
    for start_sample, end_sample in non_silent_intervals:
        non_silent_mask |= (frame_samples >= start_sample) & (frame_samples < end_sample)

    active_rms = rms[rms > 0]
    rms_threshold = np.percentile(active_rms, rms_percentile) if active_rms.size else 0.0

    voiced_mask = (f0 > 0) & (rms >= rms_threshold) & non_silent_mask

    hop_ms = hop_length / float(sr) * 1000.0
    kernel_frames = max(3, int(round(median_filter_ms / hop_ms)))
    if kernel_frames % 2 == 0:
        kernel_frames += 1
    try:
        f0_filtered = medfilt(f0, kernel_size=kernel_frames)
    except Exception:
        f0_filtered = f0.copy()

    voiced_mask = _remove_short_runs(voiced_mask, min_voiced_run_frames)

    pitch = np.where(voiced_mask, f0_filtered, 0.0)
    timestamps = times

    print(
        "[DEBUG] Pitch frames:",
        f"total={len(pitch)}",
        f"voiced={int(np.count_nonzero(pitch > 0))}",
        f"rms_threshold={rms_threshold:.6f}",
        f"median_kernel={kernel_frames}frames",
        f"silence_segments={len(non_silent_intervals)}",
        f"min_run={min_voiced_run_frames}",
    )

    return pitch, timestamps
