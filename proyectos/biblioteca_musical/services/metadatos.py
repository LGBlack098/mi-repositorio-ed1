"""Lectura de información musical sin pedir formularios al oyente."""

import math
from pathlib import Path

import mutagen


def leer_metadatos(ruta: Path, nombre_original: str) -> tuple[str, str, int]:
    """Obtenga título, artista y duración real de un archivo reconocido.

    Si faltan etiquetas se usa Artista - Título del nombre o un artista
    desconocido. Rechaza audio ilegible o sin duración; nunca inventa
    segundos para insertar una canción. No modifica el archivo.
    """
    try:
        audio = mutagen.File(ruta, easy=True)
    except (mutagen.MutagenError, OSError) as error:
        raise ValueError("No se pudo leer el archivo de audio.") from error
    if audio is None or not math.isfinite(audio.info.length):
        raise ValueError("El archivo no contiene audio reconocido.")
    if audio.info.length <= 0:
        raise ValueError("El audio no tiene una duración válida.")
    nombre = Path(nombre_original).stem
    artista, titulo = (
        nombre.split(" - ", 1)
        if " - " in nombre
        else ("Artista desconocido", nombre)
    )
    etiquetas = audio.tags or {}

    def etiqueta(clave: str, alternativa: str) -> str:
        """Lea primera etiqueta no vacía o conserve el nombre de archivo."""
        valores = etiquetas.get(clave) or etiquetas.get(
            {"title": "TIT2", "artist": "TPE1"}[clave]
        )
        if hasattr(valores, "text"):
            valores = valores.text
        if valores:
            valor = str(valores[0] if isinstance(valores, list) else valores)
            if valor.strip():
                return valor.strip()
        return alternativa.strip() or "Sin título"

    return (
        etiqueta("title", titulo),
        etiqueta("artist", artista),
        max(1, round(audio.info.length)),
    )
