#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/.."

uvx ruff check src tests
uvx ruff format --check src tests
