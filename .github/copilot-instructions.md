<!-- Copilot / AI agent instructions for the karaoke project -->
# Project snapshot & quick orientation

This repository is a small karaoke scorer app with three main runtime surfaces:

- Backend (Python, FastAPI): audio processing, pitch extraction and scoring. Key files: `backend/main.py`, `backend/pitch_extractor.py`, `backend/scoring.py`, `backend/database.py`.
- Frontend (Vue + Vite): single-page UI in `frontend/` served locally with `npm run dev`.
- Desktop wrapper (Tauri/Rust): native packaging under `src-tauri/` (requires Rust + Tauri toolchain).

High-level flow:
- User uploads a recorded audio + selects a karaoke video ID -> `/analyze` endpoint converts audio, extracts pitch (`pitch_extractor.py`) and compares with stored pitch vector using DTW (`scoring.py`).
- Admin/ingest flow: `/add_song` will download original audio via `utils/yt_downloader.py`, extract pitch and store it in Postgres (`database.py`).

# Immediate dev workflows (how to run & debug)
- Start backend + Postgres using Docker Compose (recommended):

  docker-compose up --build

  - This builds the `backend` image (see `backend/Dockerfile`) and exposes FastAPI on port 8000.
  - The Docker image installs `ffmpeg` and system libs required by `librosa`/`pyworld`.

- Run backend locally (no Docker):

  cd backend
  pip install -r requirements.txt
  # ensure ffmpeg is available on PATH (or set FFMPEG_BINARY env)
  uvicorn main:app --reload --host 0.0.0.0 --port 8000

- Frontend dev server:

  cd frontend
  npm install
  npm run dev

- Tauri / desktop: requires Rust toolchain + `tauri` CLI. Use `cargo tauri dev` from repo root (or `frontend` as the web assets directory) after installing Rust and Tauri.

# Important patterns & conventions (do NOT assume common defaults)
- Database connection: `backend/database.py` uses custom env vars `DB_NAME`, `DB_USER`, `DB_PASS`, `DB_HOST`, `DB_PORT` and includes retry logic for Compose startup — use these env names when testing locally outside Docker.
- Audio normalization: `utils/audio_utils.py` always converts uploaded audio to mono 16k WAV before pitch extraction. Agents should preserve this conversion step when modifying the pipeline.
- Pitch format: `pitch_extractor.extract_pitch` returns a 1D float array of Hz (pyworld f0). Code often filters zeros (silence) before DTW. Treat pitch arrays as possibly JSON-serialized lists when stored in DB (`pitch_data` JSONB).
- YouTube tooling: `utils/yt_downloader.py` and `utils/youtube_search.py` depend on `yt-dlp` and the YouTube Data API (env var `YOUTUBE_API_KEY`). `yt_downloader` expects `ffmpeg` at `/usr/bin/ffmpeg` inside Docker; adjust on-host PATH for local runs.

# Typical endpoints & example usages (for tests and quick checks)
- POST `/analyze` — Form data: `karaoke_video_id` (string) and `user_audio` (file). Returns JSON `{ status, score }`.
- POST `/add_song` — JSON body: `{ "karaoke_url": "...", "original_url": "..." }`. Downloads original audio, extracts pitch and saves to DB.
- GET `/songs?q=...` — search stored songs.

# Common pitfalls / gotchas for contributors and agents
- Native deps: `librosa`, `pyworld`, `pydub` and `ffmpeg` require native libs and build tools. Prefer the Docker flow for CI/dev to avoid local environment setup issues.
- Windows developers: backend Dockerfile is Linux-first; local Windows runs must ensure `ffmpeg` is installed and available, and `yt-dlp` post-processing paths may need adjusting.
- Database env mismatch: `docker-compose.yml` sets `DATABASE_URL` for the container, but `database.py` reads `DB_*` vars — `.env` or compose/env mapping is the source of truth. When adding env vars, set both forms if unsure.

# Where to look when extending functionality
- Audio pipeline: follow the chain `main.py -> utils.audio_utils -> pitch_extractor` -> `scoring.py`.
- Adding search or metadata: `utils/youtube_search.py` and `utils/yt_downloader.py`.
- DB schema & migrations: no migration framework — `database.init_db()` creates tables at startup. Keep changes backwards-compatible or add migration steps manually.

# Coding agent behavior rules (project-specific)
- Prefer running and testing changes inside Docker Compose before proposing native-install instructions.
- Preserve the WAV normalization (mono, 16k) and silence-filtering behavior — breaking this changes scoring semantics.
- When modifying pitch data storage format, update `database.get_pitch_from_db` read-path AND `scoring.calculate_score` input expectations.

# Quick references (files)
- Backend entry: `backend/main.py`
- Pitch extraction: `backend/pitch_extractor.py`
- Scoring: `backend/scoring.py`
- DB: `backend/database.py`
- YouTube / downloader: `backend/utils/yt_downloader.py`, `backend/utils/youtube_search.py`
- Frontend app: `frontend/src` and `frontend/package.json`

If anything here is unclear or you'd like the instructions to include CI commands, testing examples, or expanded troubleshooting steps (Windows ffmpeg setup, local Python virtualenv recipe), tell me which area to expand. 