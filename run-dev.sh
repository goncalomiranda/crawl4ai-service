#!/bin/bash
# Development server with auto-reload
set -e

cd "$(dirname "$(readlink -f "$0")")"

ENV_FILE="${CRAWL4AI_ENV_FILE:-.env}"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "Missing $ENV_FILE. Copy .env.example to .env and configure the database variables." >&2
    exit 1
fi

set -a
source "$ENV_FILE"
set +a

VENV_DIR="${CRAWL4AI_VENV:-$HOME/crawl4ai-env}"
if [[ ! -f "$VENV_DIR/bin/activate" ]]; then
    echo "Virtual environment not found at $VENV_DIR. Set CRAWL4AI_VENV to its location." >&2
    exit 1
fi
source "$VENV_DIR/bin/activate"
uvicorn crawler_api:app --host 0.0.0.0 --port 8000 --reload
