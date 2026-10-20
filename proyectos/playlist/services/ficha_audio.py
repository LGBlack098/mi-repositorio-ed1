"""Ficha de archivo y extracción de portada incrustada sin red."""

from base64 import b64decode
from pathlib import Path

import mutagen
from mutagen.flac import Picture


def extraer_portada(ruta: Path) -> str:
    """Copie una portada JPEG/PNG de hasta 3 MB a assets/portadas.

    Admite ID3/APIC, FLAC, MP4/covr y comentarios Vorbis. Si falta o
    es ilegible, devuelve vacío para usar el arte predeterminado.
    No cambia el audio ni descarga imágenes.
    """
    try:
        audio = mutagen.File(ruta)
        if audio is None:
            return ""
        imagenes = list(getattr(audio, "pictures", ()))
        tags = audio.tags or {}
        if hasattr(tags, "getall"):
            imagenes.extend(tags.getall("APIC"))
        candidatos = [i.data for i in imagenes]
        candidatos.extend(tags.get("covr", ()))
        for bloque in tags.get("metadata_block_picture", ()):
            if len(bloque) <= 4 * 1024 * 1024:
                candidatos.append(Picture(b64decode(bloque)).data)
        for datos in candidatos:
            if not 0 < len(datos) <= 3 * 1024 * 1024:
                continue
            extension = (
                ".png"
                if datos.startswith(b"\x89PNG\r\n\x1a\n")
                else ".jpg"
                if datos.startswith(b"\xff\xd8\xff")
                else ""
            )
            if extension:
                carpeta = ruta.parent.parent / "portadas"
                carpeta.mkdir(parents=True, exist_ok=True)
                destino = carpeta / (ruta.stem + extension)
                destino.write_bytes(datos)
                return "portadas/" + destino.name
    except (mutagen.MutagenError, OSError, ValueError, TypeError):
        return ""
    return ""


def leer_ficha(ruta: Path, nombre: str) -> dict:
    """Obtenga nombre original, bytes, formato real y portada opcional."""
    audio = mutagen.File(ruta)
    if audio is None:
        raise ValueError("El archivo no contiene audio reconocido.")
    return {
        "nombre_archivo": Path(nombre).name,
        "tamano_bytes": ruta.stat().st_size,
        "formato": audio.__class__.__name__.upper(),
        "portada": extraer_portada(ruta),
    }


def peso_legible(cantidad: int) -> str:
    """Exprese peso binario con unidades explícitas, sin alterar bytes."""
    if not cantidad:
        return "Sin datos"
    if cantidad < 1024:
        return f"{cantidad} B"
    if cantidad < 1024 * 1024:
        return f"{cantidad / 1024:.1f} KiB"
    return f"{cantidad / (1024 * 1024):.2f} MiB"
