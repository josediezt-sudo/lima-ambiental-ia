import os
from pathlib import Path

import yaml

RUTA_DEFECTO = Path(__file__).resolve().parent.parent / "config" / "municipio.yml"


def cargar_municipio(ruta: str | None = None) -> dict:
    """Carga la configuración de la municipalidad (config/municipio.yml).

    Cada despliegue de este proyecto personaliza su propia municipalidad copiando
    config/municipio.example.yml a config/municipio.yml (fuera de git) y editándolo.
    """
    ruta_config = Path(ruta or os.environ.get("MUNICIPIO_CONFIG", RUTA_DEFECTO))
    if not ruta_config.exists():
        raise FileNotFoundError(
            f"No se encontró {ruta_config}. Copia config/municipio.example.yml a "
            "config/municipio.yml y personalízalo para tu municipalidad."
        )
    with open(ruta_config, encoding="utf-8") as f:
        return yaml.safe_load(f)
