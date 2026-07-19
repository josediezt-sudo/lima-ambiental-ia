# Arquitectura

```
                 ┌─────────────────┐
  OpenAQ API ───▶│                  │
  SENAMHI (CSV) ▶│  src/ingest/*.py │──▶ PostgreSQL + PostGIS ──▶ Grafana
  PNDA (CKAN)  ──▶│                  │        │
                 └─────────────────┘        │
                                             ▼
                                   src/modelos/prediccion_pm25.py
                                   (escribe forecasts en la misma BD)
```

## Componentes

- **`config/municipio.yml`**: única fuente de verdad sobre *qué* municipalidad está corriendo este despliegue (nombre, tipo, coordenadas de monitoreo, composición esperada de la CAM). `src/config.py` la carga; nada en el código depende de Lima directamente.
- **`src/ingest/`**: un script por fuente de datos técnica (aire, residuos). Cada uno normaliza su fuente al esquema común (`sql/schema.sql`) y hace *upsert* en Postgres. Se ejecutan manualmente o programados (cron / GitHub Actions); no hay un scheduler embebido en el MVP a propósito, para mantenerlo simple.
- **`src/slga/`**: capa de seguimiento institucional del Sistema Local de Gestión Ambiental (ver `docs/slga.md`). A diferencia de `src/ingest/`, no hay fuente automática que "ingerir" — es una CLI (`src/slga/cli.py`) más un repositorio de acceso a datos (`src/slga/repositorio.py`) para registrar instrumentos de gestión, integrantes/sesiones de la CAM, acciones PLANEFA e indicadores GALS.
- **`sql/schema.sql`**: modelo de datos multi-dominio. `estaciones` + `mediciones_aire` para aire; `residuos_distrito` para residuos; `predicciones_pm25` para el output del modelo; `instrumentos_gestion_ambiental` + `cam_integrantes` + `cam_sesiones` + `planefa_acciones` + `indicadores_gals` para el SLGA. Pensado para poder agregar un dominio nuevo (bosques/incendios) sin romper lo existente.
- **`src/modelos/prediccion_pm25.py`**: modelo baseline (regresión lineal sobre tendencia horaria reciente) que lee de `mediciones_aire` y escribe en `predicciones_pm25`. Es intencionalmente simple — el objetivo del MVP es tener el pipeline de datos funcionando end-to-end, no un modelo de forecasting sofisticado.
- **Grafana**: se conecta directo a Postgres vía datasource provisionado (`grafana/provisioning/`), con dos dashboards: monitoreo técnico (`aire_lima.json`) y gestión institucional (`slga_municipal.json`). No hay una capa de API intermedia en el MVP — Grafana consulta SQL directamente, lo cual es suficiente para dashboards y reduce superficie a mantener.

## Por qué este diseño

- **Multi-dominio desde el esquema, no desde el código**: cada ingestor es independiente y solo necesita conocer su propia tabla destino, lo que permite sumar bosques/incendios en la fase 2 sin refactor.
- **Sin over-engineering**: no hay microservicios, colas de mensajes ni API REST propia en el MVP — con un pipeline de ingesta + Postgres + Grafana ya se cubre "monitorear en tiempo casi real y predecir riesgos", que es el objetivo del piloto.
- **Honestidad sobre disponibilidad de datos**: donde una fuente peruana no tiene API pública confiable (SENAMHI), el ingestor documenta el proceso manual en vez de simular una integración automática que no existe.
