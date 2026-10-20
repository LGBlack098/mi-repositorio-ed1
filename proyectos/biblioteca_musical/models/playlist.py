"""Entidad playlist con entradas identificables y navegación circular."""

from dataclasses import dataclass

from models.estructuras.lista_circular import ListaCircular


@dataclass(frozen=True)
class Entrada:
    """Identifique una aparición de una canción, permitiendo repeticiones."""

    identificador: int
    cancion_id: int


class Playlist:
    """Agrupe nombre e ID y delegue enlaces en una lista circular."""

    def __init__(self, identificador: int, nombre: str) -> None:
        """Cree una playlist vacía; ValueError si el nombre está vacío."""
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre de playlist no puede estar vacío.")
        self.identificador = identificador
        self.nombre = nombre.strip()
        self.entradas: ListaCircular[Entrada] = ListaCircular()
