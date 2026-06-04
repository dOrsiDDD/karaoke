from yt_dlp import YoutubeDL

url = "https://www.youtube.com/watch?v=qgaRVvAKoqQ"

opts = {
    "format": "bestaudio",
    "outtmpl": "test_audio.%(ext)s",
    "ffmpeg_location": "/usr/bin/ffmpeg",
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'wav',
        'preferredquality': '192',
    }],
}

with YoutubeDL(opts) as ydl:
    ydl.download([url])