"""Import de calidad de aire desde un CSV descargado manualmente de SENAMHI.

SENAMHI (https://www.senamhi.gob.pe/site/descarga-datos/) opera la red de estaciones
de calidad de aire de Lima Metropolitana, pero no expone una API REST pública y
documentada para descarga automática. Este script asume que el usuario descargó
manualmente un CSV desde el portal y ajusta el mapeo de columnas según ese archivo.

Formato esperado (ajusta MAPEO_COLUMNAS si tu CSV usa otros nombres):
    estacion, lat, lon, fecha_hora, parametro, valor, unidad
"""
import csv
import sys
from datetime import datetime

from src.db import get_connection, upsert_estacion, upsert_medicion_aire
from src.distritos import cargar_distritos, distrito_mas_cercano

MAPEO_COLUMNAS = {
    "estacion": "estacion",
    "lat": "lat",
    "lon": "lon",
    "fecha_hora": "fecha_hora",
    "parametro": "parametro",
    "valor": "valor",
    "unidad": "unidad",
}


def ejecutar(ruta_csv: str) -> None:
    conn = get_connection()
    filas_procesadas = 0
    try:
        distritos = cargar_distritos(conn)
        with conn.cursor() as cur, open(ruta_csv, newline="", encoding="utf-8") as f:
            lector = csv.DictReader(f)
            for fila in lector:
                nombre_estacion = fila[MAPEO_COLUMNAS["estacion"]]
                lat = fila.get(MAPEO_COLUMNAS["lat"]) or None
                lon = fila.get(MAPEO_COLUMNAS["lon"]) or None
                distrito = distrito_mas_cercano(distritos, float(lat) if lat else None, float(lon) if lon else None)
                estacion_id = upsert_estacion(
                    cur,
                    fuente="senamhi",
                    id_externo=nombre_estacion,
                    nombre=nombre_estacion,
                    lat=lat,
                    lon=lon,
                    distrito_id=distrito["id"] if distrito else None,
                )

                medido_en = datetime.fromisoformat(fila[MAPEO_COLUMNAS["fecha_hora"]])
                upsert_medicion_aire(
                    cur,
                    estacion_id=estacion_id,
                    parametro=fila[MAPEO_COLUMNAS["parametro"]].lower(),
                    valor=float(fila[MAPEO_COLUMNAS["valor"]]),
                    unidad=fila[MAPEO_COLUMNAS["unidad"]],
                    medido_en=medido_en,
                    fuente="senamhi",
                )
                filas_procesadas += 1
        conn.commit()
    finally:
        conn.close()

    print(f"SENAMHI: {filas_procesadas} mediciones importadas desde {ruta_csv}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python -m src.ingest.senamhi_aire_csv <ruta_al_csv>")
        sys.exit(1)
    ejecutar(sys.argv[1])
