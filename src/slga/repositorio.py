"""Operaciones de base de datos para el seguimiento del Sistema Local de Gestión
Ambiental (SLGA): instrumentos de gestión, integrantes y sesiones de la CAM,
acciones PLANEFA e indicadores GALS — todo por distrito (los 44 gobiernos locales
de Lima Metropolitana). Ver docs/slga.md para el marco legal.
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

_SELECT_CON_DISTRITO = "SELECT t.*, d.nombre AS distrito_nombre FROM {tabla} t JOIN distritos d ON d.id = t.distrito_id"


def _dict_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# --- Instrumentos de gestión ambiental ---------------------------------------

def insertar_instrumento(conn, *, distrito_id, tipo, nombre, estado="en_elaboracion", norma_aprobacion=None,
                          fecha_aprobacion=None, fecha_revision_prevista=None, documento_url=None,
                          responsable=None, notas=None) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO instrumentos_gestion_ambiental
                (distrito_id, tipo, nombre, estado, norma_aprobacion, fecha_aprobacion,
                 fecha_revision_prevista, documento_url, responsable, notas)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (distrito_id, tipo, nombre, estado, norma_aprobacion, fecha_aprobacion,
             fecha_revision_prevista, documento_url, responsable, notas),
        )
        instrumento_id = cur.fetchone()[0]
    conn.commit()
    return instrumento_id


def listar_instrumentos(conn, estado=None, distrito_id=None) -> list[dict]:
    query = _SELECT_CON_DISTRITO.format(tabla="instrumentos_gestion_ambiental")
    condiciones, params = [], []
    if estado:
        condiciones.append("t.estado = %s")
        params.append(estado)
    if distrito_id:
        condiciones.append("t.distrito_id = %s")
        params.append(distrito_id)
    if condiciones:
        query += " WHERE " + " AND ".join(condiciones)
    query += " ORDER BY t.fecha_revision_prevista NULLS LAST"
    with _dict_cursor(conn) as cur:
        cur.execute(query, params)
        return [dict(fila) for fila in cur.fetchall()]


# --- Comisión Ambiental Municipal (CAM) --------------------------------------

def insertar_cam_integrante(conn, *, distrito_id, institucion, sector, representante=None, cargo=None,
                             fecha_incorporacion=None, vigente=True) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO cam_integrantes
                (distrito_id, institucion, sector, representante, cargo, fecha_incorporacion, vigente)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (distrito_id, institucion, sector, representante, cargo, fecha_incorporacion, vigente),
        )
        integrante_id = cur.fetchone()[0]
    conn.commit()
    return integrante_id


def listar_cam_integrantes(conn, solo_vigentes=True, distrito_id=None) -> list[dict]:
    query = _SELECT_CON_DISTRITO.format(tabla="cam_integrantes")
    condiciones, params = [], []
    if solo_vigentes:
        condiciones.append("t.vigente = true")
    if distrito_id:
        condiciones.append("t.distrito_id = %s")
        params.append(distrito_id)
    if condiciones:
        query += " WHERE " + " AND ".join(condiciones)
    query += " ORDER BY d.nombre, t.institucion"
    with _dict_cursor(conn) as cur:
        cur.execute(query, params)
        return [dict(fila) for fila in cur.fetchall()]


def insertar_cam_sesion(conn, *, distrito_id, fecha, tipo, asistentes=None, acuerdos=None, acta_url=None) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO cam_sesiones (distrito_id, fecha, tipo, asistentes, acuerdos, acta_url)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (distrito_id, fecha, tipo, asistentes, acuerdos, acta_url),
        )
        sesion_id = cur.fetchone()[0]
    conn.commit()
    return sesion_id


def listar_cam_sesiones(conn, anio=None, distrito_id=None) -> list[dict]:
    query = _SELECT_CON_DISTRITO.format(tabla="cam_sesiones")
    condiciones, params = [], []
    if anio:
        condiciones.append("date_part('year', t.fecha) = %s")
        params.append(anio)
    if distrito_id:
        condiciones.append("t.distrito_id = %s")
        params.append(distrito_id)
    if condiciones:
        query += " WHERE " + " AND ".join(condiciones)
    query += " ORDER BY t.fecha DESC"
    with _dict_cursor(conn) as cur:
        cur.execute(query, params)
        return [dict(fila) for fila in cur.fetchall()]


# --- PLANEFA -------------------------------------------------------------------

def insertar_planefa_accion(conn, *, distrito_id, anio, unidad_fiscalizable, tipo_accion,
                             trimestre_programado=None, estado="programada",
                             resultado=None, notas=None) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO planefa_acciones
                (distrito_id, anio, unidad_fiscalizable, tipo_accion, trimestre_programado, estado, resultado, notas)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (distrito_id, anio, unidad_fiscalizable, tipo_accion, trimestre_programado, estado, resultado, notas),
        )
        accion_id = cur.fetchone()[0]
    conn.commit()
    return accion_id


def listar_planefa_acciones(conn, anio=None, distrito_id=None) -> list[dict]:
    query = _SELECT_CON_DISTRITO.format(tabla="planefa_acciones")
    condiciones, params = [], []
    if anio:
        condiciones.append("t.anio = %s")
        params.append(anio)
    if distrito_id:
        condiciones.append("t.distrito_id = %s")
        params.append(distrito_id)
    if condiciones:
        query += " WHERE " + " AND ".join(condiciones)
    query += " ORDER BY t.anio DESC, t.trimestre_programado"
    with _dict_cursor(conn) as cur:
        cur.execute(query, params)
        return [dict(fila) for fila in cur.fetchall()]


# --- Indicadores GALS ------------------------------------------------------------

def insertar_indicador_gals(conn, *, distrito_id, dimension, indicador, nivel_objetivo, avance_pct,
                             fecha_corte, notas=None) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO indicadores_gals
                (distrito_id, dimension, indicador, nivel_objetivo, avance_pct, fecha_corte, notas)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (distrito_id, dimension, indicador, nivel_objetivo, avance_pct, fecha_corte, notas),
        )
        indicador_id = cur.fetchone()[0]
    conn.commit()
    return indicador_id


def listar_indicadores_gals(conn, dimension=None, distrito_id=None) -> list[dict]:
    query = _SELECT_CON_DISTRITO.format(tabla="indicadores_gals")
    condiciones, params = [], []
    if dimension:
        condiciones.append("t.dimension = %s")
        params.append(dimension)
    if distrito_id:
        condiciones.append("t.distrito_id = %s")
        params.append(distrito_id)
    if condiciones:
        query += " WHERE " + " AND ".join(condiciones)
    query += " ORDER BY t.fecha_corte DESC"
    with _dict_cursor(conn) as cur:
        cur.execute(query, params)
        return [dict(fila) for fila in cur.fetchall()]
