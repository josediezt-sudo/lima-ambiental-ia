"""Ingesta de focos de calor (incendios) desde NASA FIRMS
(https://firms.modaps.eosdis.nasa.gov/api/area/), acotada al bounding box de los
43 distritos de Lima Metropolitana.

Lima no tiene bosque amazónico, así que este dominio es más relevante para
incendios urbanos/periurbanos y en las lomas costeras (ecosistemas de neblina en
distritos del sur/este) que para deforestación en sentido estricto — por eso se
prioriza FIRMS (focos de calor reales) sobre Geobosques (pensado para el
monitoreo de bosques amazónicos, fuera del ámbito de esta provincia).

Requiere una MAP_KEY gratuita — regístrate en
https://firms.modaps.eosdis.nasa.gov/api/map_key/
"""
import csv
import io
import os
from datetime import datetime, timezone

import requests

from src.db import get_connection
from src.distritos import cargar_distritos, distrito_mas_cercano

BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
SATELITE = "VIIRS_SNPP_NRT"
RANGO_DIAS = 3
PADDING_GRADOS = 0.05


def _bbox_lima(distritos: list[dict]) -> str:
    puntos = [d for d in distritos if d["nivel"] == "distrital" and d["lat"] is not None]
    lats = [d["lat"] for d in puntos]
    lons = [d["lon"] for d in puntos]
    min_lon, max_lon = min(lons) - PADDING_GRADOS, max(lons) + PADDING_GRADOS
    min_lat, max_lat = min(lats) - PADDING_GRADOS, max(lats) + PADDING_GRADOS
    return f"{min_lon},{min_lat},{max_lon},{max_lat}"


def obtener_focos_calor(bbox: str) -> list[dict]:
    map_key = os.environ["FIRMS_MAP_KEY"]
    url = f"{BASE_URL}/{map_key}/{SATELITE}/{bbox}/{RANGO_DIAS}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return list(csv.DictReader(io.StringIO(resp.text)))


def ejecutar() -> None:
    conn = get_connection()
    try:
        distritos = cargar_distritos(conn)
        focos = obtener_focos_calor(_bbox_lima(distritos))
        print(f"NASA FIRMS: {len(focos)} focos de calor detectados en los últimos {RANGO_DIAS} días")

        insertados = 0
        with conn.cursor() as cur:
            for foco in focos:
                try:
                    lat, lon = float(foco["latitude"]), float(foco["longitude"])
                    fecha_hora = f"{foco['acq_date']} {foco['acq_time'][:2]}:{foco['acq_time'][2:]}"
                    detectado_en = datetime.strptime(fecha_hora, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                except (KeyError, ValueError) as exc:
                    print(f"Foco de calor omitido por formato inesperado: {exc}")
                    continue

                distrito = distrito_mas_cercano(distritos, lat, lon)
                cur.execute(
                    """
                    INSERT INTO alertas_forestales
                        (distrito_id, tipo, fuente, lat, lon, detectado_en, confianza, detalle)
                    VALUES (%s, 'incendio', 'nasa_firms', %s, %s, %s, %s, %s)
                    ON CONFLICT (fuente, lat, lon, detectado_en) DO NOTHING
                    """,
                    (
                        distrito["id"] if distrito else None,
                        lat, lon, detectado_en,
                        foco.get("confidence"),
                        f"satélite={foco.get('satellite')} frp={foco.get('frp')}",
                    ),
                )
                insertados += 1
        conn.commit()
    finally:
        conn.close()

    print(f"NASA FIRMS: ingesta completada ({insertados} focos procesados)")


if __name__ == "__main__":
    ejecutar()
