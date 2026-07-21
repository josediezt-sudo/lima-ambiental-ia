"""Ingesta de calidad del aire desde la API v3 de OpenAQ (https://docs.openaq.org/).

Requiere una API key gratuita (OPENAQ_API_KEY) — regístrate en https://explore.openaq.org/register.

Busca estaciones en el bounding box de los 43 distritos de Lima Metropolitana (no
solo un radio desde el centro) para no perder distritos periféricos, y asigna cada
estación al distrito más cercano (heurística, ver src/distritos.py).
"""
import os

import requests

from src.db import get_connection, upsert_estacion, upsert_medicion_aire
from src.distritos import cargar_distritos, distrito_mas_cercano

BASE_URL = "https://api.openaq.org/v3"
PADDING_GRADOS = 0.05  # ~5.5 km, para no perder estaciones justo en el borde


def _headers() -> dict:
    api_key = os.environ["OPENAQ_API_KEY"]
    return {"X-API-Key": api_key}


def _bbox_lima(distritos: list[dict]) -> str:
    puntos = [d for d in distritos if d["nivel"] == "distrital" and d["lat"] is not None]
    if not puntos:
        raise RuntimeError("No hay distritos cargados — corre sql/schema.sql antes de la ingesta.")
    lats = [d["lat"] for d in puntos]
    lons = [d["lon"] for d in puntos]
    min_lon, max_lon = min(lons) - PADDING_GRADOS, max(lons) + PADDING_GRADOS
    min_lat, max_lat = min(lats) - PADDING_GRADOS, max(lats) + PADDING_GRADOS
    return f"{min_lon},{min_lat},{max_lon},{max_lat}"


def obtener_ubicaciones_lima(distritos: list[dict]) -> list[dict]:
    resp = requests.get(
        f"{BASE_URL}/locations",
        headers=_headers(),
        params={"bbox": _bbox_lima(distritos), "limit": 1000},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def obtener_ultimas_mediciones(sensor_id: int, limit: int = 24) -> list[dict]:
    resp = requests.get(
        f"{BASE_URL}/sensors/{sensor_id}/measurements",
        headers=_headers(),
        params={"limit": limit, "sort": "desc"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def ejecutar() -> None:
    conn = get_connection()
    try:
        distritos = cargar_distritos(conn)
        ubicaciones = obtener_ubicaciones_lima(distritos)
        print(f"OpenAQ: {len(ubicaciones)} estaciones encontradas en Lima Metropolitana (43 distritos)")

        with conn.cursor() as cur:
            for ubicacion in ubicaciones:
                coords = ubicacion.get("coordinates") or {}
                lat, lon = coords.get("latitude"), coords.get("longitude")
                distrito = distrito_mas_cercano(distritos, lat, lon)

                estacion_id = upsert_estacion(
                    cur,
                    fuente="openaq",
                    id_externo=str(ubicacion["id"]),
                    nombre=ubicacion.get("name", f"openaq-{ubicacion['id']}"),
                    lat=lat,
                    lon=lon,
                    distrito_id=distrito["id"] if distrito else None,
                )

                for sensor in ubicacion.get("sensors", []):
                    parametro = sensor.get("parameter", {}).get("name")
                    unidad = sensor.get("parameter", {}).get("units")
                    if not parametro:
                        continue

                    for medicion in obtener_ultimas_mediciones(sensor["id"]):
                        periodo = medicion.get("period", {}).get("datetimeTo", {})
                        medido_en = periodo.get("utc")
                        valor = medicion.get("value")
                        if medido_en is None or valor is None:
                            continue

                        upsert_medicion_aire(
                            cur,
                            estacion_id=estacion_id,
                            parametro=parametro,
                            valor=valor,
                            unidad=unidad or "",
                            medido_en=medido_en,
                            fuente="openaq",
                        )
        conn.commit()
    finally:
        conn.close()

    print("OpenAQ: ingesta completada")


if __name__ == "__main__":
    ejecutar()
