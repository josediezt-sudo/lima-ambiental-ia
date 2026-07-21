import os

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    database_url = os.environ["DATABASE_URL"]
    return psycopg2.connect(database_url)


def upsert_estacion(cur, fuente: str, id_externo: str, nombre: str, lat, lon, distrito_id=None) -> int:
    cur.execute(
        """
        INSERT INTO estaciones (fuente, id_externo, nombre, distrito_id, lat, lon)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (fuente, id_externo) DO UPDATE
            SET nombre = EXCLUDED.nombre, lat = EXCLUDED.lat, lon = EXCLUDED.lon,
                distrito_id = COALESCE(EXCLUDED.distrito_id, estaciones.distrito_id)
        RETURNING id
        """,
        (fuente, id_externo, nombre, distrito_id, lat, lon),
    )
    return cur.fetchone()[0]


def upsert_medicion_aire(cur, estacion_id: int, parametro: str, valor: float, unidad: str, medido_en, fuente: str):
    cur.execute(
        """
        INSERT INTO mediciones_aire (estacion_id, parametro, valor, unidad, medido_en, fuente)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (estacion_id, parametro, medido_en) DO NOTHING
        """,
        (estacion_id, parametro, valor, unidad, medido_en, fuente),
    )
