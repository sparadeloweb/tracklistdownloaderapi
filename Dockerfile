FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8420

# System deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python deps first (better layer caching)
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# App code
COPY . .

# Normalize line endings and ensure executable bit for entrypoint (Windows-safe)
RUN sed -i 's/\r$//' docker-entrypoint.sh && chmod +x docker-entrypoint.sh

EXPOSE 8420

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 CMD curl -fsS http://127.0.0.1:${PORT:-8420}/ || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]


