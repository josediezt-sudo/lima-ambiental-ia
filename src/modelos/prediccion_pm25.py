"""Modelo baseline de predicción de PM2.5.

Ajusta una regresión lineal sobre la tendencia reciente (últimas 72h) de cada
estación y proyecta el valor esperado a distintos horizontes. Es deliberadamente
simple: el objetivo del MVP es validar el pipeline de datos completo (ingesta ->
almacenamiento -> modelo -> visualización), no maximizar precisión predictiva.
"""
from datetime import timedelta

import pandas as pd
from sklearn.linear_model import LinearRegression

from src.db import get_connection

VENTANA_HORAS = 72
HORIZONTES_HORAS = [1, 3, 6, 12, 24]
MODELO_VERSION = "linreg_tendencia_v1"
MIN_PUNTOS = 10


def _mediciones_recientes(conn, estacion_id: int) -> pd.DataFrame:
    query = """
        SELECT medido_en, valor
        FROM mediciones_aire
        WHERE estacion_id = %s AND parametro = 'pm25'
          AND medido_en >= now() - interval '%s hours'
        ORDER BY medido_en
    """
    return pd.read_sql(query, conn, params=(estacion_id, VENTANA_HORAS))


def _estaciones_con_pm25(conn) -> list[int]:
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT estacion_id FROM mediciones_aire WHERE parametro = 'pm25'")
        return [fila[0] for fila in cur.fetchall()]


def ejecutar() -> None:
    conn = get_connection()
    predicciones_generadas = 0
    try:
        for estacion_id in _estaciones_con_pm25(conn):
            df = _mediciones_recientes(conn, estacion_id)
            if len(df) < MIN_PUNTOS:
                continue

            t0 = df["medido_en"].min()
            df["horas_desde_t0"] = (df["medido_en"] - t0).dt.total_seconds() / 3600

            modelo = LinearRegression()
            modelo.fit(df[["horas_desde_t0"]], df["valor"])

            ultima_hora = df["horas_desde_t0"].max()
            ultimo_timestamp = df["medido_en"].max()

            with conn.cursor() as cur:
                for horizonte in HORIZONTES_HORAS:
                    x_pred = [[ultima_hora + horizonte]]
                    valor_predicho = max(0.0, float(modelo.predict(x_pred)[0]))
                    timestamp_prediccion = ultimo_timestamp + timedelta(hours=horizonte)

                    cur.execute(
                        """
                        INSERT INTO predicciones_pm25
                            (estacion_id, horizonte_horas, timestamp_prediccion, valor_predicho, modelo_version)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (estacion_id, horizonte, timestamp_prediccion, valor_predicho, MODELO_VERSION),
                    )
                    predicciones_generadas += 1
        conn.commit()
    finally:
        conn.close()

    print(f"Predicción PM2.5: {predicciones_generadas} predicciones generadas")


if __name__ == "__main__":
    ejecutar()
