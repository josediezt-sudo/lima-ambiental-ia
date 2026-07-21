# Arquitectura

```
  OpenAQ API ─────────────┐
  SENAMHI (CSV) ──────────┤
  NASA FIRMS API ─────────┤
  Global Forest Watch ────┤──▶ src/ingest/*.py ──▶ PostgreSQL ──▶ Grafana
  PNDA / CKAN (residuos, ─┤        (usa `distritos` y            (4 dashboards)
   agua, ruido, áreas     │         src/distritos.py para              │
   verdes) ───────────────┘         asignar cada dato a un             ▼
                                     distrito)                src/modelos/prediccion_pm25.py
  src/slga/cli.py (carga manual) ──▶ Postgres (por distrito)  (escribe forecasts en la misma BD)

  .github/workflows/ingesta.yml ──▶ corre los ingest/*.py por cron (hora/día)
```

## Componentes

- **`distritos`** (tabla, sembrada en `sql/schema.sql`): única fuente de verdad sobre los 44 gobiernos locales de Lima Metropolitana (1 provincial + 43 distritales). Todo lo demás — estaciones, residuos, indicadores, instrumentos SLGA, alertas forestales — se ancla a un `distrito_id`. Ver `docs/distritos.md`.
- **`src/distritos.py`**: resolución de distrito por nombre (tolerante a acentos, con alias) para datasets que vienen con nombre de distrito en texto (residuos, agua, ruido, áreas verdes), y por coordenada más cercana (heurística, no polígono real) para datos georreferenciados (estaciones de aire, alertas forestales).
- **`src/ingest/`**: un script por fuente de datos técnica.
  - `openaq_aire.py`: API real, bbox de los 43 distritos.
  - `senamhi_aire_csv.py`: import manual de CSV (SENAMHI no tiene API pública).
  - `residuos_ckan.py`: cliente CKAN específico para el dataset de residuos de la PNDA.
  - `ckan_generico.py`: cliente CKAN parametrizable (`config/fuentes_ckan.yml`) para agua, ruido y áreas verdes — se generalizó en vez de triplicar `residuos_ckan.py`, porque las tres fuentes son estructuralmente el mismo patrón (indicador periódico por distrito desde un dataset CKAN).
  - `nasa_firms.py`: API real de focos de calor/incendios.
  - `global_forest_watch.py`: cliente estructural para alertas de pérdida de cobertura (lomas costeras) — no verificado en vivo, ver `docs/fuentes_datos.md`.
  - Se ejecutan manualmente (`python -m src.ingest.run_ingest <comando>`) o programados vía `.github/workflows/ingesta.yml`; no hay un scheduler embebido en el proyecto mismo, para mantenerlo simple.
- **`src/slga/`**: capa de seguimiento institucional del SLGA (ver `docs/slga.md`), por distrito. A diferencia de `src/ingest/`, no hay fuente automática que "ingerir" — es una CLI (`src/slga/cli.py`) más un repositorio de acceso a datos (`src/slga/repositorio.py`) para registrar instrumentos de gestión, integrantes/sesiones de la CAM, acciones PLANEFA e indicadores GALS, cada uno resuelto contra `distritos` por nombre.
- **`sql/schema.sql`**: modelo de datos multi-dominio, todo referenciando `distritos`:
  - Aire: `estaciones` + `mediciones_aire` + `predicciones_pm25`.
  - Residuos: `residuos_distrito`.
  - Agua / ruido / áreas verdes: `indicadores_ambientales_distrito` (tabla genérica — estos dominios se publican en Perú como indicadores periódicos, no como telemetría, así que comparten una sola tabla en vez de una por dominio).
  - Bosques/incendios: `alertas_forestales` (puntual, no por distrito agregado).
  - SLGA: `instrumentos_gestion_ambiental`, `cam_integrantes`, `cam_sesiones`, `planefa_acciones`, `indicadores_gals`.
- **`src/modelos/prediccion_pm25.py`**: modelo baseline (regresión lineal sobre tendencia horaria reciente) que lee de `mediciones_aire` y escribe en `predicciones_pm25`. Es intencionalmente simple — el objetivo es tener el pipeline de datos funcionando end-to-end, no un modelo de forecasting sofisticado.
- **Grafana**: se conecta directo a Postgres vía datasource provisionado (`grafana/provisioning/`), con tres dashboards, todos con un filtro de distrito (variable de plantilla `$distrito`):
  - `aire_lima.json`: series de PM2.5 + predicción + tabla de cobertura de monitoreo por distrito.
  - `slga_municipal.json`: instrumentos, CAM, PLANEFA, GALS.
  - `ambiente_extendido.json`: agua, ruido, áreas verdes, alertas forestales/incendios.
  - No hay una capa de API intermedia — Grafana consulta SQL directamente.
- **`.github/workflows/ingesta.yml`**: automatiza la actualización periódica (aire/incendios cada hora, dominios periódicos una vez al día) — ver el comentario al inicio del archivo sobre por qué esas frecuencias y sobre que `DATABASE_URL` debe apuntar a un Postgres accesible desde internet, no al `docker compose` local.

## Por qué este diseño

- **Multi-distrito desde el esquema, no desde el código**: cada ingestor y cada comando de la CLI solo necesita resolver "a qué distrito pertenece este dato" contra la tabla `distritos` — el resto del modelo es igual para 1 distrito o para 44.
- **Una tabla genérica para lo que es estructuralmente genérico**: `indicadores_ambientales_distrito` evita triplicar el patrón de `residuos_distrito` para agua/ruido/áreas verdes; pero `mediciones_aire` (con semántica de series temporales, unicidad por timestamp, índices propios) se mantuvo separada porque es un patrón distinto (telemetría, no indicador anual) y porque ya estaba probada — no se refactorizó código que funciona solo por consistencia estética.
- **Sin over-engineering**: no hay microservicios, colas de mensajes ni API REST propia — un pipeline de ingesta + Postgres + Grafana + un cron de GitHub Actions ya cubre "monitorear lo más seguido posible y predecir riesgos", que es el objetivo del proyecto.
- **Honestidad sobre disponibilidad de datos**: donde una fuente no tiene API pública confiable o no se pudo verificar en vivo (SENAMHI, Global Forest Watch, los datasets de agua/ruido/áreas verdes), el código lo documenta explícitamente en vez de simular una integración que no está confirmada.
