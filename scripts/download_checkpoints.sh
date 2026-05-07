#!/usr/bin/env bash
# Download the CoTracker checkpoints expected by the pipeline.
#
# Usage:
#   scripts/download_checkpoints.sh           # writes to ./checkpoints
#   COTRACKER_LIPS_CHECKPOINTS=/path scripts/download_checkpoints.sh

set -euo pipefail

DEST="${COTRACKER_LIPS_CHECKPOINTS:-./checkpoints}"
mkdir -p "$DEST"
cd "$DEST"

echo "[checkpoints] downloading to $(pwd)"

if [[ ! -f cotracker2.pth ]]; then
    curl -fL --progress-bar \
        -o cotracker2.pth \
        https://huggingface.co/facebook/cotracker/resolve/main/cotracker2.pth
fi

if [[ ! -f scaled_online.pth ]]; then
    curl -fL --progress-bar \
        -o scaled_online.pth \
        https://huggingface.co/facebook/cotracker3/resolve/main/scaled_online.pth
fi

echo "[checkpoints] done."
echo
echo "Note: the SPIGA model weights (spiga_300wprivate.pt) must be downloaded"
echo "manually from the Google Drive linked in docs/install.md and placed at"
echo "  SPIGA/spiga/models/weights/spiga_300wprivate.pt"
