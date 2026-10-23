#!/usr/bin/env sh
# Параметры CLI: приглашение, путь к VFS, стартовый сценарий.
set -eu
cd "$(dirname "$0")/.."
./run.sh --vfs data/nested.csv --prompt 'custom$ ' \
    --script examples/startup.txt
