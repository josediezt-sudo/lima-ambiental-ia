# Lima Ambiental IA

Plataforma open source de monitoreo e IA ambiental para **los 44 gobiernos
locales de Lima Metropolitana** (1 municipalidad provincial + 43 distritales).
Cubre dos capas complementarias:

- **Monitoreo técnico, por distrito**: calidad del aire (PM2.5/PM10/etc. vía
  [OpenAQ](https://openaq.org/), con predicción básica de picos), residuos
  sólidos, agua, ruido, áreas verdes ([Plataforma Nacional de Datos
  Abiertos](https://www.datosabiertos.gob.pe/)) e incendios/pérdida de
  cobertura vegetal en las lomas costeras ([NASA
  FIRMS](https://firms.modaps.eosdis.nasa.gov/) / [Global Forest
  Watch](https://www.globalforestwatch.org/)).
- **Gestión institucional (SLGA), por distrito**: seguimiento del [Sistema
  Local de Gestión Ambiental](docs/slga.md) que cada uno de los 44 gobiernos
  locales debe operar por ley — instrumentos de gestión (Política/Diagnóstico/
  Plan de Acción/Agenda Ambiental Local, PIGARS, PLANEFA), composición y
  sesiones de su Comisión Ambiental Municipal (CAM), y avance hacia la
  certificación GALS.

Todo se actualiza automáticamente vía [GitHub
Actions](.github/workflows/ingesta.yml) (aire/incendios cada hora, dominios
periódicos una vez al día — ver ese archivo para el porqué de esas frecuencias).

Ver [`docs/distritos.md`](docs/distritos.md) para cómo se modelan los 44
gobiernos locales, [`docs/fuentes_datos.md`](docs/fuentes_datos.md) para el
detalle de cada fuente técnica (con notas honestas sobre cuáles están
verificadas en vivo y cuáles no), [`docs/slga.md`](docs/slga.md) para el marco
legal del SLGA, y [`docs/arquitectura.md`](docs/arquitectura.md) para el diseño
técnico general.

## Stack

- **Ingesta**: Python (un script por fuente, ejecutables manualmente o por el cron de GitHub Actions)
- **Almacenamiento**: PostgreSQL (`docker-compose.yml`)
- **Visualización**: Grafana (provisionado automáticamente, 3 dashboards)
- **Modelos**: scikit-learn / pandas (baseline de predicción de PM2.5)

## Arranque rápido

1. Copia `.env.example` a `.env` y completa las variables (como mínimo
   `OPENAQ_API_KEY`, gratis en https://explore.openaq.org/register).
2. Levanta la base de datos y Grafana:

   ```bash
   docker compose up -d db grafana
   ```

3. Aplica el esquema de base de datos (esto también siembra los 44 gobiernos locales):

   ```bash
   docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < sql/schema.sql
   ```

4. Instala dependencias de Python y corre una ingesta manual:

   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python -m src.ingest.run_ingest aire
   python -m src.ingest.run_ingest residuos   # requiere RESIDUOS_CKAN_PACKAGE_ID real, ver docs/fuentes_datos.md
   ```

5. (Opcional) carga datos de ejemplo del SLGA para tres distritos, para ver el dashboard institucional poblado:

   ```bash
   python -m src.slga.cli seed-ejemplo
   ```

6. Abre Grafana en http://localhost:3000 (usuario/clave por defecto en `.env.example`) — datasource y los 3 dashboards ya están provisionados, cada uno con un filtro de distrito.

7. (Opcional, para producción) configura los secretos de `.github/workflows/ingesta.yml` en tu repo de GitHub (`DATABASE_URL` accesible desde internet, `OPENAQ_API_KEY`, `FIRMS_MAP_KEY`, etc.) para que la ingesta corra sola.

## Estado del proyecto

| Dominio | Fuente | Estado |
|---|---|---|
| Aire | OpenAQ API v3 | Funcional — bbox de los 43 distritos, requiere API key gratuita |
| Aire | SENAMHI | Import manual de CSV — no expone API REST pública; ver `src/ingest/senamhi_aire_csv.py` |
| Residuos | PNDA (CKAN) | Cliente funcional — **debes verificar el slug exacto del dataset** en el portal, no se pudo confirmar en vivo desde este entorno |
| Agua / ruido / áreas verdes | PNDA (CKAN genérico) | Cliente funcional (`ckan_generico.py`) — **plantilla sin datasets reales confirmados aún**, ver `config/fuentes_ckan.example.yml` |
| Incendios | NASA FIRMS | Funcional — API real, requiere MAP_KEY gratuita |
| Bosques / lomas costeras | Global Forest Watch | Estructura implementada, **no verificada en vivo** (dataset/auth exactos por confirmar) |
| Bosques (Amazonía) | Geobosques | No implementado — Lima no tiene bosque amazónico, ver `docs/fuentes_datos.md` |
| SLGA (institucional) | Carga manual vía `src/slga/cli.py`, por distrito | Funcional — instrumentos, CAM, PLANEFA, GALS; ver `docs/slga.md` |
| Actualización periódica | GitHub Actions (`.github/workflows/ingesta.yml`) | Configurado — requiere `DATABASE_URL` accesible desde internet |

## Roadmap sugerido

1. Verificar y completar los `package_id` reales en `config/fuentes_ckan.yml` (agua, ruido, áreas verdes) y `RESIDUOS_CKAN_PACKAGE_ID`.
2. Confirmar el dataset/autenticación exactos de la API de Global Forest Watch contra la documentación vigente.
3. Completar los códigos UBIGEO oficiales de los 43 distritos en la tabla `distritos` (ver `docs/distritos.md`).
4. Reemplazar la heurística de "distrito más cercano" por un join espacial contra polígonos oficiales de INEI/IGN.
5. Mejorar el modelo de predicción de PM2.5 (features horarias/estacionales, validación cruzada).
6. Vincular indicadores SLGA/GALS con los datos técnicos (ej. cobertura real de monitoreo de aire como insumo del indicador GALS de calidad ambiental) en vez de cargarlos por separado.
7. Sumar un panel de mapa (Grafana Geomap) para las alertas forestales y estaciones de aire.

## Licencia

MIT — ver [`LICENSE`](LICENSE).
