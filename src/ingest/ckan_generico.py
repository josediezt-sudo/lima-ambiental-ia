"""Ingesta genérica desde datasets CKAN (PNDA, https://www.datosabiertos.gob.pe/)
para dominios que en Perú se publican como indicadores periódicos por distrito en
vez de telemetría en tiempo real: agua, ruido, áreas verdes.

Cada fuente se declara en config/fuentes_ckan.yml (plantilla en
config/fuentes_ckan.example.yml) — package_id, dominio/indicador destino y mapeo de
columnas del CSV. NO se pudo verificar en vivo ningún package_id real desde este
entorno (bloqueo de red a datosabiertos.gob.pe): la plantilla trae "TODO" en vez de
slugs reales — complétalos contra el portal antes de usar esto en producción.
"""
import csv
import io
import os
import sys

import requests
import yaml

from src.db import get_connection
from src.distritos import cargar_distritos, resolver_distrito_por_nombre

RUTA_CONFIG_DEFECTO = "config/fuentes_ckan.yml"


def _cargar_config(ruta: str | None = None) -> list[dict]:
    ruta = ruta or os.environ.get("FUENTES_CKAN_CONFIG", RUTA_CONFIG_DEFECTO)
    if not os.path.exists(ruta):
        raise FileNotFoundError(
            f"No se encontró {ruta}. Copia config/fuentes_ckan.example.yml a "
            "config/fuentes_ckan.yml y completa los package_id reales."
        )
    with open(ruta, encoding="utf-8") as f:
        return yaml.safe_load(f) or []


def _obtener_recursos(base_url: str, package_id: str) -> list[dict]:
    resp = requests.get(f"{base_url}/api/3/action/package_show", params={"id": package_id}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"CKAN respondió sin éxito para '{package_id}': {data}")
    return data["result"]["resources"]


def _descargar_csv(url: str) -> list[dict]:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return list(csv.DictReader(io.StringIO(resp.text)))


def _procesar_fuente(cur, distritos: list[dict], fuente: dict) -> None:
    base_url = fuente.get("base_url", "https://www.datosabiertos.gob.pe")
    recursos = [r for r in _obtener_recursos(base_url, fuente["package_id"])
                if r.get("format", "").upper() == "CSV"]
    columnas = fuente["columnas"]
    procesadas = omitidas = 0

    for recurso in recursos:
        for fila in _descargar_csv(recurso["url"]):
            distrito = resolver_distrito_por_nombre(distritos, fila.get(columnas["distrito"], ""))
            if distrito is None:
                omitidas += 1
                continue
            try:
                cur.execute(
                    """
                    INSERT INTO indicadores_ambientales_distrito
                        (distrito_id, dominio, indicador, anio, valor, unidad, fuente, dataset_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (distrito_id, dominio, indicador, anio, fuente) DO UPDATE
                        SET valor = EXCLUDED.valor
                    """,
                    (
                        distrito["id"], fuente["dominio"], fuente["indicador"],
                        int(fila[columnas["anio"]]), float(fila[columnas["valor"]]),
                        fuente.get("unidad"), fuente["nombre"], recurso.get("id"),
                    ),
                )
                procesadas += 1
            except (KeyError, ValueError) as exc:
                print(f"[{fuente['nombre']}] fila omitida por columnas inesperadas: {exc}")
                omitidas += 1

    print(f"{fuente['nombre']}: {procesadas} filas importadas, {omitidas} omitidas")


def ejecutar(nombre_fuente: str | None = None) -> None:
    fuentes = _cargar_config()
    if nombre_fuente:
        fuentes = [f for f in fuentes if f["nombre"] == nombre_fuente]
        if not fuentes:
            raise ValueError(f"No hay ninguna fuente '{nombre_fuente}' en config/fuentes_ckan.yml")

    conn = get_connection()
    try:
        distritos = cargar_distritos(conn)
        with conn.cursor() as cur:
            for fuente in fuentes:
                _procesar_fuente(cur, distritos, fuente)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    ejecutar(sys.argv[1] if len(sys.argv) > 1 else None)
