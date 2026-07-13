# backend/utils/youtube_downloader.py
import os
from pathlib import Path
from fastapi import HTTPException
import yt_dlp as youtube_dl


def download_audio(url: str) -> str:
    os.makedirs("./temp_audios", exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "./temp_audios/temp_audio.%(ext)s",
        "noplaylist": True,
        "quiet": True,
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    downloaded = list(Path("./temp_audios").glob("temp_audio.*"))
    if not downloaded:
        raise HTTPException(status_code=400, detail="Falha ao baixar o áudio.")

    return str(downloaded[0])
    
