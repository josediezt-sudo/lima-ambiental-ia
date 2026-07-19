"""CLI para registrar y consultar datos del Sistema Local de Gestión Ambiental (SLGA).

No existe una API pública para esta información: instrumentos de gestión,
composición de la CAM, acciones PLANEFA y avance GALS son decisiones/actas
administrativas propias de cada municipalidad, así que se cargan manualmente.

Uso:
    python -m src.slga.cli instrumento-add --tipo agenda_ambiental_local --nombre "Agenda Ambiental Local 2026-2027" --estado vigente
    python -m src.slga.cli instrumento-list [--estado vigente]
    python -m src.slga.cli cam-integrante-add --institucion "Municipalidad" --sector publico --representante "..." --cargo "..."
    python -m src.slga.cli cam-integrante-list
    python -m src.slga.cli cam-sesion-add --fecha 2026-03-15 --tipo ordinaria --asistentes 12 --acuerdos "..."
    python -m src.slga.cli cam-sesion-list [--anio 2026]
    python -m src.slga.cli planefa-add --anio 2026 --unidad "Comercio ambulatorio" --tipo-accion supervision --trimestre 2
    python -m src.slga.cli planefa-list [--anio 2026]
    python -m src.slga.cli gals-indicador-add --dimension calidad_ambiental --indicador "..." --nivel-objetivo "GALS I" --avance-pct 60 --fecha-corte 2026-06-30
    python -m src.slga.cli gals-indicador-list [--dimension calidad_ambiental]
    python -m src.slga.cli seed-ejemplo
"""
import argparse
import json

import yaml

from src.db import get_connection
from src.slga import repositorio as repo


def _print_filas(filas: list[dict]) -> None:
    print(json.dumps(filas, indent=2, ensure_ascii=False, default=str))


def _cmd_instrumento_add(conn, args):
    instrumento_id = repo.insertar_instrumento(
        conn, tipo=args.tipo, nombre=args.nombre, estado=args.estado,
        norma_aprobacion=args.norma_aprobacion, fecha_aprobacion=args.fecha_aprobacion,
        fecha_revision_prevista=args.fecha_revision_prevista, documento_url=args.documento_url,
        responsable=args.responsable, notas=args.notas,
    )
    print(f"Instrumento creado con id={instrumento_id}")


def _cmd_instrumento_list(conn, args):
    _print_filas(repo.listar_instrumentos(conn, estado=args.estado))


def _cmd_cam_integrante_add(conn, args):
    integrante_id = repo.insertar_cam_integrante(
        conn, institucion=args.institucion, sector=args.sector, representante=args.representante,
        cargo=args.cargo, fecha_incorporacion=args.fecha_incorporacion,
    )
    print(f"Integrante CAM creado con id={integrante_id}")


def _cmd_cam_integrante_list(conn, args):
    _print_filas(repo.listar_cam_integrantes(conn, solo_vigentes=not args.todos))


def _cmd_cam_sesion_add(conn, args):
    sesion_id = repo.insertar_cam_sesion(
        conn, fecha=args.fecha, tipo=args.tipo, asistentes=args.asistentes,
        acuerdos=args.acuerdos, acta_url=args.acta_url,
    )
    print(f"Sesión CAM creada con id={sesion_id}")


def _cmd_cam_sesion_list(conn, args):
    _print_filas(repo.listar_cam_sesiones(conn, anio=args.anio))


def _cmd_planefa_add(conn, args):
    accion_id = repo.insertar_planefa_accion(
        conn, anio=args.anio, unidad_fiscalizable=args.unidad, tipo_accion=args.tipo_accion,
        trimestre_programado=args.trimestre, estado=args.estado, resultado=args.resultado,
    )
    print(f"Acción PLANEFA creada con id={accion_id}")


def _cmd_planefa_list(conn, args):
    _print_filas(repo.listar_planefa_acciones(conn, anio=args.anio))


def _cmd_gals_indicador_add(conn, args):
    indicador_id = repo.insertar_indicador_gals(
        conn, dimension=args.dimension, indicador=args.indicador, nivel_objetivo=args.nivel_objetivo,
        avance_pct=args.avance_pct, fecha_corte=args.fecha_corte,
    )
    print(f"Indicador GALS creado con id={indicador_id}")


def _cmd_gals_indicador_list(conn, args):
    _print_filas(repo.listar_indicadores_gals(conn, dimension=args.dimension))


def _cmd_seed_ejemplo(conn, args):
    with open(args.archivo, encoding="utf-8") as f:
        datos = yaml.safe_load(f)

    for item in datos.get("instrumentos", []):
        repo.insertar_instrumento(conn, **item)
    for item in datos.get("cam_integrantes", []):
        repo.insertar_cam_integrante(conn, **item)
    for item in datos.get("cam_sesiones", []):
        repo.insertar_cam_sesion(conn, **item)
    for item in datos.get("planefa_acciones", []):
        repo.insertar_planefa_accion(conn, **item)
    for item in datos.get("indicadores_gals", []):
        repo.insertar_indicador_gals(conn, **item)

    print(f"Datos de ejemplo cargados desde {args.archivo}")


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="CLI del Sistema Local de Gestión Ambiental (SLGA)")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("instrumento-add")
    p.add_argument("--tipo", required=True, choices=repo.TIPOS_INSTRUMENTO)
    p.add_argument("--nombre", required=True)
    p.add_argument("--estado", default="en_elaboracion", choices=repo.ESTADOS_INSTRUMENTO)
    p.add_argument("--norma-aprobacion", dest="norma_aprobacion")
    p.add_argument("--fecha-aprobacion", dest="fecha_aprobacion")
    p.add_argument("--fecha-revision-prevista", dest="fecha_revision_prevista")
    p.add_argument("--documento-url", dest="documento_url")
    p.add_argument("--responsable")
    p.add_argument("--notas")
    p.set_defaults(func=_cmd_instrumento_add)

    p = sub.add_parser("instrumento-list")
    p.add_argument("--estado", choices=repo.ESTADOS_INSTRUMENTO)
    p.set_defaults(func=_cmd_instrumento_list)

    p = sub.add_parser("cam-integrante-add")
    p.add_argument("--institucion", required=True)
    p.add_argument("--sector", required=True, choices=repo.SECTORES_CAM)
    p.add_argument("--representante")
    p.add_argument("--cargo")
    p.add_argument("--fecha-incorporacion", dest="fecha_incorporacion")
    p.set_defaults(func=_cmd_cam_integrante_add)

    p = sub.add_parser("cam-integrante-list")
    p.add_argument("--todos", action="store_true", help="incluir integrantes no vigentes")
    p.set_defaults(func=_cmd_cam_integrante_list)

    p = sub.add_parser("cam-sesion-add")
    p.add_argument("--fecha", required=True)
    p.add_argument("--tipo", required=True, choices=repo.TIPOS_SESION)
    p.add_argument("--asistentes", type=int)
    p.add_argument("--acuerdos")
    p.add_argument("--acta-url", dest="acta_url")
    p.set_defaults(func=_cmd_cam_sesion_add)

    p = sub.add_parser("cam-sesion-list")
    p.add_argument("--anio", type=int)
    p.set_defaults(func=_cmd_cam_sesion_list)

    p = sub.add_parser("planefa-add")
    p.add_argument("--anio", type=int, required=True)
    p.add_argument("--unidad", required=True, dest="unidad")
    p.add_argument("--tipo-accion", required=True, dest="tipo_accion")
    p.add_argument("--trimestre", type=int, dest="trimestre")
    p.add_argument("--estado", default="programada", choices=repo.ESTADOS_PLANEFA)
    p.add_argument("--resultado")
    p.set_defaults(func=_cmd_planefa_add)

    p = sub.add_parser("planefa-list")
    p.add_argument("--anio", type=int)
    p.set_defaults(func=_cmd_planefa_list)

    p = sub.add_parser("gals-indicador-add")
    p.add_argument("--dimension", required=True, choices=repo.DIMENSIONES_GALS)
    p.add_argument("--indicador", required=True)
    p.add_argument("--nivel-objetivo", required=True, dest="nivel_objetivo", choices=repo.NIVELES_GALS)
    p.add_argument("--avance-pct", type=float, required=True, dest="avance_pct")
    p.add_argument("--fecha-corte", required=True, dest="fecha_corte")
    p.set_defaults(func=_cmd_gals_indicador_add)

    p = sub.add_parser("gals-indicador-list")
    p.add_argument("--dimension", choices=repo.DIMENSIONES_GALS)
    p.set_defaults(func=_cmd_gals_indicador_list)

    p = sub.add_parser("seed-ejemplo")
    p.add_argument("--archivo", default="config/slga_ejemplo.yml")
    p.set_defaults(func=_cmd_seed_ejemplo)

    return parser


def main() -> None:
    args = construir_parser().parse_args()
    conn = get_connection()
    try:
        args.func(conn, args)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
