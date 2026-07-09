import shutil

from fastapi import FastAPI, UploadFile, HTTPException, File, Form
from fastapi.responses import JSONResponse
from pitch_extractor import extract_pitch
from database import GetSongs, GetSongByVideoId, SaveSong
from scoring import CalculateScore
from utils.yt_downloader import download_audio
from utils.extract_vocal import extract_vocals
from utils.audio_utils import save_upload_to_temp, convert_to_wav, cleanup_files, build_segments, clean_note_sequence, ConverterFreqParaMidi
from database import init_db
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import numpy as np
from pydantic import BaseModel
import uvicorn
import os
import traceback

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.on_event("startup")
def startup_event():
    init_db()


class OriginalVideoResponse(BaseModel):
    originalVideoId: Optional[str] = None

def pitch_to_midi_and_notes(pitch_hz):
    midi_float = ConverterFreqParaMidi(pitch_hz)
    pitch_midi = np.where(
        np.isfinite(midi_float),
        np.round(midi_float),
        -1,
    ).astype(int)
    pitch_notes = np.where(pitch_midi >= 0, pitch_midi % 12, -1).astype(int)
    return pitch_midi, pitch_notes

@app.post("/analyze")
async def analyze(karaokeVideoId: str = Form(...), user_audio: UploadFile = File(...)):
    tmp_path = None
    wav_path = None
    try:
        print(f"[DEBUG] Iniciando análise para vídeo {karaokeVideoId}")

        if user_audio is None:
            raise HTTPException(status_code=400, detail="Arquivo de áudio não recebido.")

        # 1. Salva upload temporário
        tmp_path = save_upload_to_temp(user_audio)
        if os.path.getsize(tmp_path) == 0:
            raise HTTPException(status_code=400, detail="O áudio enviado está vazio.")
        print(f"[DEBUG] Arquivo salvo em: {tmp_path}")

        # 2. Converte para wav normalizado
        wav_path = convert_to_wav(tmp_path, channels=1, sr=16000)
        print(f"[DEBUG] Arquivo convertido para WAV: {wav_path}")

        # 3. Extrai pitches
        userPitch, userTimestamps = extract_pitch(wav_path)
        if len(userPitch) == 0 or np.all(userPitch <= 0):
            raise HTTPException(status_code=400, detail="Não foi possível extrair pitch do áudio enviado.")

        userMidi, userNotes = pitch_to_midi_and_notes(userPitch)
        userNotes = clean_note_sequence(userNotes)
        print(f"[DEBUG] Pitch extraído do usuário: {userPitch[:20]}... (total {len(userPitch)})")

        song = GetSongByVideoId(karaokeVideoId)
        if not song:
            raise HTTPException(status_code=404, detail="Música não encontrada.")

        originalNotes = song.get("pitch_notes")
        if originalNotes is None:
            raise HTTPException(status_code=404, detail="Pitch original não encontrado. Música não cadastrada.")
        print(f"[DEBUG] Pitch original carregado: {originalNotes[:20]}... (total {len(originalNotes)})")

        # 4. Calcula nota
        score = CalculateScore(userNotes, originalNotes)
        print(f"[DEBUG] Score calculado: {score}")

        return JSONResponse({
            "status": "success",
            "score": round(score, 2)
        })

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro interno ao processar o áudio: {str(e)}") from e

    finally:
        # 5. Limpeza
        cleanup_files(tmp_path, wav_path)

@app.get("/song/{karaokeVideoId}")
async def get_song(karaokeVideoId: str):
    song = GetSongByVideoId(karaokeVideoId)
    if not song:
        raise HTTPException(status_code=404, detail="Música não encontrada.")
    return song


@app.get("/search_song_db")
async def SearchSongsFromDb(q: str = ""):
    try:
        songs = GetSongs(q)
        return {"songs": songs}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao buscar músicas no banco de dados")


@app.post("/add_song")
async def add_song(karaokeVideoId: str = Form(...), title: str = Form(...), query: str = Form(...)):
    originalSearchQuery = f"{query} intitle:lyrics -karaoke -instrumental"
    from utils.youtube_search import original_search
    originalVideoId = original_search(originalSearchQuery).get("originalVideoId")
    
    if not originalVideoId:
        raise HTTPException(status_code=404, detail="Vídeo original não encontrado no YouTube")
    
    originalUrl = f"https://www.youtube.com/watch?v={originalVideoId}"

    audioPath = None
    vocalPath = None
    try:
        # 1. Baixa áudio e extrai metadados
        audioPath = download_audio(originalUrl)

        #2. Extrai vocais
        vocalPath = extract_vocals(audioPath)
        
        # 3. Processa o áudio
        pitchHz, timestamps = extract_pitch(vocalPath)
        pitchMidi, pitchNotes = pitch_to_midi_and_notes(pitchHz)
        pitchMidiCleaned = clean_note_sequence(pitchMidi)
        segments = build_segments(timestamps, pitchMidiCleaned)

        # 4. Salva no banco
        pitchHzList = pitchHz.tolist()
        pitchNotesList = pitchNotes.tolist()
        SaveSong(title, karaokeVideoId, pitchHzList, pitchNotesList, segments)
        
        response = {
            "status": "success",
            "details": {
                "karaokeVideoId": karaokeVideoId,
                "original_video_id": originalVideoId,
                "pitch_hz": pitchHzList,
                "pitch_notes": pitchNotesList,
                "segments": segments
            }
        }
        return response
    except Exception as e:
        # Garante que o arquivo seja deletado mesmo em caso de erro
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Erro ao processar o vídeo: {str(e)}")
    finally:
        for path in [audioPath, vocalPath]:
            if not path:
                continue
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            elif os.path.exists(path):
                os.remove(path)

        if vocalPath:
            parent_dir = os.path.dirname(vocalPath)
            if parent_dir and os.path.isdir(parent_dir):
                shutil.rmtree(parent_dir, ignore_errors=True)

@app.get("/karaoke_yt_search")
async def KaraokeYoutubeSearch(q: str):
    from utils.youtube_search import karaoke_search
    try:
        results = karaoke_search(q)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro na busca no YouTube")
        

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
