"""Controlador que conecta la vista con el TDA lista circular."""

from models.cancion import Cancion
from models.lista_circular import ListaCircular


class ErrorDeValidacion(ValueError):
    """Error provocado por datos de entrada inválidos."""


class ControladorPlaylist:
    """Expone las operaciones que la interfaz puede ejecutar."""

    def __init__(self, modelo: ListaCircular | None = None) -> None:
        self._modelo = modelo or ListaCircular()

    def agregar_cancion(self, titulo: str, artista: str) -> Cancion:
        """Valida y agrega una canción al final de la playlist."""
        titulo_limpio = titulo.strip()
        artista_limpio = artista.strip()

        if not titulo_limpio:
            raise ErrorDeValidacion("El título no puede estar vacío.")
        if not artista_limpio:
            raise ErrorDeValidacion("El artista no puede estar vacío.")

        return self._modelo.agregar(titulo_limpio, artista_limpio)

    def seleccionar_cancion(self, identificador: int) -> Cancion:
        """Establece como actual la canción seleccionada por el usuario."""
        cancion = self._modelo.seleccionar(identificador)
        if cancion is None:
            raise ErrorDeValidacion("La canción seleccionada ya no existe.")
        return cancion

    def reproducir_siguiente(self) -> Cancion:
        """Avanza circularmente a la siguiente canción."""
        cancion = self._modelo.avanzar()
        if cancion is None:
            raise ErrorDeValidacion("La playlist está vacía.")
        return cancion

    def eliminar_cancion(self, identificador: int) -> None:
        """Elimina una canción mediante su identificador único."""
        if not self._modelo.eliminar(identificador):
            raise ErrorDeValidacion("La canción seleccionada ya no existe.")

    def obtener_canciones(self, filtro: str = "") -> list[Cancion]:
        """Retorna todas las canciones o las coincidencias del filtro."""
        filtro_limpio = filtro.strip()
        if filtro_limpio:
            return self._modelo.buscar(filtro_limpio)
        return self._modelo.listar()

    def obtener_actual(self) -> Cancion | None:
        """Retorna la canción actual."""
        return self._modelo.obtener_actual()

    def cantidad(self) -> int:
        """Retorna el tamaño actual de la playlist."""
        return len(self._modelo)
