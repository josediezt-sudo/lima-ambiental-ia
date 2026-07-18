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

## Bosques, deforestación e incendios (fase 2, no implementado aún)

- **Geobosques (MINAM/PNCBMCC)** — https://geobosques.minam.gob.pe/
  Monitoreo satelital de cobertura forestal con alertas tempranas (cada 21–26 días) y servicios API/WMS públicos.
- **Global Forest Watch** — Data API: https://data-api.globalforestwatch.org/ · portal: https://data.globalforestwatch.org/
  Alertas GLAD (30m, semanal) y RADD (10m, casi tiempo real) de pérdida de cobertura arbórea. API REST/GeoJSON, stack open source en GitHub.
- **NASA FIRMS** — https://firms.modaps.eosdis.nasa.gov/api/area/
  Focos de calor/incendios activos (MODIS/VIIRS) en casi tiempo real (≤3h), con API de área y alertas por correo.

## Imágenes satelitales (insumo para modelos futuros)

- **Copernicus Data Space Ecosystem (Sentinel Hub)** — https://dataspace.copernicus.eu/
- **Sentinelsat** (librería Python) — https://github.com/sentinelsat/sentinelsat
- **awesome-sentinel** (catálogo de herramientas) — https://github.com/kr-stn/awesome-sentinel

## Otros datos abiertos peruanos relevantes

- **MEF — Datos Abiertos** — https://datosabiertos.mef.gob.pe/ (para cruzar inversión pública con proyectos ambientales municipales, si se necesita en fases posteriores).
