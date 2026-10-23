#!/usr/bin/env sh
# Запуск с параметром стартового сценария.
set -eu
cd "$(dirname "$0")/.."
./run.sh --script examples/startup.txt
