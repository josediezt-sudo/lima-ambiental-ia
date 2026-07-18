"""Ingesta de residuos sólidos por distrito desde la Plataforma Nacional de Datos
Abiertos (PNDA, https://www.datosabiertos.gob.pe/), que -como la mayoría de portales
gob.pe de datos abiertos- corre sobre CKAN (https://docs.ckan.org/en/latest/api/).

IMPORTANTE: no fue posible verificar en vivo el slug exacto del dataset de residuos
desde este entorno de desarrollo (bloqueo de red al portal). Antes de usar este
script en producción:
  1. Busca el dataset de "generación de residuos sólidos municipales" en
     https://www.datosabiertos.gob.pe/ y copia su slug (la parte final de la URL).
  2. Configúralo en RESIDUOS_CKAN_PACKAGE_ID (.env).
  3. Revisa que las columnas del recurso CSV coincidan con MAPEO_COLUMNAS de abajo
     y ajústalas si es necesario.
"""
import io
import os

import requests

from src.db import get_connection

MAPEO_COLUMNAS = {
    "distrito": "distrito",
    "anio": "anio",
    "generacion_tn_dia": "generacion_tn_dia",
    "disposicion_final_pct": "disposicion_final_pct",
}


def obtener_recursos_dataset() -> list[dict]:
    base_url = os.environ["RESIDUOS_CKAN_BASE_URL"]
    package_id = os.environ["RESIDUOS_CKAN_PACKAGE_ID"]
    if not package_id:
        raise RuntimeError(
            "RESIDUOS_CKAN_PACKAGE_ID no está configurado. "
            "Busca el dataset en el portal de datos abiertos y configura su slug en .env"
        )

    resp = requests.get(f"{base_url}/api/3/action/package_show", params={"id": package_id}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"CKAN respondió sin éxito: {data}")
    return data["result"]["resources"]


def _descargar_csv(url: str) -> list[dict]:
    import csv

    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return list(csv.DictReader(io.StringIO(resp.text)))


def ejecutar() -> None:
    recursos_csv = [r for r in obtener_recursos_dataset() if r.get("format", "").upper() == "CSV"]
    if not recursos_csv:
        print("No se encontraron recursos CSV en el dataset configurado.")
        return

    conn = get_connection()
    filas_procesadas = 0
    try:
        with conn.cursor() as cur:
            for recurso in recursos_csv:
                filas = _descargar_csv(recurso["url"])
                for fila in filas:
                    try:
                        cur.execute(
                            """
                            INSERT INTO residuos_distrito
                                (distrito, anio, generacion_tn_dia, disposicion_final_pct, fuente, dataset_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (distrito, anio, fuente) DO UPDATE
                                SET generacion_tn_dia = EXCLUDED.generacion_tn_dia,
                                    disposicion_final_pct = EXCLUDED.disposicion_final_pct
                            """,
                            (
                                fila[MAPEO_COLUMNAS["distrito"]],
                                int(fila[MAPEO_COLUMNAS["anio"]]),
                                float(fila[MAPEO_COLUMNAS["generacion_tn_dia"]] or 0) or None,
                                float(fila[MAPEO_COLUMNAS["disposicion_final_pct"]] or 0) or None,
                                "pnda",
                                recurso.get("id"),
                            ),
                        )
                        filas_procesadas += 1
                    except (KeyError, ValueError) as exc:
                        print(f"Fila omitida por columnas inesperadas: {exc}")
        conn.commit()
    finally:
        conn.close()

    print(f"Residuos (PNDA): {filas_procesadas} filas importadas")


if __name__ == "__main__":
    ejecutar()
