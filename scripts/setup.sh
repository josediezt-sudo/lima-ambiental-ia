#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Creado .env a partir de .env.example — edítalo antes de continuar (OPENAQ_API_KEY, etc.)"
fi

docker compose up -d db grafana

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

echo "Esperando a que Postgres esté listo..."
until docker compose exec -T db pg_isready -U "$(grep POSTGRES_USER .env | cut -d= -f2)" >/dev/null 2>&1; do
  sleep 1
done

set -a
source .env
set +a
docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < sql/schema.sql

echo "Listo. Grafana: http://localhost:3000 — corre 'python -m src.ingest.run_ingest aire' para la primera ingesta."
