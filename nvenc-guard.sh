#!/usr/bin/env bash
set -euo pipefail

if [ ! -e /dev/nvidia0 ]; then
  mapfile -t gpus < <(ls -1 /dev/nvidia[0-9] 2>/dev/null || true)
  if [ ${#gpus[@]} -eq 1 ] && [ -e "${gpus[0]}" ]; then
    ln -sf "${gpus[0]}" /dev/nvidia0 || true
  fi
fi

echo "[nvenc-guard] Probing NVENC support..."
if ! ffmpeg -f lavfi -i nullsrc=s=64x64 -t 0.1 -c:v h264_nvenc -f null - 2>/dev/null; then
  echo "[nvenc-guard] NVENC not available on this GPU. Refusing to start." >&2
  exit 1
fi
echo "[nvenc-guard] NVENC OK. Starting worker."

exec "$@"