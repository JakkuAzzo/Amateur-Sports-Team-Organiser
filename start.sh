#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is required but not installed."
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "Error: docker compose is required but not installed."
  exit 1
fi

if [[ ! -f ".env" && -f ".env.example" ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

echo "Starting Docker services (db)..."
"${COMPOSE_CMD[@]}" up -d db

echo "Waiting for Postgres to become ready..."
for i in {1..30}; do
  if "${COMPOSE_CMD[@]}" exec -T db pg_isready -U "${POSTGRES_USER:-sports}" -d "${POSTGRES_DB:-sportsdb}" >/dev/null 2>&1; then
    break
  fi
  if [[ "$i" -eq 30 ]]; then
    echo "Error: Postgres did not become ready in time."
    exit 1
  fi
  sleep 1
done

if [[ ! -d ".venv" ]]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing Python dependencies..."
pip install -r requirements.txt

export FLASK_APP=wsgi.py
export FLASK_DEBUG="${FLASK_DEBUG:-1}"

if [[ ! -d "migrations" ]]; then
  echo "Initializing migrations..."
  flask db init
  flask db migrate -m "init"
fi

echo "Applying database migrations..."
flask db upgrade

echo "Seeding demo content..."
flask seed-demo

echo "Starting Flask app on http://127.0.0.1:5000"
exec flask run
