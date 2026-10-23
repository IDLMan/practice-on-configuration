#!/usr/bin/env sh
# Обе серии проверок: успешная и с ожидаемыми ошибками.
set -eu
cd "$(dirname "$0")/.."
./run.sh --vfs data/nested.csv --script examples/demo_copy.txt
if ./run.sh --vfs data/nested.csv \
    --script examples/demo_copy_errors.txt; then
    echo 'ERROR: cp failures were not detected'
    exit 1
fi
echo 'OK: cp errors were detected'
