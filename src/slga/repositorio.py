"""Operaciones de base de datos para el seguimiento del Sistema Local de Gestión
Ambiental (SLGA): instrumentos de gestión, integrantes y sesiones de la CAM,
acciones PLANEFA e indicadores GALS. Ver docs/slga.md para el marco legal.
"""
import psycopg2.extras

TIPOS_INSTRUMENTO = (
    "politica_ambiental_local",
    "diagnostico_ambiental_local",
    "plan_accion_ambiental_local",
    "agenda_ambiental_local",
    "pigars",
    "planefa",
    "ordenanza_ambiental",
    "otro",
)
ESTADOS_INSTRUMENTO = ("vigente", "en_elaboracion", "vencido", "desactualizado")
SECTORES_CAM = ("publico", "privado", "sociedad_civil")
TIPOS_SESION = ("ordinaria", "extraordinaria")
ESTADOS_PLANEFA = ("programada", "ejecutada", "reprogramada", "cancelada")
DIMENSIONES_GALS = ("calidad_ambiental", "institucionalidad_ciudadania", "aprovechamiento_rrnn_cc")
NIVELES_GALS = ("GALS I", "GALS II")


def _dict_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# --- Instrumentos de gestión ambiental ---------------------------------------

def insertar_instrumento(conn, *, tipo, nombre, estado="en_elaboracion", norma_aprobacion=None,
                          fecha_aprobacion=None, fecha_revision_prevista=None, documento_url=None,
                          responsable=None, notas=None) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO instrumentos_gestion_ambiental
                (tipo, nombre, estado, norma_aprobacion, fecha_aprobacion,
                 fecha_revision_prevista, documento_url, responsable, notas)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (tipo, nombre, estado, norma_aprobacion, fecha_aprobacion,
             fecha_revision_prevista, documento_url, responsable, notas),
        )
        instrumento_id = cur.fetchone()[0]
    conn.commit()
    return instrumento_id


def listar_instrumentos(conn, estado=None) -> list[dict]:
    with _dict_cursor(conn) as cur:
        if estado:
            cur.execute(
                "SELECT * FROM instrumentos_gestion_ambiental WHERE estado = %s "
                "ORDER BY fecha_revision_prevista NULLS LAST",
                (estado,),
            )
        else:
            cur.execute(
                "SELECT * FROM instrumentos_gestion_ambiental "
                "ORDER BY fecha_revision_prevista NULLS LAST"
            )
        return [dict(fila) for fila in cur.fetchall()]


# --- Comisión Ambiental Municipal (CAM) --------------------------------------

def insertar_cam_integrante(conn, *, institucion, sector, representante=None, cargo=None,
                             fecha_incorporacion=None, vigente=True) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO cam_integrantes (institucion, sector, representante, cargo, fecha_incorporacion, vigente)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (institucion, sector, representante, cargo, fecha_incorporacion, vigente),
        )
        integrante_id = cur.fetchone()[0]
    conn.commit()
    return integrante_id


def listar_cam_integrantes(conn, solo_vigentes=True) -> list[dict]:
    with _dict_cursor(conn) as cur:
        if solo_vigentes:
            cur.execute("SELECT * FROM cam_integrantes WHERE vigente = true ORDER BY institucion")
        else:
            cur.execute("SELECT * FROM cam_integrantes ORDER BY institucion")
        return [dict(fila) for fila in cur.fetchall()]


def insertar_cam_sesion(conn, *, fecha, tipo, asistentes=None, acuerdos=None, acta_url=None) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO cam_sesiones (fecha, tipo, asistentes, acuerdos, acta_url)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (fecha, tipo, asistentes, acuerdos, acta_url),
        )
        sesion_id = cur.fetchone()[0]
    conn.commit()
    return sesion_id


def listar_cam_sesiones(conn, anio=None) -> list[dict]:
    with _dict_cursor(conn) as cur:
        if anio:
            cur.execute(
                "SELECT * FROM cam_sesiones WHERE date_part('year', fecha) = %s ORDER BY fecha DESC",
                (anio,),
            )
        else:
            cur.execute("SELECT * FROM cam_sesiones ORDER BY fecha DESC")
        return [dict(fila) for fila in cur.fetchall()]


# --- PLANEFA -------------------------------------------------------------------

def insertar_planefa_accion(conn, *, anio, unidad_fiscalizable, tipo_accion,
                             trimestre_programado=None, estado="programada",
                             resultado=None, notas=None) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO planefa_acciones
                (anio, unidad_fiscalizable, tipo_accion, trimestre_programado, estado, resultado, notas)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (anio, unidad_fiscalizable, tipo_accion, trimestre_programado, estado, resultado, notas),
        )
        accion_id = cur.fetchone()[0]
    conn.commit()
    return accion_id


def listar_planefa_acciones(conn, anio=None) -> list[dict]:
    with _dict_cursor(conn) as cur:
        if anio:
            cur.execute(
                "SELECT * FROM planefa_acciones WHERE anio = %s ORDER BY trimestre_programado",
                (anio,),
            )
        else:
            cur.execute("SELECT * FROM planefa_acciones ORDER BY anio DESC, trimestre_programado")
        return [dict(fila) for fila in cur.fetchall()]


# --- Indicadores GALS ------------------------------------------------------------

def insertar_indicador_gals(conn, *, dimension, indicador, nivel_objetivo, avance_pct,
                             fecha_corte, notas=None) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO indicadores_gals (dimension, indicador, nivel_objetivo, avance_pct, fecha_corte, notas)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (dimension, indicador, nivel_objetivo, avance_pct, fecha_corte, notas),
        )
        indicador_id = cur.fetchone()[0]
    conn.commit()
    return indicador_id


def listar_indicadores_gals(conn, dimension=None) -> list[dict]:
    with _dict_cursor(conn) as cur:
        if dimension:
            cur.execute(
                "SELECT * FROM indicadores_gals WHERE dimension = %s ORDER BY fecha_corte DESC",
                (dimension,),
            )
        else:
            cur.execute("SELECT * FROM indicadores_gals ORDER BY fecha_corte DESC")
        return [dict(fila) for fila in cur.fetchall()]
