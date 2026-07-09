FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    pkg-config \
    libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /images/wheels
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir --no-index --find-links=/images/wheels -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]