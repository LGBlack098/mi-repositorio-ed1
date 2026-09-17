"""Entidad que representa una canción de la playlist."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Cancion:
    """Datos inmutables de una canción identificada de forma única."""

    identificador: int
    titulo: str
    artista: str
