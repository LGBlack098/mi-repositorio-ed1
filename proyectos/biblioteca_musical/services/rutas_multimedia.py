"""Resuelva archivos importados para web y aplicaciones móviles nativas."""

import os
from pathlib import Path


def fuente_multimedia(assets: Path, relativa: str) -> str:
    """Use ruta local absoluta en móvil y asset relativo en web/Windows.

    Flet móvil resuelve los assets empaquetados desde otro directorio.
    Una ruta absoluta existente permite al cliente nativo leer las copias
    guardadas en su almacenamiento privado. Los datos persistidos siguen
    siendo relativos, para no trasladar rutas de un dispositivo a otro.
    """
    if os.getenv("FLET_PLATFORM", "").lower() in ("android", "ios"):
        ruta = (assets / relativa).resolve()
        if not ruta.is_relative_to(assets.resolve()):
            raise ValueError("El archivo debe permanecer dentro de assets.")
        return str(ruta)
    return relativa
