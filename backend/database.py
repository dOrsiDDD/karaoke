import os
import time

import psycopg2
from psycopg2.extras import Json


def get_connection(retries: int = 5, delay: float = 2.0):
    """
    Tenta conectar ao Postgres algumas vezes.
    Usa variaveis de ambiente com valores padrao.
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
    raise last_exc


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS songs (
                id SERIAL PRIMARY KEY,
                title TEXT,
                karaoke_video_id TEXT UNIQUE,
                pitch_hz JSONB,
                pitch_notes JSONB,
                segments JSONB,
                sync_offset FLOAT DEFAULT 0.0
            )
            """
        )
        cursor.execute(
            """
            ALTER TABLE songs
            ADD COLUMN IF NOT EXISTS sync_offset FLOAT DEFAULT 0.0
            """
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def SaveSong(title, karaokeVideoId, pitch_hz, pitch_notes, segments):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO songs (title, karaoke_video_id, pitch_hz, pitch_notes, segments)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (karaoke_video_id) DO NOTHING
            """,
            (title, karaokeVideoId, Json(pitch_hz), Json(pitch_notes), Json(segments)),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    print("Musica salva com sucesso:", title, karaokeVideoId)


def GetSongs(query: str):
    """Busca musicas por titulo ou id do video."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT title, karaoke_video_id, pitch_notes, segments, sync_offset FROM songs
            WHERE title ILIKE %s OR karaoke_video_id ILIKE %s
            """,
            (f"%{query}%", f"%{query}%"),
        )

        return [
            {
                "title": row[0],
                "karaokeVideoId": row[1],
                "pitch_notes": row[2],
                "segments": row[3],
                "syncOffset": row[4] if row[4] is not None else 0,
            }
            for row in cursor.fetchall()
        ]
    finally:
        cursor.close()
        conn.close()


def GetSongByVideoId(karaokeVideoId: str):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT title, karaoke_video_id, pitch_notes, segments, sync_offset FROM songs
            WHERE karaoke_video_id = %s
            """,
            (karaokeVideoId,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if not row:
        return None

    return {
        "title": row[0],
        "karaokeVideoId": row[1],
        "pitch_notes": row[2],
        "segments": row[3],
        "syncOffset": row[4] if row[4] is not None else 0,
    }


def UpdateSongSyncOffset(karaokeVideoId, sync_offset):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE songs
            SET sync_offset = %s
            WHERE karaoke_video_id = %s
            """,
            (sync_offset, karaokeVideoId),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
