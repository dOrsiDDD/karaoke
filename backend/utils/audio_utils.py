import os
import tempfile
from pathlib import Path

import numpy as np
import librosa
import soundfile as sf


def ConverterFreqParaMidi(freq):
    """
    Converte Hz para número MIDI.
    Frequências <= 0 retornam NaN.
    """
    freq = np.asarray(freq, dtype=float)

    midi = np.full(freq.shape, np.nan)

    valid = freq > 0
    midi[valid] = 69 + 12 * np.log2(freq[valid] / 440.0)

    return midi

def clean_note_sequence(notes, min_run_frames=4, passes=2):
    """
    Remove saltos muito curtos do vetor de notas.

    - Notas negativas representam silencio/sem pitch confiavel.
    - Runs vocais curtos entre silencios viram silencio.
    - Runs curtos entre notas vocais sao absorvidos pelo vizinho mais plausivel.
    """
    cleaned = np.asarray(notes, dtype=int).copy()

    for _ in range(passes):
        runs = []
        start = 0

        for i in range(1, len(cleaned) + 1):
            if i == len(cleaned) or cleaned[i] != cleaned[start]:
                runs.append({
                    "start": start,
                    "end": i,
                    "note": int(cleaned[start]),
                    "length": i - start,
                })
                start = i

        updated = cleaned.copy()

        for idx, run in enumerate(runs):
            if run["length"] >= min_run_frames or run["note"] < 0:
                continue

            prev_run = runs[idx - 1] if idx > 0 else None
            next_run = runs[idx + 1] if idx + 1 < len(runs) else None
            prev_note = prev_run["note"] if prev_run else -1
            next_note = next_run["note"] if next_run else -1

            if run["note"] < 0:
                if prev_note == next_note and prev_note >= 0:
                    replacement = prev_note  # Fecha o buraco com a nota ao redor
                elif prev_note >= 0 and next_note >= 0:
                    replacement = (
                        prev_note
                        if prev_run["length"] >= next_run["length"]
                        else next_note
                    )
                else:
                    continue  # Silêncio na borda do áudio, deixa quieto
            else:
                # Comportamento original para notas curtas (ruídos)
                if prev_note == next_note:
                    replacement = prev_note
                elif prev_note >= 0 and next_note >= 0:
                    replacement = (
                        prev_note
                        if prev_run["length"] >= next_run["length"]
                        else next_note
                    )
                else:
                    replacement = -1

            updated[run["start"] : run["end"]] = replacement
        if np.array_equal(updated, cleaned):
            break

        cleaned = updated

    return cleaned

def build_segments(times, notes):
    # Proteções: garante que `times` e `notes` tenham comprimentos compatíveis
    if len(times) == 0 or len(notes) == 0:
        return []

    # Se `notes` for maior que `times`, corta; se for menor, pad com -1
    if len(notes) > len(times):
        notes = notes[: len(times)]
    elif len(notes) < len(times):
        pad = [-1] * (len(times) - len(notes))
        notes = list(notes) + pad

    segments = []
    current_note = None
    start = None

    for i, note in enumerate(notes):
        note = int(note)

        if note < 0:
            if current_note is not None:
                segments.append({
                    "note": int(current_note),
                    "start": float(start),
                    "end": float(times[i]),
                })
                current_note = None
                start = None
            continue

        if current_note is None:
            current_note = note
            start = times[i]
            continue

        if note != current_note:
            segments.append({
                "note": int(current_note),
                "start": float(start),
                "end": float(times[i]),
            })

            current_note = note
            start = times[i]

    if current_note is not None:
        # Estima o fim do último frame como delta entre frames (fallback 0.1s)
        if len(times) >= 2:
            delta = float(times[1] - times[0])
        else:
            delta = 0.1
        segments.append({
            "note": int(current_note),
            "start": float(start),
            "end": float(times[-1] + delta),
        })

    return segments


def save_upload_to_temp(upload_file) -> str:
    """
    Salva o arquivo enviado em disco temporário e retorna o caminho.
    """
    suffix = os.path.splitext(upload_file.filename or "")[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp.write(upload_file.file.read())
    tmp.close()
    return tmp.name

def convert_to_wav(input_path: str, channels: int | None = None, sr: int | None = None) -> str:
    """
    Converte qualquer formato suportado para WAV mono/16k quando necessário.
    """
    input_path = str(input_path)
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input audio file not found: {input_path}")

    try:
        data, file_sr = sf.read(input_path, dtype="float32")
    except Exception:
        if Path(input_path).suffix.lower() == ".wav":
            return input_path
        raise

    if data.ndim > 1:
        if channels is not None and channels == 1:
            data = np.mean(data, axis=1)
        elif data.shape[1] == 2:
            data = np.mean(data, axis=1)

    if sr is not None and file_sr != sr:
        data = librosa.resample(data, orig_sr=file_sr, target_sr=sr)

    if channels is not None and channels == 1 and data.ndim > 1:
        data = np.mean(data, axis=1)

    wav_path = input_path if Path(input_path).suffix.lower() == ".wav" else input_path + ".wav"
    sf.write(wav_path, data, sr or file_sr)

    return wav_path


def cleanup_files(*paths):
    """
    Remove arquivos temporários.
    """
    for p in paths:
        if p and os.path.exists(p):
            os.remove(p)
