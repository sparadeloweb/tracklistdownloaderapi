FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8420

# System deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
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

# Healthcheck with proper curl path
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS http://127.0.0.1:${PORT:-8420}/ || exit 1

# Expose a default port (actual port is controlled by $PORT)
EXPOSE 8420

ENTRYPOINT ["/app/docker-entrypoint.sh"]


