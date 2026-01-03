import requests
import database
from dotenv import load_dotenv
from fastapi import HTTPException
import os

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") 

def karaoke_search (query):
    blocked_ids = set(database.get_blocked_ids())
    queryKaraoke = f"{query} intitle:karaoke -part -cover"
    paramsKaraoke = {
        "part": "snippet",
        "q": queryKaraoke,
        "type": "video",
        "order": "relevance",
        "videoEmbeddable": "true",
        "videoSyndicated": "true",
        "maxResults": 3,
        "key": YOUTUBE_API_KEY
    }

    try:
        r = requests.get(
        "https://www.googleapis.com/youtube/v3/search",
        params = paramsKaraoke,
        timeout = 10
        )
        r.raise_for_status()
        items = r.json().get("items", [])
    except Exception as e:
         print (f"Error: Youtube API error {e}")
         raise HTTPException(status_code=500,detail="Erro na busca no youtube")
    
    results = []

    for item in items:
        video_id = item["id"].get("videoId")
        if not video_id:
            continue
        if video_id in blocked_ids:
            continue
         
        title = item["snippet"]["title"]
        artist = None

        if "-" in title:
            parts = title.split("-")
            artist = parts[0].strip()
            title = parts[-1].strip()

        results.append({
             "karaokeVideoId": video_id,
             "title": title,
             "artist": artist
        })

    print("[DEBUG] Retornando para frontend:", results)
    return {"results": results}

    

def original_search(q: str):
        query_original = f"{q} intitle:lyrics -karaoke -instrumental"
        params_original = {
            "part": "snippet",
            "q": query_original,
            "type": "video",
            "order": "relevance",
            "videoEmbeddable": "true",
            "maxResults": 1,    
            "key": YOUTUBE_API_KEY
            }
            
        response = requests.get("https://www.googleapis.com/youtube/v3/search", params=params_original)
        response.raise_for_status() # Lança um erro para respostas HTTP ruins (4xx ou 5xx)

        results = response.json().get("items", [])
            
        if results:
            video_id = results[0]["id"]["videoId"]
            return {"originalVideoId": video_id}
            
        return {"originalVideoId": None}