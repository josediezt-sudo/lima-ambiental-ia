"""Ingesta de calidad del aire desde la API v3 de OpenAQ (https://docs.openaq.org/).

Requiere una API key gratuita (OPENAQ_API_KEY) — regístrate en https://explore.openaq.org/register.
"""
import os

import requests

from src.db import get_connection, upsert_estacion, upsert_medicion_aire

BASE_URL = "https://api.openaq.org/v3"


def _headers() -> dict:
    api_key = os.environ["OPENAQ_API_KEY"]
    return {"X-API-Key": api_key}


def obtener_ubicaciones_lima() -> list[dict]:
    lat = os.environ.get("OPENAQ_LAT", "-12.0464")
    lon = os.environ.get("OPENAQ_LON", "-77.0428")
    radius = os.environ.get("OPENAQ_RADIUS_M", "30000")

    resp = requests.get(
        f"{BASE_URL}/locations",
        headers=_headers(),
        params={"coordinates": f"{lat},{lon}", "radius": radius, "limit": 100},
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
    ubicaciones = obtener_ubicaciones_lima()
    print(f"OpenAQ: {len(ubicaciones)} estaciones encontradas cerca de Lima")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for ubicacion in ubicaciones:
                coords = ubicacion.get("coordinates") or {}
                estacion_id = upsert_estacion(
                    cur,
                    fuente="openaq",
                    id_externo=str(ubicacion["id"]),
                    nombre=ubicacion.get("name", f"openaq-{ubicacion['id']}"),
                    lat=coords.get("latitude"),
                    lon=coords.get("longitude"),
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
