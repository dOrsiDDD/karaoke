import psycopg2
import json
import os
import time
from typing import Set, Any

def get_connection(retries: int = 5, delay: float = 2.0):
    """
    Tenta conectar ao Postgres algumas vezes.
    Usa variáveis de ambiente com valores padrão.
    """

    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                host=os.getenv("DB_HOST", "db"),
                port=os.getenv("DB_PORT", "5432"),
            )
        except Exception as e:
            last_exc = e
            if attempt == retries:
                raise
            time.sleep(delay)
    # fallback raise
    raise last_exc

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                id SERIAL PRIMARY KEY,
                title TEXT,
                artist TEXT,
                karaoke_video_id TEXT UNIQUE,
                original_video_id TEXT UNIQUE,
                pitch_data JSONB
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocked_videos (
                video_id TEXT PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        ''')
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def add_blocked_video(video_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    # Usamos ON CONFLICT para evitar erros caso o mesmo vídeo seja reportado múltiplas vezes
    cursor.execute('''
        INSERT INTO blocked_videos (video_id)
        VALUES (%s)
        ON CONFLICT (video_id) DO NOTHING
    ''', (video_id,))
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Vídeo {video_id} adicionado à blocklist.")

def get_blocked_ids() -> Set[str]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT video_id FROM blocked_videos')

    blocked_video_ids = set()

    for row in cursor.fetchall():
        blocked_video_ids.add(row[0])

    cursor.close()
    conn.close()

    return blocked_video_ids


def save_song(title, artist, karaoke_video_id, original_video_id, pitch_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO songs (title, artist, karaoke_video_id, original_video_id, pitch_data)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (karaoke_video_id) DO NOTHING
    ''', (title, artist, karaoke_video_id, original_video_id, json.dumps(pitch_data)))
    conn.commit()
    cursor.close()
    conn.close()
    print("Música salva com sucesso:", title, artist, karaoke_video_id, original_video_id)

def get_pitch_from_db(karaoke_video_id: str) -> Any:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT pitch_data FROM songs WHERE karaoke_video_id = %s
    ''', (karaoke_video_id,))

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result:
        raise ValueError(f"Vídeo ID {karaoke_video_id} não encontrado no banco de dados")

    pitch = result[0]
    # Se for string JSON, converte; se já for lista/dict, retorna direto
    if isinstance(pitch, str):
        try:
            pitch = json.loads(pitch)
        except Exception:
            pass

    # Logging seguro (não tenta fatiar objetos que não suportam slicing)
    try:
        preview = pitch[:20] if hasattr(pitch, "__len__") else str(pitch)
        print(f"[DEBUG] Pitch original do banco: {preview}... (total {len(pitch) if hasattr(pitch, '__len__') else 'unknown'})")
    except Exception:
        print("[DEBUG] Pitch original do banco (não foi possível mostrar preview)")

    return pitch

def search_songs(query: str):
    """Busca músicas por título ou artista"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT title, artist, original_video_id FROM songs 
        WHERE title ILIKE %s OR artist ILIKE %s OR original_video_id ILIKE %s
    ''', (f"%{query}%", f"%{query}%", f"%{query}%"))

    results = [{"title": r[0], "artist": r[1], "original_video_id": r[2]} for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return results