#!/usr/bin/env sh
# Проверка: приложение должно завершиться с ошибкой, скрипт — успешно.
set -eu
cd "$(dirname "$0")/.."
if ./run.sh --vfs data/does_not_exist.csv \
    --script examples/demo_vfs.txt; then
    echo 'ERROR: missing VFS was accepted'
    exit 1
fi
echo 'OK: missing VFS detected'
