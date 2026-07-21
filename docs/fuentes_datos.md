# Fuentes de datos ambientales abiertas

Investigación de referencia para el proyecto, con notas honestas sobre disponibilidad real de API (no todo lo que se llama "datos abiertos" tiene una API lista para consumir en tiempo real).

## Calidad del aire

- **OpenAQ** — https://openaq.org/ · API docs: https://docs.openaq.org/ · código: https://github.com/openaq
  Plataforma global open source (datos y software). API REST v3 estable, requiere API key gratuita. Agrega estaciones de Lima entre otras ciudades. **Fuente principal usada en este MVP.**
- **SENAMHI — Descarga de datos** — https://www.senamhi.gob.pe/site/descarga-datos/
  Opera la red de estaciones automáticas de calidad de aire de Lima Metropolitana, pero no publica una API REST pública y documentada para consumo automático — el acceso es vía descarga manual desde su portal. `src/ingest/senamhi_aire_csv.py` asume un CSV descargado manualmente.
- **SINIA — Portal de Datos Abiertos (MINAM)** — https://sinia.minam.gob.pe/portal/datos-abiertos/
  Repositorio ambiental central del Perú (aire, agua, suelo, biodiversidad); republica parte de los datos SENAMHI.

## Residuos sólidos

- **Plataforma Nacional de Datos Abiertos (PNDA)** — https://www.datosabiertos.gob.pe/
  Incluye datasets de generación de residuos sólidos municipales y disposición final por distrito, publicados por MINAM. Portales `gob.pe` de datos abiertos suelen correr sobre **CKAN**, por lo que `src/ingest/residuos_ckan.py` implementa un cliente CKAN genérico (`package_search` / `package_show`) — **no se pudo verificar en vivo el slug exacto del dataset desde este entorno (bloqueo de red al portal), así que hay que confirmarlo manualmente en el sitio y configurarlo en `.env`.**
- **OEFA — Datos Abiertos** — https://datosabiertos.oefa.gob.pe/home
  Fiscalización ambiental, sanciones, denuncias — útil para cruzar cumplimiento normativo con zonas de mayor generación de residuos.

## Agua

- **SUNASS — Datos Abiertos (PNDA)** — https://datosabiertos.gob.pe/group/servicio-de-agua-potable-y-alcantarillado-de-lima
  El organismo regulador de saneamiento publica indicadores de las EPS (empresas prestadoras) en la PNDA, incluida SEDAPAL (Lima Metropolitana) — ej. conexiones activas de agua potable. `src/ingest/ckan_generico.py` puede apuntar a estos datasets configurando `config/fuentes_ckan.yml`.
- **ANA (Autoridad Nacional del Agua) — Red Nacional de Monitoreo de la Calidad de los Cuerpos de Agua**
  Monitorea calidad de ríos/cuerpos de agua a nivel nacional; no se confirmó en vivo desde este entorno un endpoint API específico — verificar en su portal antes de configurar una fuente.
- **SEDAPAL** no tiene una API pública documentada conocida — el acceso es vía los datasets que publica en la PNDA (arriba).

## Ruido ambiental

- **MINAM — Protocolo Nacional de Monitoreo de Ruido Ambiental (RM N° 227-2013-MINAM)**
  Define la metodología oficial de monitoreo; no es en sí una fuente de datos continua, sino el marco que sigue OEFA y las municipalidades al hacer campañas puntuales de monitoreo (no telemetría permanente).
- **OEFA** realiza campañas de monitoreo de ruido en Lima-Callao y publica los resultados como reportes — buscar en su portal de datos abiertos (`datosabiertos.oefa.gob.pe`) o en SINIA.

## Áreas verdes

- No se identificó un dataset único y confirmado de "m² de área verde por habitante" por distrito con API — este indicador suele aparecer en anuarios estadísticos (INEI — Anuario de Estadísticas Ambientales) o en reportes/ordenanzas municipales individuales. `indicadores_ambientales_distrito` está listo para recibirlo en cuanto se identifique una fuente concreta y estable.

## Bosques, lomas costeras e incendios

Lima Metropolitana **no tiene bosque amazónico** — Geobosques (pensado para monitorear la Amazonía) no aplica en su forma estándar a esta provincia. Lo relevante para Lima son los **incendios** (urbanos/periurbanos) y la **pérdida de cobertura vegetal en las lomas costeras** (ecosistemas de neblina en distritos del sur/este como Pachacámac, Villa María del Triunfo, Lurín, Punta Hermosa). Por eso el proyecto prioriza estas dos fuentes:

- **NASA FIRMS** — https://firms.modaps.eosdis.nasa.gov/api/area/
  Focos de calor/incendios activos (MODIS/VIIRS) en casi tiempo real (≤3h), con API de área (requiere MAP_KEY gratuita). **Implementado en `src/ingest/nasa_firms.py`, API real y estable.**
- **Global Forest Watch** — Data API: https://data-api.globalforestwatch.org/ · portal: https://data.globalforestwatch.org/
  Alertas GLAD (30m, semanal) y RADD (10m, casi tiempo real) de pérdida de cobertura vegetal — no exclusivo de bosque amazónico, cubre cualquier cobertura arbórea/arbustiva detectable por satélite, incluidas lomas costeras. **Estructura implementada en `src/ingest/global_forest_watch.py`, pero no se pudo verificar en vivo el nombre/versión exacto del dataset ni el formato de autenticación vigente desde este entorno — confirmar contra la documentación actual antes de producción.**
- **Geobosques (MINAM/PNCBMCC)** — https://geobosques.minam.gob.pe/
  Monitoreo satelital de cobertura forestal amazónica con alertas tempranas y servicios API/WMS. No implementado aquí por el desajuste geográfico explicado arriba — relevante solo si el proyecto se adapta a una región con cobertura amazónica.

## Imágenes satelitales (insumo para modelos futuros)

- **Copernicus Data Space Ecosystem (Sentinel Hub)** — https://dataspace.copernicus.eu/
- **Sentinelsat** (librería Python) — https://github.com/sentinelsat/sentinelsat
- **awesome-sentinel** (catálogo de herramientas) — https://github.com/kr-stn/awesome-sentinel

## Marco normativo de gestión ambiental municipal (SLGA)

No son "fuentes de datos" en el sentido de API, sino el marco legal que define qué
debe existir y trackearse a nivel institucional en cada municipalidad. Ver el
detalle completo y su mapeo al modelo de datos en [`docs/slga.md`](slga.md).

- **Ley N° 28245** — Ley Marco del Sistema Nacional de Gestión Ambiental.
- **RM N° 101-2021-MINAM** — Guía para el funcionamiento de los Sistemas Locales de Gestión Ambiental (SLGA).
- **Sistema de Información Ambiental Local (SIAL)** — https://sial.minam.gob.pe/ (portales oficiales por provincia; parte del SINIA).
- **Reconocimiento GALS** — https://www.minam.gob.pe/gals/

## Otros datos abiertos peruanos relevantes

- **MEF — Datos Abiertos** — https://datosabiertos.mef.gob.pe/ (para cruzar inversión pública con proyectos ambientales municipales, si se necesita en fases posteriores).
