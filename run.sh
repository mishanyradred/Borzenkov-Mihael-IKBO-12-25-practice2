#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ "${1:-}" = test ]; then
    shift
    exec python3 -m unittest discover -s tests "$@"
fi
exec python3 -m src.cli "$@"
