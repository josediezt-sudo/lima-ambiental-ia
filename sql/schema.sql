-- Esquema inicial: calidad del aire + residuos sólidos (Lima Metropolitana)

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS estaciones (
    id              SERIAL PRIMARY KEY,
    fuente          TEXT NOT NULL,          -- 'openaq', 'senamhi', ...
    id_externo      TEXT NOT NULL,          -- id de la estación en la fuente original
    nombre          TEXT NOT NULL,
    distrito        TEXT,
    lat             DOUBLE PRECISION,
    lon             DOUBLE PRECISION,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (fuente, id_externo)
);

CREATE TABLE IF NOT EXISTS mediciones_aire (
    id              BIGSERIAL PRIMARY KEY,
    estacion_id     INTEGER NOT NULL REFERENCES estaciones(id),
    parametro       TEXT NOT NULL,          -- 'pm25', 'pm10', 'no2', 'o3', 'co', 'so2'
    valor           DOUBLE PRECISION NOT NULL,
    unidad          TEXT NOT NULL,
    medido_en       TIMESTAMPTZ NOT NULL,
    fuente          TEXT NOT NULL,
    cargado_en      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (estacion_id, parametro, medido_en)
);

CREATE INDEX IF NOT EXISTS idx_mediciones_aire_estacion_tiempo
    ON mediciones_aire (estacion_id, medido_en DESC);

CREATE INDEX IF NOT EXISTS idx_mediciones_aire_parametro_tiempo
    ON mediciones_aire (parametro, medido_en DESC);

CREATE TABLE IF NOT EXISTS predicciones_pm25 (
    id                  BIGSERIAL PRIMARY KEY,
    estacion_id         INTEGER NOT NULL REFERENCES estaciones(id),
    generado_en         TIMESTAMPTZ NOT NULL DEFAULT now(),
    horizonte_horas     INTEGER NOT NULL,
    timestamp_prediccion TIMESTAMPTZ NOT NULL,
    valor_predicho      DOUBLE PRECISION NOT NULL,
    modelo_version      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_predicciones_estacion_tiempo
    ON predicciones_pm25 (estacion_id, timestamp_prediccion DESC);

CREATE TABLE IF NOT EXISTS residuos_distrito (
    id                      BIGSERIAL PRIMARY KEY,
    distrito                TEXT NOT NULL,
    anio                    INTEGER NOT NULL,
    generacion_tn_dia       DOUBLE PRECISION,
    disposicion_final_pct   DOUBLE PRECISION,
    fuente                  TEXT NOT NULL,
    dataset_id              TEXT,
    cargado_en              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (distrito, anio, fuente)
);

CREATE INDEX IF NOT EXISTS idx_residuos_distrito_anio
    ON residuos_distrito (distrito, anio);
