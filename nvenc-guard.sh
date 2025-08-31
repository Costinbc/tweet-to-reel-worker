#!/usr/bin/env bash
set -euo pipefail

if [ ! -e /dev/nvidia0 ]; then
  mapfile -t gpus < <(ls -1 /dev/nvidia[0-9] 2>/dev/null || true)
  if [ ${#gpus[@]} -eq 1 ] && [ -e "${gpus[0]}" ]; then
    ln -sf "${gpus[0]}" /dev/nvidia0 || true
  fi
fi

exec "$@"