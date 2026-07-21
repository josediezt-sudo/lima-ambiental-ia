# Los 44 gobiernos locales de Lima Metropolitana

Lima Metropolitana está conformada por la **Municipalidad Metropolitana de Lima**
(provincial) y **43 municipalidades distritales**. Cada una es un gobierno local
independiente, con su propia Comisión Ambiental Municipal (CAM) e instrumentos de
gestión ambiental (ver [`docs/slga.md`](slga.md)). Por eso todo el proyecto —
técnico e institucional — está organizado alrededor de la tabla `distritos`
(44 filas: 1 `nivel='provincial'` + 43 `nivel='distrital'`), sembrada
automáticamente al aplicar `sql/schema.sql`.

## Qué hay en cada fila

| Columna | Contenido |
|---|---|
| `nombre` | Nombre oficial del distrito (o "Lima Metropolitana" para la fila provincial) |
| `nivel` | `'provincial'` o `'distrital'` |
| `lat`, `lon` | Punto de referencia aproximado (ej. el municipio) — **no es un centroide censal oficial**, es solo suficiente para la heurística de "distrito más cercano" |
| `ubigeo` | Código INEI de 6 dígitos — **queda sin poblar a propósito.** No se pudo verificar en vivo desde este entorno de desarrollo (bloqueo de red hacia los portales de INEI/gob.pe) el código exacto de cada uno de los 43 distritos, y prefiero dejarlo vacío a arriesgarme a insertar códigos "oficiales" incorrectos. Complétalo desde la fuente oficial de INEI antes de depender de él para cruces con otros datasets. |

## Cómo se asigna un distrito a un dato

- **Instrumentos SLGA, CAM, PLANEFA, indicadores GALS**: se asignan explícitamente
  al cargar el dato (`--distrito "San Isidro"` en la CLI, o el campo `distrito:`
  en los YAML de ejemplo/seed). No hay ambigüedad — es una decisión administrativa
  de qué gobierno local es dueño de ese instrumento.
- **Residuos sólidos, agua, ruido, áreas verdes**: se resuelven por **nombre**
  contra la columna `nombre` de `distritos` (`src/distritos.py:resolver_distrito_por_nombre`),
  tolerante a acentos/mayúsculas y con una pequeña lista de alias para variantes
  comunes ("Lima" → "Lima (Cercado)", etc.). Si el dataset de origen usa un nombre
  que no reconoce, la fila se omite con un aviso en vez de fallar todo el import —
  revisa `ALIAS_NOMBRE` en `src/distritos.py` si ves distritos reales omitidos.
- **Estaciones de aire (OpenAQ/SENAMHI) y alertas forestales (FIRMS/GFW)**: se
  asignan por **coordenada**, con el distrito más cercano
  (`distrito_mas_cercano`, distancia Haversine al punto de referencia de cada
  distrito). Es una heurística de vecino más cercano, **no una contención
  geométrica real contra polígonos oficiales** — una estación muy cerca de un
  límite distrital puede quedar asignada al distrito vecino. Para uso
  institucional serio, reemplázala por un join espacial contra los polígonos
  oficiales de INEI/IGN (requeriría cargar esos polígonos, que este proyecto no
  incluye).

## Por qué no hay 43 estaciones de aire

La red real de monitoreo de aire en Lima (SENAMHI + lo que agrega OpenAQ) tiene
muchas menos estaciones que distritos — es normal y esperado ver distritos con 0
estaciones asignadas. El panel "Cobertura de monitoreo por distrito" del
dashboard de aire existe justamente para mostrar ese vacío con transparencia, no
para ocultarlo.
