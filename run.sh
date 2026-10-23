#!/usr/bin/env sh
# Run as ./run.sh [CLI arguments].
set -eu
cd "$(dirname "$0")"
python3 -m src.main "$@"
