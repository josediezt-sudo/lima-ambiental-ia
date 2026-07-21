"""Cliente para la Global Forest Watch Data API
(https://data-api.globalforestwatch.org/), para alertas de pérdida de cobertura
vegetal en el bounding box de Lima Metropolitana — relevante sobre todo para las
lomas costeras del sur/este de la provincia (Lima no tiene bosque amazónico, así
que Geobosques no se implementó aquí; ver docs/fuentes_datos.md).

NO VERIFICADO EN VIVO: no se pudo confirmar desde este entorno (bloqueo de red)
el nombre/versión exactos del dataset ni el formato de autenticación vigente.
Antes de usar esto en producción:
  1. Revisa la documentación actual en https://data-api.globalforestwatch.org/
  2. Confirma el dataset de alertas (GLAD-L / RADD) y ajusta DATASET abajo.
  3. Consigue un API key en https://www.globalforestwatch.org/ y configúralo en
     GFW_API_KEY (.env).
Esta es la estructura esperada del cliente (autenticación, bbox, forma de la
respuesta), no una integración confirmada contra la API real.
"""
import os

import requests

from src.db import get_connection
from src.distritos import cargar_distritos, distrito_mas_cercano

BASE_URL = "https://data-api.globalforestwatch.org"
DATASET = "gfw_integrated_alerts"  # TODO: confirmar nombre/versión exactos contra la doc actual
PADDING_GRADOS = 0.05


def _headers() -> dict:
    return {"x-api-key": os.environ["GFW_API_KEY"]}


def _bbox_lima(distritos: list[dict]) -> tuple[float, float, float, float]:
    puntos = [d for d in distritos if d["nivel"] == "distrital" and d["lat"] is not None]
    lats = [d["lat"] for d in puntos]
    lons = [d["lon"] for d in puntos]
    return (
        min(lons) - PADDING_GRADOS, min(lats) - PADDING_GRADOS,
        max(lons) + PADDING_GRADOS, max(lats) + PADDING_GRADOS,
    )


def obtener_alertas(bbox: tuple[float, float, float, float]) -> list[dict]:
    min_lon, min_lat, max_lon, max_lat = bbox
    sql = (
        "SELECT latitude, longitude, alert_date, confidence "
        f"FROM {DATASET} "
        f"WHERE latitude BETWEEN {min_lat} AND {max_lat} "
        f"AND longitude BETWEEN {min_lon} AND {max_lon} "
        "ORDER BY alert_date DESC LIMIT 1000"
    )
    resp = requests.get(
        f"{BASE_URL}/dataset/{DATASET}/latest/query",
        headers=_headers(), params={"sql": sql}, timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


def ejecutar() -> None:
    conn = get_connection()
    try:
        distritos = cargar_distritos(conn)
        alertas = obtener_alertas(_bbox_lima(distritos))
        print(f"Global Forest Watch: {len(alertas)} alertas de pérdida de cobertura")

        insertadas = 0
        with conn.cursor() as cur:
            for alerta in alertas:
                lat, lon = alerta.get("latitude"), alerta.get("longitude")
                fecha = alerta.get("alert_date")
                if lat is None or lon is None or fecha is None:
                    continue

                distrito = distrito_mas_cercano(distritos, lat, lon)
                cur.execute(
                    """
                    INSERT INTO alertas_forestales
                        (distrito_id, tipo, fuente, lat, lon, detectado_en, confianza, detalle)
                    VALUES (%s, 'perdida_cobertura', 'global_forest_watch', %s, %s, %s, %s, NULL)
                    ON CONFLICT (fuente, lat, lon, detectado_en) DO NOTHING
                    """,
                    (distrito["id"] if distrito else None, lat, lon, fecha, str(alerta.get("confidence"))),
                )
                insertadas += 1
        conn.commit()
    finally:
        conn.close()

    print(f"Global Forest Watch: ingesta completada ({insertadas} alertas procesadas)")


if __name__ == "__main__":
    ejecutar()
