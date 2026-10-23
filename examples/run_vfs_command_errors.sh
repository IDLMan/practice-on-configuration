#!/usr/bin/env sh
# Убедиться, что ошибки команд отображаются и дают ненулевой код.
set -eu
cd "$(dirname "$0")/.."
if ./run.sh --vfs data/nested.csv \
    --script examples/demo_vfs_errors.txt; then
    echo 'ERROR: VFS command errors were not detected'
    exit 1
fi
echo 'OK: VFS command errors were detected'
