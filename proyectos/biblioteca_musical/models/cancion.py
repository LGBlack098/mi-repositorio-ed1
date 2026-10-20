"""Definición de una canción y validación de sus datos."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Cancion:
    """Represente datos inmutables, sin enlaces ni controles gráficos.

    identificador distingue títulos repetidos. duracion_segundos es un
    entero positivo. archivo es una ruta relativa dentro de assets.
    """

    identificador: int
    titulo: str
    artista: str
    duracion_segundos: int
    archivo: str = ""
    nombre_archivo: str = ""
    tamano_bytes: int = 0
    formato: str = ""
    portada: str = ""

    def __post_init__(self) -> None:
        """Rechace campos inválidos con ValueError.

        El constructor generado por dataclass llama a este método.
        Las anotaciones de tipo no validan valores por sí mismas.
        El costo no depende del catálogo, pero sí del tamaño del texto.
        """
        if type(self.identificador) is not int or self.identificador <= 0:
            raise ValueError("El identificador debe ser un entero positivo.")
        if not isinstance(self.titulo, str) or not self.titulo.strip():
            raise ValueError("El título no puede estar vacío.")
        if not isinstance(self.artista, str) or not self.artista.strip():
            raise ValueError("El artista no puede estar vacío.")
        if (
            type(self.duracion_segundos) is not int
            or self.duracion_segundos <= 0
        ):
            raise ValueError("La duración debe ser un entero positivo.")
        if not isinstance(self.archivo, str):
            raise ValueError("El archivo debe ser una ruta de texto.")
        if type(self.tamano_bytes) is not int or self.tamano_bytes < 0:
            raise ValueError("El tamaño debe ser un entero no negativo.")
        for campo in (self.nombre_archivo, self.formato, self.portada):
            if not isinstance(campo, str):
                raise ValueError("Los metadatos de archivo deben ser texto.")
        if self.portada:
            from pathlib import PurePosixPath

            imagen = PurePosixPath(self.portada)
            if (
                len(imagen.parts) != 2
                or imagen.parts[0] != "portadas"
                or imagen.suffix.lower() not in (".jpg", ".png")
                or ".." in imagen.parts
                or "\\" in self.portada
                or ":" in self.portada
            ):
                raise ValueError("La portada debe estar en assets/portadas.")
        if self.archivo:
            from pathlib import PurePosixPath

            ruta = PurePosixPath(self.archivo)
            if (
                ruta.is_absolute()
                or len(ruta.parts) != 2
                or ruta.parts[0] != "audio"
                or ".." in ruta.parts
                or "\\" in self.archivo
                or ":" in self.archivo
            ):
                raise ValueError("El audio debe estar dentro de assets/audio.")

    def duracion_formateada(self) -> str:
        """Devuelva minutos:segundos sin modificar la canción; O(1)."""
        minutos, segundos = divmod(self.duracion_segundos, 60)
        return f"{minutos}:{segundos:02d}"
