#!/usr/bin/env sh
# Нормальные и ошибочные сценарии (второй должен вернуть код 1).
set -eu
cd "$(dirname "$0")/.."
./run.sh --vfs data/nested.csv --script examples/demo_commands.txt
if ./run.sh --vfs data/nested.csv \
    --script examples/demo_errors.txt; then
    echo 'ERROR: command failures were not detected'
    exit 1
fi
echo 'OK: invalid commands were detected'
