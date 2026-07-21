"""Resolución de distritos: distrito más cercano a una coordenada y resolución de
nombre de distrito (tolerante a acentos/mayúsculas) contra la tabla `distritos`.

No hay polígonos reales de distrito en este proyecto — la asignación por
coordenada es una heurística de "distrito más cercano" (basada en el punto de
referencia aproximado de cada distrito), no una contención geométrica real.
Para uso institucional serio, reemplázala por un join espacial contra los
polígonos oficiales de INEI/IGN.
"""
import math
import unicodedata

ALIAS_NOMBRE = {
    # las claves y los valores deben estar ya normalizados (sin tildes, minúsculas)
    # porque se comparan contra nombres de distrito ya pasados por _normalizar().
    "lima": "lima (cercado)",
    "cercado de lima": "lima (cercado)",
    "lima cercado": "lima (cercado)",
    "magdalena": "magdalena del mar",
    "san martin de porras": "san martin de porres",
}


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return texto.strip().lower()


def _distancia_km(lat1, lon1, lat2, lon2) -> float:
    radio_tierra_km = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radio_tierra_km * math.asin(math.sqrt(a))


def cargar_distritos(conn) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute("SELECT id, nombre, nivel, lat, lon FROM distritos")
        columnas = [d[0] for d in cur.description]
        return [dict(zip(columnas, fila)) for fila in cur.fetchall()]


def distrito_mas_cercano(distritos: list[dict], lat, lon) -> dict | None:
    """Heurística de vecino más cercano entre los 43 distritos (nivel='distrital')."""
    if lat is None or lon is None:
        return None
    candidatos = [d for d in distritos if d["nivel"] == "distrital" and d["lat"] is not None]
    if not candidatos:
        return None
    return min(candidatos, key=lambda d: _distancia_km(lat, lon, d["lat"], d["lon"]))


def resolver_distrito_por_nombre(distritos: list[dict], nombre: str) -> dict | None:
    objetivo = _normalizar(nombre)
    objetivo = ALIAS_NOMBRE.get(objetivo, objetivo)
    for d in distritos:
        if _normalizar(d["nombre"]) == objetivo:
            return d
    return None


def distrito_provincial(distritos: list[dict]) -> dict:
    for d in distritos:
        if d["nivel"] == "provincial":
            return d
    raise RuntimeError(
        "No se encontró el distrito provincial 'Lima Metropolitana' en la tabla "
        "`distritos` — ¿corriste sql/schema.sql (incluye el seed de los 44 gobiernos "
        "locales) contra esta base de datos?"
    )
