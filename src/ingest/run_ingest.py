"""CLI para correr los ingestores disponibles.

Uso:
    python -m src.ingest.run_ingest aire
    python -m src.ingest.run_ingest residuos
    python -m src.ingest.run_ingest senamhi_csv <ruta_al_csv>
"""
import sys

from src.ingest import openaq_aire, residuos_ckan, senamhi_aire_csv

COMANDOS = {
    "aire": lambda args: openaq_aire.ejecutar(),
    "residuos": lambda args: residuos_ckan.ejecutar(),
    "senamhi_csv": lambda args: senamhi_aire_csv.ejecutar(args[0]),
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in COMANDOS:
        print(f"Uso: python -m src.ingest.run_ingest <{'|'.join(COMANDOS)}> [args]")
        sys.exit(1)

    comando, args = sys.argv[1], sys.argv[2:]
    COMANDOS[comando](args)


if __name__ == "__main__":
    main()
