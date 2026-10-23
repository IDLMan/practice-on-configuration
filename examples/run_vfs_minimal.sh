#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
./run.sh --vfs data/minimal.csv --script examples/demo_vfs.txt
