# backend/utils/youtube_downloader.py
import os
from fastapi import HTTPException
import yt_dlp as youtube_dl

def download_audio(url: str) -> str:
    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": "./temp_audios/temp_audio.%(ext)s",
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    output_path = './temp_audios/temp_audio.webm'
    if os.path.exists(output_path):
        return output_path
    else:
        raise HTTPException(status_code=400, detail="Falha ao baixar o audio.")
    
