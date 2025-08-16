#!/bin/sh
set -eu

# If a token is provided via env, write scdl.cfg for convenience
if [ -n "${SCDL_AUTH_TOKEN-}" ]; then
  mkdir -p "/root/.config/scdl"
  cat > "/root/.config/scdl/scdl.cfg" <<EOF
[DEFAULT]
oauth_token=${SCDL_AUTH_TOKEN}
EOF
fi

# Ensure the app directory exists and contains the expected files
if [ ! -f "/app/app/main.py" ]; then
  echo "ERROR: app/main.py not found!"
  ls -la /app/
  ls -la /app/app/ || echo "app/ directory not found"
  exit 1
fi

echo "Starting SoundCloud Downloader API on port ${PORT:-8420}..."
echo "SCDL config: $(ls -la /root/.config/scdl/ 2>/dev/null || echo 'not configured')"

# Start uvicorn with proper signal handling
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8420} --log-level info


