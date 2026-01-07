# backend/utils/youtube_downloader.py
import yt_dlp
import re
import os
from fastapi import HTTPException

from typing import Callable, Optional

os.environ["FFMPEG_BINARY"] = "/usr/bin/ffmpeg"
os.environ["FFPROBE_BINARY"] = "/usr/bin/ffprobe"

def download_audio(url: str, progress_hook: Optional[Callable[[dict], None]] = None) -> str:
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        "ffmpeg_location": "/usr/bin/ffmpeg",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'progress_hooks': [progress_hook] if progress_hook else [],
        'quiet': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
    
    output_path = 'temp_audio.wav'
    if os.path.exists(output_path):
        return output_path
    else:
        raise HTTPException(status_code=400, detail="Falha ao baixar o audio.")

def extract_metadata(url: str) -> tuple[str, str]:
    """Extrai título e artista do vídeo do YouTube"""
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'Unknown Title')
        artist = info.get('uploader', 'Unknown Artist')
        
        # Tenta extrair artista do título (ex: "Artista - Música")
        if '-' in title:
            parts = title.split('-')
            artist = parts[0].strip()
            title = parts[-1].strip()
            
        return title, artist
    
def progress_hook(d: dict):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '?')
        speed = d.get('_speed_str', '?')
        print(f"\rDownload: {percent} a {speed}", end='', flush=True)
    elif d['status'] == 'finished':
        print("\nDownload concluído! Convertendo áudio...")