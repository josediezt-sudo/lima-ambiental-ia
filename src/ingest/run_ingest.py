"""CLI para correr los ingestores disponibles.

Uso:
    python -m src.ingest.run_ingest aire
    python -m src.ingest.run_ingest residuos
    python -m src.ingest.run_ingest senamhi_csv <ruta_al_csv>
    python -m src.ingest.run_ingest agua              # requiere config/fuentes_ckan.yml
    python -m src.ingest.run_ingest ruido
    python -m src.ingest.run_ingest areas_verdes
    python -m src.ingest.run_ingest incendios          # NASA FIRMS
    python -m src.ingest.run_ingest bosques            # Global Forest Watch
"""
import sys

from src.ingest import (
    ckan_generico,
    global_forest_watch,
    nasa_firms,
    openaq_aire,
    residuos_ckan,
    senamhi_aire_csv,
)

COMANDOS = {
    "aire": lambda args: openaq_aire.ejecutar(),
    "residuos": lambda args: residuos_ckan.ejecutar(),
    "senamhi_csv": lambda args: senamhi_aire_csv.ejecutar(args[0]),
    "agua": lambda args: ckan_generico.ejecutar("cobertura_agua_potable"),
    "ruido": lambda args: ckan_generico.ejecutar("nivel_ruido_ambiental"),
    "areas_verdes": lambda args: ckan_generico.ejecutar("areas_verdes_por_habitante"),
    "incendios": lambda args: nasa_firms.ejecutar(),
    "bosques": lambda args: global_forest_watch.ejecutar(),
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in COMANDOS:
        print(f"Uso: python -m src.ingest.run_ingest <{'|'.join(COMANDOS)}> [args]")
        sys.exit(1)

    comando, args = sys.argv[1], sys.argv[2:]
    COMANDOS[comando](args)


if __name__ == "__main__":
    main()
