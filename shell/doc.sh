#!/usr/bin/env bash
# Serve the documentation on http://localhost:8000 (rebuilds on change).
set -Eeuo pipefail
cd "$(dirname "$0")/.."

uvx zensical serve "$@"
