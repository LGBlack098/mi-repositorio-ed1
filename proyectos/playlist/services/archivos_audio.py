"""Importación local de audio a assets para escritorio y servidor web."""

import shutil
from pathlib import Path
from uuid import uuid4

EXTENSIONES = (".wav", ".mp3", ".ogg", ".m4a", ".flac")
LIMITE_AUDIO = 50 * 1024 * 1024


class ArchivosAudio:
    """Conserve copias propias con nombres únicos, sin modificar originales."""

    def __init__(self, assets: Path) -> None:
        """Fije el directorio servido por Flet."""
        self.assets = assets.resolve()

    def importar(
        self,
        nombre: str,
        contenido: bytes | None = None,
        origen: str | None = None,
    ) -> str:
        """Copie un audio y devuelva audio/uuid.ext; O(bytes).

        Navegador aporta bytes; escritorio aporta ruta. Máximo 50 MB.
        La extensión no garantiza un códec válido: el reproductor debe
        comunicar fallos de decodificación. No borra archivos al deshacer.
        """
        extension = Path(nombre).suffix.lower()
        if extension not in EXTENSIONES:
            raise ValueError("Usa WAV, MP3, OGG, M4A o FLAC.")
        if contenido is None:
            if not origen or not Path(origen).is_file():
                raise ValueError("El archivo seleccionado ya no existe.")
            tamano = Path(origen).stat().st_size
        else:
            tamano = len(contenido)
        if not 0 < tamano <= LIMITE_AUDIO:
            raise ValueError("El audio debe ocupar entre 1 byte y 50 MB.")
        destino = self.assets / "audio" / f"{uuid4().hex}{extension}"
        destino.parent.mkdir(parents=True, exist_ok=True)
        if contenido is None:
            shutil.copyfile(origen, destino)
        else:
            destino.write_bytes(contenido)
        return destino.relative_to(self.assets).as_posix()

    def comprobar(self, archivo: str) -> str:
        """Resuelva un asset; ValueError si falta o sale de assets."""
        ruta = (self.assets / archivo).resolve()
        if not archivo or not ruta.is_relative_to(self.assets):
            raise ValueError("Esta canción no tiene audio asociado.")
        if not ruta.is_file():
            raise ValueError("No se encuentra el audio; vuelve a asociarlo.")
        return archivo
