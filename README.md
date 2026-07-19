# Lima Ambiental IA

Plataforma open source de monitoreo e IA ambiental, con un piloto inicial en
**Lima Metropolitana** pero **personalizable para cualquier municipalidad del
Perú** (ver [`config/municipio.example.yml`](config/municipio.example.yml)).
Cubre dos capas complementarias:

- **Monitoreo técnico**: ingesta de calidad del aire (PM2.5/PM10/NO2/etc. vía
  [OpenAQ](https://openaq.org/)) y residuos sólidos por distrito (vía la
  [Plataforma Nacional de Datos Abiertos](https://www.datosabiertos.gob.pe/)),
  con predicción básica de picos de contaminación.
- **Gestión institucional (SLGA)**: seguimiento del
  [Sistema Local de Gestión Ambiental](docs/slga.md) que cada municipalidad debe
  operar por ley — instrumentos de gestión (Política/Diagnóstico/Plan de
  Acción/Agenda Ambiental Local, PIGARS, PLANEFA), composición y sesiones de la
  Comisión Ambiental Municipal (CAM), y avance hacia la certificación GALS.

Ver [`docs/fuentes_datos.md`](docs/fuentes_datos.md) para las fuentes de datos
técnicas evaluadas (incluyendo bosques/Geobosques y NASA FIRMS, planeadas para una
siguiente fase), [`docs/slga.md`](docs/slga.md) para el marco legal del SLGA y su
mapeo al modelo de datos, y [`docs/arquitectura.md`](docs/arquitectura.md) para el
diseño técnico general.

## Stack

- **Ingesta**: Python (scripts independientes por fuente, ejecutables manualmente o por cron/CI)
- **Almacenamiento**: PostgreSQL + PostGIS (`docker-compose.yml`)
- **Visualización**: Grafana (provisionado automáticamente con el datasource de Postgres)
- **Modelos**: scikit-learn / pandas (baseline de predicción de PM2.5)

## Arranque rápido

1. Copia `config/municipio.example.yml` a `config/municipio.yml` y personalízalo
   para tu municipalidad (nombre, coordenadas, composición esperada de la CAM).
2. Copia `.env.example` a `.env` y completa las variables (como mínimo `OPENAQ_API_KEY`, gratis en https://explore.openaq.org/register).
3. Levanta la base de datos y Grafana:

   ```bash
   docker compose up -d db grafana
   ```

4. Aplica el esquema de base de datos:

   ```bash
   docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < sql/schema.sql
   ```

5. Instala dependencias de Python y corre una ingesta manual:

   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python -m src.ingest.run_ingest aire
   python -m src.ingest.run_ingest residuos
   ```

6. (Opcional) carga datos de ejemplo del SLGA para ver el dashboard institucional poblado:

   ```bash
   python -m src.slga.cli seed-ejemplo
   ```

7. Abre Grafana en http://localhost:3000 (usuario/clave por defecto en `.env.example`) — datasource, dashboard de aire y dashboard SLGA ya están provisionados.

## Estado del MVP

| Dominio | Fuente | Estado |
|---|---|---|
| Aire | OpenAQ API v3 | Funcional (requiere API key gratuita; ubicación configurable en `config/municipio.yml`) |
| Aire | SENAMHI | Import manual de CSV — SENAMHI no expone una API REST pública documentada para descarga automática; ver `src/ingest/senamhi_aire_csv.py` |
| Residuos | PNDA / MINAM (CKAN) | Cliente CKAN genérico — **debes verificar el slug exacto del dataset** en el portal antes de usarlo en producción (no se pudo verificar en vivo desde este entorno, ver `docs/fuentes_datos.md`) |
| SLGA (institucional) | Carga manual vía `src/slga/cli.py` | Funcional — instrumentos de gestión, CAM, PLANEFA e indicadores GALS; ver `docs/slga.md` |
| Bosques/incendios | Geobosques, Global Forest Watch, NASA FIRMS | Planeado, no implementado aún |

## Roadmap sugerido

1. Validar y ajustar el ingestor de residuos (CKAN) contra el dataset real de la PNDA.
2. Agregar dashboard de Grafana para residuos por distrito.
3. Mejorar el modelo de predicción de PM2.5 (features horarias/estacionales, validación cruzada).
4. Sumar el dominio de bosques/incendios (Geobosques + GFW + NASA FIRMS) reutilizando el mismo patrón de ingesta.
5. Automatizar la ingesta periódica (cron, GitHub Actions o un scheduler en el propio `docker-compose.yml`).
6. Vincular indicadores SLGA/GALS con los datos técnicos (ej. cobertura real de monitoreo de aire como insumo del indicador GALS de calidad ambiental) en vez de cargarlos por separado.

## Licencia

MIT — ver [`LICENSE`](LICENSE).
