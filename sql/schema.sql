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

-- Sistema Local de Gestión Ambiental (SLGA) — seguimiento institucional/normativo.
-- Ver docs/slga.md para el marco legal (Ley 28245, D.S. 008-2005-PCM, Ley 27972,
-- Guía SLGA RM 101-2021-MINAM) y el mapeo de cada tabla a su instrumento oficial.

CREATE TABLE IF NOT EXISTS instrumentos_gestion_ambiental (
    id                      SERIAL PRIMARY KEY,
    tipo                    TEXT NOT NULL CHECK (tipo IN (
                                'politica_ambiental_local',
                                'diagnostico_ambiental_local',
                                'plan_accion_ambiental_local',
                                'agenda_ambiental_local',
                                'pigars',
                                'planefa',
                                'ordenanza_ambiental',
                                'otro'
                            )),
    nombre                  TEXT NOT NULL,
    estado                  TEXT NOT NULL DEFAULT 'en_elaboracion' CHECK (estado IN (
                                'vigente', 'en_elaboracion', 'vencido', 'desactualizado'
                            )),
    norma_aprobacion        TEXT,           -- ej. "Ordenanza N° 123-2024-MDX"
    fecha_aprobacion        DATE,
    fecha_revision_prevista DATE,
    documento_url           TEXT,
    responsable             TEXT,
    notas                   TEXT,
    actualizado_en          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_instrumentos_estado
    ON instrumentos_gestion_ambiental (estado, fecha_revision_prevista);

CREATE TABLE IF NOT EXISTS cam_integrantes (
    id                  SERIAL PRIMARY KEY,
    institucion         TEXT NOT NULL,
    sector              TEXT NOT NULL CHECK (sector IN ('publico', 'privado', 'sociedad_civil')),
    representante       TEXT,
    cargo               TEXT,
    fecha_incorporacion DATE,
    vigente             BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS cam_sesiones (
    id          SERIAL PRIMARY KEY,
    fecha       DATE NOT NULL,
    tipo        TEXT NOT NULL CHECK (tipo IN ('ordinaria', 'extraordinaria')),
    asistentes  INTEGER,
    acuerdos    TEXT,
    acta_url    TEXT
);

CREATE INDEX IF NOT EXISTS idx_cam_sesiones_fecha ON cam_sesiones (fecha DESC);

CREATE TABLE IF NOT EXISTS planefa_acciones (
    id                      SERIAL PRIMARY KEY,
    anio                    INTEGER NOT NULL,
    unidad_fiscalizable     TEXT NOT NULL,
    tipo_accion             TEXT NOT NULL,   -- ej. 'supervision', 'monitoreo', 'evaluacion'
    trimestre_programado    INTEGER CHECK (trimestre_programado BETWEEN 1 AND 4),
    estado                  TEXT NOT NULL DEFAULT 'programada' CHECK (estado IN (
                                'programada', 'ejecutada', 'reprogramada', 'cancelada'
                            )),
    resultado               TEXT,
    notas                   TEXT
);

CREATE INDEX IF NOT EXISTS idx_planefa_anio ON planefa_acciones (anio, estado);

CREATE TABLE IF NOT EXISTS indicadores_gals (
    id              SERIAL PRIMARY KEY,
    dimension       TEXT NOT NULL CHECK (dimension IN (
                        'calidad_ambiental', 'institucionalidad_ciudadania', 'aprovechamiento_rrnn_cc'
                    )),
    indicador       TEXT NOT NULL,
    nivel_objetivo  TEXT NOT NULL CHECK (nivel_objetivo IN ('GALS I', 'GALS II')),
    avance_pct      DOUBLE PRECISION CHECK (avance_pct BETWEEN 0 AND 100),
    fecha_corte     DATE NOT NULL,
    notas           TEXT
);

CREATE INDEX IF NOT EXISTS idx_indicadores_gals_fecha ON indicadores_gals (fecha_corte DESC);
