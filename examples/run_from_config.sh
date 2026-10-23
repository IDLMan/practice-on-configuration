#!/usr/bin/env sh
# Конфигурация JSON; CLI переопределяет приглашение.
set -eu
cd "$(dirname "$0")/.."
./run.sh --config examples/config.json --prompt 'overridden$ '
