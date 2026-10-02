#!/usr/bin/env bash
# Every test, then the example layers through the command itself.
set -Eeuo pipefail
cd "$(dirname "$0")/.."

uv run pytest tests -q "$@"
uv run semantic-layers check --layers layers
