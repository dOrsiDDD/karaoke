import requests
import database
from dotenv import load_dotenv
import os

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY") 

def karaoke_search (query):
    blocked_ids = database.get_blocked_ids()
    queryKaraoke = f"{query} intitle:karaoke -part -cover"
    paramsKaraoke = {
        "part": "snippet",
        "q": queryKaraoke,
        "type": "video",
        "order": "relevance",
        "videoEmbeddable": "true",
        "videoSyndicated": "true",
        "maxResults": 15,
        "key": YOUTUBE_API_KEY
    }

    r = requests.get("https://www.googleapis.com/youtube/v3/search", params=paramsKaraoke)
    results = r.json().get("items", [])
    karaoke_ids = [item["id"]["videoId"] for item in results]
    karaoke_ids = [vid for vid in karaoke_ids if vid not in blocked_ids]
    final_ids = []
    if karaoke_ids:       
        for item in karaoke_ids:
                video_id = item["id"]
                title = item["snippet"]["title"]
                artist = None
                if "-" in title:
                    parts = title.split("-")
                    artist = parts[0].strip()
                    title = parts[-1].strip()
                final_ids.append({
                    "karaokeVideoId": video_id,
                    "title": title,
                    "artist": artist
                })


    print(f"[DEBUG] Resultados da busca: {final_ids}")

    return {"results": final_ids}

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