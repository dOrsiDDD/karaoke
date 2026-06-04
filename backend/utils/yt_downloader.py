# backend/utils/youtube_downloader.py
from yt_dlp import YoutubeDL
import os
from fastapi import HTTPException

def download_audio(url: str) -> str:
    ydl_opts = {
        "format": "bestaudio",
        "outtmpl": "./temp_audios/temp_audio.%(ext)s",
    }
    
    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    output_path = './temp_audios/temp_audio.webm'
    if os.path.exists(output_path):
        return output_path
    else:
        raise HTTPException(status_code=400, detail="Falha ao baixar o audio.")
    
