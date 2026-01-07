from fastapi import FastAPI, UploadFile, HTTPException, File, Form
from fastapi.responses import JSONResponse
from pitch_extractor import extract_pitch
from database import get_pitch_from_db, search_songs, save_song
import database
from scoring import calculate_score
from utils.yt_downloader import download_audio, extract_metadata, progress_hook
from utils.audio_utils import save_upload_to_temp, convert_to_wav, cleanup_files
from database import init_db
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from pydantic import BaseModel
import uvicorn
import os

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

class SongRequest(BaseModel):
    karaoke_url: str
    original_url: str

class OriginalVideoResponse(BaseModel):
    originalVideoId: Optional[str] = None

class ReportRequest(BaseModel):
    video_id: str

@app.post("/analyze")
async def analyze(karaoke_video_id: str = Form(...), user_audio: UploadFile = File(...)):
    tmp_path = None
    wav_path = None
    try:
        print(f"[DEBUG] Iniciando análise para vídeo {karaoke_video_id}")
        # 1. Salva upload temporário
        tmp_path = save_upload_to_temp(user_audio)
        print(f"[DEBUG] Arquivo salvo em: {tmp_path}")

        # 2. Converte para wav normalizado
        wav_path = convert_to_wav(tmp_path)
        print(f"[DEBUG] Arquivo convertido para WAV: {wav_path}")

        # 3. Extrai pitches
        user_pitch = extract_pitch(wav_path)
        print(f"[DEBUG] Pitch extraído do usuário: {user_pitch[:20]}... (total {len(user_pitch)})")
        original_pitch = get_pitch_from_db(karaoke_video_id)
        if original_pitch is None:
            raise HTTPException(
            status_code=404,
            detail="Pitch original não encontrado. Música não cadastrada."
            )
        print(f"[DEBUG] Pitch original carregado: {original_pitch[:20]}... (total {len(original_pitch)})")

        # 4. Calcula nota
        score = calculate_score(user_pitch, original_pitch)
        print(f"[DEBUG] Score calculado: {score}")

        return JSONResponse({
            "status": "success",
            "score": round(score, 2)
        })

    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

    finally:
        # 5. Limpeza
        cleanup_files(tmp_path, wav_path)
    
@app.get("/songs")
async def search_songs_endpoint(q: str = ""):
    try:
        results = search_songs(q)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro na busca")
    
@app.post("/add_song")
async def add_song(req: SongRequest):
    karaoke_url = req.karaoke_url
    original_url = req.original_url
    audio_path = None
    karaoke_id = karaoke_url.split('v=')[-1].split('&')[0]
    original_id = original_url.split('v=')[-1].split('&')[0]

    existing_song = search_songs(karaoke_id)
    if existing_song:
        print(f"[DEBUG] Música já cadastrada: {karaoke_id}")
        return JSONResponse({
            "status": "exists",
            "message": "Música já cadastrada",
            "details": existing_song
        })

    try:
        # 1. Baixa áudio e extrai metadados
        audio_path = download_audio(original_url, progress_hook=progress_hook)
        title, artist = extract_metadata(original_url)
        
        # 2. Processa o áudio
        pitch_data = extract_pitch(audio_path).tolist() # Converte numpy array para lista
        
        # 3. Salva no banco de dados
        save_song(
            title=title,
            artist=artist,
            karaoke_video_id=karaoke_id,
            original_video_id=original_id,
            pitch_data=pitch_data 
        )
        
        response = {
            "status": "success",
            "details": {
                "title": title,
                "artist": artist,
                "karaoke_video_id": karaoke_id,
                "original_video_id": original_id,
                "pitch_data": pitch_data
            }
        }
        return response
    except Exception as e:
        # Garante que o arquivo seja deletado mesmo em caso de erro
        print(f"Erro ao processar o vídeo: {e}")
        raise HTTPException(status_code=400, detail=f"Erro ao processar o vídeo: {str(e)}")
    finally:
        if audio_path and os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"Arquivo temporário {audio_path} removido!")

@app.get("/karaoke_search")
async def karaoke_search_endpoint(q: str):
    from utils.youtube_search import karaoke_search
    try:
        results = karaoke_search(q)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro na busca no YouTube")
    
@app.get("/original_search")
async def original_search_endpoint(q: str) -> OriginalVideoResponse:
    from utils.youtube_search import original_search
    try:
        result = original_search(q)
        if result and "originalVideoId" in result:
            return OriginalVideoResponse(originalVideoId=result["originalVideoId"])
        else:
            return OriginalVideoResponse(originalVideoId=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro na busca do vídeo original no YouTube")
    

@app.post("/report_bad_video")
async def report_bad_video(req: ReportRequest):
    """
    Endpoint para um cliente reportar um vídeo que não funciona.
    O vídeo é adicionado a uma blocklist no banco de dados.
    """
    try:
        database.add_blocked_video(
            video_id=req.video_id,
        )
        return {"status": "success", "message": "Video reportado e bloqueado."}
    except Exception as e:
        # Captura qualquer erro de banco de dados e retorna uma resposta adequada
        raise HTTPException(status_code=500, detail=f"Erro ao reportar vídeo: {e}")



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)