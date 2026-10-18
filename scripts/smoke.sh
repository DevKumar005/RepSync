#!/usr/bin/env bash
set -e

BASE_URL="${1:-http://localhost:8000}"
python scripts/smoke.py "$BASE_URL"
