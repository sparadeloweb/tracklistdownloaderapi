#!/usr/bin/env sh
set -euo pipefail

# If a token is provided via env, write scdl.cfg for convenience
if [ -n "${SCDL_AUTH_TOKEN-}" ]; then
  mkdir -p "/root/.config/scdl"
  cat > "/root/.config/scdl/scdl.cfg" <<EOF
[DEFAULT]
oauth_token=${SCDL_AUTH_TOKEN}
EOF
fi

exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8420}


