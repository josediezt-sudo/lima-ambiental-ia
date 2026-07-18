# Lima Ambiental IA

Plataforma open source de monitoreo e IA ambiental para **Lima Metropolitana**. MVP enfocado en dos dominios:

- **Calidad del aire**: ingesta de mediciones PM2.5/PM10/NO2/etc. desde [OpenAQ](https://openaq.org/) (agregador global open source con estaciones en Lima) y predicción básica de picos de contaminación.
- **Residuos sólidos**: ingesta de datasets de generación y disposición final de residuos por distrito desde la [Plataforma Nacional de Datos Abiertos (PNDA)](https://www.datosabiertos.gob.pe/) / MINAM.

Ver [`docs/fuentes_datos.md`](docs/fuentes_datos.md) para el detalle de todas las fuentes abiertas evaluadas (incluyendo bosques/Geobosques y NASA FIRMS, planeadas para una siguiente fase) y [`docs/arquitectura.md`](docs/arquitectura.md) para el diseño técnico.

## Stack

- **Ingesta**: Python (scripts independientes por fuente, ejecutables manualmente o por cron/CI)
- **Almacenamiento**: PostgreSQL + PostGIS (`docker-compose.yml`)
- **Visualización**: Grafana (provisionado automáticamente con el datasource de Postgres)
- **Modelos**: scikit-learn / pandas (baseline de predicción de PM2.5)

## Arranque rápido

1. Copia `.env.example` a `.env` y completa las variables (como mínimo `OPENAQ_API_KEY`, gratis en https://explore.openaq.org/register).
2. Levanta la base de datos y Grafana:

   ```bash
   docker compose up -d db grafana
   ```

3. Aplica el esquema de base de datos:

   ```bash
   docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < sql/schema.sql
   ```

4. Instala dependencias de Python y corre una ingesta manual:

   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python -m src.ingest.run_ingest aire
   python -m src.ingest.run_ingest residuos
   ```

5. Abre Grafana en http://localhost:3000 (usuario/clave por defecto en `.env.example`) — el datasource de Postgres ya está provisionado.

## Estado del MVP

| Dominio | Fuente | Estado |
|---|---|---|
| Aire | OpenAQ API v3 | Funcional (requiere API key gratuita) |
| Aire | SENAMHI | Import manual de CSV — SENAMHI no expone una API REST pública documentada para descarga automática; ver `src/ingest/senamhi_aire_csv.py` |
| Residuos | PNDA / MINAM (CKAN) | Cliente CKAN genérico — **debes verificar el slug exacto del dataset** en el portal antes de usarlo en producción (no se pudo verificar en vivo desde este entorno, ver `docs/fuentes_datos.md`) |
| Bosques/incendios | Geobosques, Global Forest Watch, NASA FIRMS | Planeado, no implementado aún |

## Roadmap sugerido

1. Validar y ajustar el ingestor de residuos (CKAN) contra el dataset real de la PNDA.
2. Agregar dashboard de Grafana para residuos por distrito.
3. Mejorar el modelo de predicción de PM2.5 (features horarias/estacionales, validación cruzada).
4. Sumar el dominio de bosques/incendios (Geobosques + GFW + NASA FIRMS) reutilizando el mismo patrón de ingesta.
5. Automatizar la ingesta periódica (cron, GitHub Actions o un scheduler en el propio `docker-compose.yml`).

## Licencia

MIT — ver [`LICENSE`](LICENSE).
