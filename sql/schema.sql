-- Esquema: monitoreo ambiental y gestión (SLGA) de Lima Metropolitana y sus 43 distritos.
--
-- CAMBIO IMPORTANTE (v2): este esquema pasó de modelar UNA municipalidad genérica a
-- modelar explícitamente los 44 gobiernos locales de Lima Metropolitana (1 provincial +
-- 43 distritales) vía la tabla `distritos`. Es un cambio incompatible con la v1: si ya
-- tenías una base de datos con el esquema anterior, tienes que recrearla desde cero
-- (no hay migración automática — el proyecto todavía no tiene un sistema de migraciones,
-- ver docs/arquitectura.md).

CREATE EXTENSION IF NOT EXISTS postgis;

-- --- Distritos (los 44 gobiernos locales) ------------------------------------

CREATE TABLE IF NOT EXISTS distritos (
    id          SERIAL PRIMARY KEY,
    nombre      TEXT NOT NULL UNIQUE,
    nivel       TEXT NOT NULL CHECK (nivel IN ('provincial', 'distrital')),
    ubigeo      TEXT,               -- código INEI de 6 dígitos — NO poblado por defecto,
                                     -- ver docs/distritos.md: complétalo desde la fuente
                                     -- oficial (INEI) antes de usarlo para cruces de datos
    lat         DOUBLE PRECISION,   -- punto de referencia aproximado (municipio/centro),
    lon         DOUBLE PRECISION,   -- NO es un centroide censal oficial
    creado_en   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- --- Calidad del aire ----------------------------------------------------------

CREATE TABLE IF NOT EXISTS estaciones (
    id              SERIAL PRIMARY KEY,
    fuente          TEXT NOT NULL,          -- 'openaq', 'senamhi', ...
    id_externo      TEXT NOT NULL,          -- id de la estación en la fuente original
    nombre          TEXT NOT NULL,
    distrito_id     INTEGER REFERENCES distritos(id),  -- asignado por distrito más cercano
                                                         -- al punto (heurística, no polígono
                                                         -- real), ver src/distritos.py
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

-- --- Residuos sólidos (por distrito) --------------------------------------------

CREATE TABLE IF NOT EXISTS residuos_distrito (
    id                      BIGSERIAL PRIMARY KEY,
    distrito_id             INTEGER NOT NULL REFERENCES distritos(id),
    anio                    INTEGER NOT NULL,
    generacion_tn_dia       DOUBLE PRECISION,
    disposicion_final_pct   DOUBLE PRECISION,
    fuente                  TEXT NOT NULL,
    dataset_id              TEXT,
    cargado_en              TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (distrito_id, anio, fuente)
);

CREATE INDEX IF NOT EXISTS idx_residuos_distrito_anio
    ON residuos_distrito (distrito_id, anio);

-- --- Agua, ruido, áreas verdes y cobertura vegetal (indicadores periódicos) -----
--
-- Estos dominios en Perú se publican como datasets/reportes periódicos (anuales,
-- por distrito), no como telemetría en tiempo real — a diferencia del aire, donde
-- SENAMHI/OpenAQ sí exponen mediciones por hora. Por eso comparten una tabla
-- genérica en vez de una tabla de "mediciones" por dominio: modelan el mismo tipo
-- de dato (un indicador con nombre, valor y año, publicado por una fuente oficial).

CREATE TABLE IF NOT EXISTS indicadores_ambientales_distrito (
    id              BIGSERIAL PRIMARY KEY,
    distrito_id     INTEGER NOT NULL REFERENCES distritos(id),
    dominio         TEXT NOT NULL CHECK (dominio IN (
                        'agua', 'ruido', 'areas_verdes', 'cobertura_vegetal'
                    )),
    indicador       TEXT NOT NULL,          -- ej. 'cobertura_agua_potable_pct', 'nivel_ruido_leq_db'
    anio            INTEGER NOT NULL,
    valor           DOUBLE PRECISION NOT NULL,
    unidad          TEXT,
    fuente          TEXT NOT NULL,
    dataset_id      TEXT,
    cargado_en      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (distrito_id, dominio, indicador, anio, fuente)
);

CREATE INDEX IF NOT EXISTS idx_indicadores_ambientales_distrito
    ON indicadores_ambientales_distrito (distrito_id, dominio, anio DESC);

-- --- Bosques, lomas costeras e incendios (alertas puntuales) --------------------
--
-- Lima Metropolitana no tiene bosque amazónico (Geobosques no aplica en su forma
-- estándar), pero sí tiene lomas costeras (ecosistemas de neblina) en varios
-- distritos del sur/este, y sí es relevante monitorear incendios. Ver docs/slga.md
-- y docs/fuentes_datos.md para el detalle de cada fuente.

CREATE TABLE IF NOT EXISTS alertas_forestales (
    id              BIGSERIAL PRIMARY KEY,
    distrito_id     INTEGER REFERENCES distritos(id),  -- nullable: se asigna por
                                                         -- cercanía si cae dentro del
                                                         -- radio de algún distrito
    tipo            TEXT NOT NULL CHECK (tipo IN ('incendio', 'deforestacion', 'perdida_cobertura')),
    fuente          TEXT NOT NULL CHECK (fuente IN ('nasa_firms', 'global_forest_watch', 'geobosques')),
    lat             DOUBLE PRECISION NOT NULL,
    lon             DOUBLE PRECISION NOT NULL,
    detectado_en    TIMESTAMPTZ NOT NULL,
    confianza       TEXT,
    detalle         TEXT,
    cargado_en      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (fuente, lat, lon, detectado_en)
);

CREATE INDEX IF NOT EXISTS idx_alertas_forestales_fecha
    ON alertas_forestales (detectado_en DESC);

CREATE INDEX IF NOT EXISTS idx_alertas_forestales_distrito
    ON alertas_forestales (distrito_id, detectado_en DESC);

-- --- Sistema Local de Gestión Ambiental (SLGA) — por distrito -------------------
--
-- Lima Metropolitana tiene 44 gobiernos locales independientes (1 municipalidad
-- provincial + 43 distritales), cada uno con su propia Comisión Ambiental Municipal
-- (CAM) e instrumentos de gestión (Art. 25, Ley 28245). Por eso cada fila de estas
-- tablas pertenece a un distrito_id específico — incluida la fila 'Lima Metropolitana'
-- (nivel='provincial') de la tabla `distritos`, para los instrumentos y la CAM del
-- ámbito metropolitano. Ver docs/slga.md para el marco legal completo.

CREATE TABLE IF NOT EXISTS instrumentos_gestion_ambiental (
    id                      SERIAL PRIMARY KEY,
    distrito_id             INTEGER NOT NULL REFERENCES distritos(id),
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

CREATE INDEX IF NOT EXISTS idx_instrumentos_distrito_estado
    ON instrumentos_gestion_ambiental (distrito_id, estado, fecha_revision_prevista);

CREATE TABLE IF NOT EXISTS cam_integrantes (
    id                  SERIAL PRIMARY KEY,
    distrito_id         INTEGER NOT NULL REFERENCES distritos(id),
    institucion         TEXT NOT NULL,
    sector              TEXT NOT NULL CHECK (sector IN ('publico', 'privado', 'sociedad_civil')),
    representante       TEXT,
    cargo               TEXT,
    fecha_incorporacion DATE,
    vigente             BOOLEAN NOT NULL DEFAULT true
);

CREATE INDEX IF NOT EXISTS idx_cam_integrantes_distrito ON cam_integrantes (distrito_id, vigente);

CREATE TABLE IF NOT EXISTS cam_sesiones (
    id          SERIAL PRIMARY KEY,
    distrito_id INTEGER NOT NULL REFERENCES distritos(id),
    fecha       DATE NOT NULL,
    tipo        TEXT NOT NULL CHECK (tipo IN ('ordinaria', 'extraordinaria')),
    asistentes  INTEGER,
    acuerdos    TEXT,
    acta_url    TEXT
);

CREATE INDEX IF NOT EXISTS idx_cam_sesiones_distrito_fecha ON cam_sesiones (distrito_id, fecha DESC);

CREATE TABLE IF NOT EXISTS planefa_acciones (
    id                      SERIAL PRIMARY KEY,
    distrito_id             INTEGER NOT NULL REFERENCES distritos(id),
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

CREATE INDEX IF NOT EXISTS idx_planefa_distrito_anio ON planefa_acciones (distrito_id, anio, estado);

CREATE TABLE IF NOT EXISTS indicadores_gals (
    id              SERIAL PRIMARY KEY,
    distrito_id     INTEGER NOT NULL REFERENCES distritos(id),
    dimension       TEXT NOT NULL CHECK (dimension IN (
                        'calidad_ambiental', 'institucionalidad_ciudadania', 'aprovechamiento_rrnn_cc'
                    )),
    indicador       TEXT NOT NULL,
    nivel_objetivo  TEXT NOT NULL CHECK (nivel_objetivo IN ('GALS I', 'GALS II')),
    avance_pct      DOUBLE PRECISION CHECK (avance_pct BETWEEN 0 AND 100),
    fecha_corte     DATE NOT NULL,
    notas           TEXT
);

CREATE INDEX IF NOT EXISTS idx_indicadores_gals_distrito_fecha ON indicadores_gals (distrito_id, fecha_corte DESC);

-- --- Seed: los 44 gobiernos locales de Lima Metropolitana -----------------------
-- Nombres verificados; coordenadas aproximadas (referencia, no censales); ubigeo
-- sin completar (ver comentario en la definición de la tabla). Idempotente.

INSERT INTO distritos (nombre, nivel, lat, lon) VALUES
    ('Lima Metropolitana', 'provincial', -12.0464, -77.0428),
    ('Lima (Cercado)', 'distrital', -12.0464, -77.0428),
    ('Ancón', 'distrital', -11.7725, -77.1783),
    ('Ate', 'distrital', -12.0267, -76.9178),
    ('Barranco', 'distrital', -12.1494, -77.0208),
    ('Breña', 'distrital', -12.0586, -77.0486),
    ('Carabayllo', 'distrital', -11.8583, -77.0333),
    ('Chaclacayo', 'distrital', -11.9853, -76.7728),
    ('Chorrillos', 'distrital', -12.1747, -77.0181),
    ('Cieneguilla', 'distrital', -12.0847, -76.8347),
    ('Comas', 'distrital', -11.9333, -77.05),
    ('El Agustino', 'distrital', -12.0392, -77.0083),
    ('Independencia', 'distrital', -11.9911, -77.0508),
    ('Jesús María', 'distrital', -12.0797, -77.0489),
    ('La Molina', 'distrital', -12.0864, -76.9464),
    ('La Victoria', 'distrital', -12.0714, -77.0281),
    ('Lince', 'distrital', -12.0864, -77.035),
    ('Los Olivos', 'distrital', -11.9689, -77.0714),
    ('Lurigancho', 'distrital', -11.9333, -76.7),
    ('Lurín', 'distrital', -12.2739, -76.87),
    ('Magdalena del Mar', 'distrital', -12.0964, -77.0725),
    ('Miraflores', 'distrital', -12.1211, -77.0297),
    ('Pachacámac', 'distrital', -12.2064, -76.8419),
    ('Pucusana', 'distrital', -12.4808, -76.7961),
    ('Pueblo Libre', 'distrital', -12.0742, -77.0631),
    ('Puente Piedra', 'distrital', -11.8628, -77.0761),
    ('Punta Hermosa', 'distrital', -12.3325, -76.8264),
    ('Punta Negra', 'distrital', -12.3742, -76.7994),
    ('Rímac', 'distrital', -12.0289, -77.0392),
    ('San Bartolo', 'distrital', -12.39, -76.7742),
    ('San Borja', 'distrital', -12.1017, -77.0011),
    ('San Isidro', 'distrital', -12.0969, -77.0367),
    ('San Juan de Lurigancho', 'distrital', -11.9976, -77.0044),
    ('San Juan de Miraflores', 'distrital', -12.1592, -76.9689),
    ('San Luis', 'distrital', -12.0764, -77.0067),
    ('San Martín de Porres', 'distrital', -12.0158, -77.0783),
    ('San Miguel', 'distrital', -12.0775, -77.0864),
    ('Santa Anita', 'distrital', -12.0442, -76.9711),
    ('Santa María del Mar', 'distrital', -12.3606, -76.8064),
    ('Santa Rosa', 'distrital', -11.7975, -77.1653),
    ('Santiago de Surco', 'distrital', -12.1428, -76.9931),
    ('Surquillo', 'distrital', -12.1097, -77.0169),
    ('Villa El Salvador', 'distrital', -12.2114, -76.9364),
    ('Villa María del Triunfo', 'distrital', -12.1608, -76.9319)
ON CONFLICT (nombre) DO NOTHING;
