"""Motor musical independiente de UI: playlists, historial y turnos."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from models.biblioteca import Biblioteca
from models.cancion import Cancion
from models.estructuras.lineales import (
    Cola,
    ColaCircular,
    ColaPrioridad,
    Pila,
    Prioridad,
)
from models.estructuras.lista_doble import ListaDoblementeEnlazada
from models.playlist import Entrada, Playlist

T = TypeVar("T")


@dataclass(frozen=True)
class FotoPlaylist:
    """Conserve datos y cursor, sin referencias de nodos mutables."""

    identificador: int
    nombre: str
    entradas: tuple[Entrada, ...]
    actual_id: int | None


@dataclass(frozen=True)
class Estado:
    """Instantánea de edición; las colas de sesión no forman parte."""

    canciones: tuple[Cancion, ...]
    playlists: tuple[FotoPlaylist, ...]
    siguiente_cancion: int
    siguiente_playlist: int
    siguiente_entrada: int


@dataclass(frozen=True)
class Cambio:
    """Guarde un antes/después y etiqueta para las dos pilas."""

    etiqueta: str
    antes: Estado
    despues: Estado


class SesionMusical:
    """Coordine el dominio, sin importar Flet ni tocar enlaces.

    Las ediciones son transacciones con instantáneas. Mover cursor y
    consumir colas no son ediciones. Historial limitado a 50 cambios
    para acotar memoria en este proyecto educativo.
    """

    def __init__(self, biblioteca: Biblioteca | None = None) -> None:
        """Cree catálogo, playlists, dos pilas y tres colas."""
        self.biblioteca = (
            biblioteca if biblioteca is not None else Biblioteca()
        )
        self.playlists: ListaDoblementeEnlazada[Playlist] = (
            ListaDoblementeEnlazada()
        )
        self.deshacer: Pila[Cambio] = Pila()
        self.rehacer: Pila[Cambio] = Pila()
        self.fifo: Cola[int] = Cola()
        self.prioridad: ColaPrioridad[int] = ColaPrioridad()
        self.turnos: ColaCircular[int] = ColaCircular(8)
        self._siguiente_playlist = 1
        self._siguiente_entrada = 1
        self.ultimo_evento = "Sesión iniciada."

    def estado(self) -> Estado:
        """Capture datos y cursores para historial/JSON; O(n + e + p)."""
        return Estado(
            self.biblioteca.listar(),
            tuple(
                FotoPlaylist(
                    p.identificador,
                    p.nombre,
                    tuple(p.entradas),
                    p.entradas.actual().identificador
                    if p.entradas.actual()
                    else None,
                )
                for p in self.playlists
            ),
            self.biblioteca.siguiente_id,
            self._siguiente_playlist,
            self._siguiente_entrada,
        )

    def restaurar(self, estado: Estado, conservar_marcas: bool = True) -> None:
        """Reconstruya enlaces y depure colas; O(n + e + p + q).

        El estado debe estar validado. Al deshacer no se reutilizan IDs
        generados anteriormente, aunque una inserción se haya deshecho.
        """
        marca = self.biblioteca.siguiente_id if conservar_marcas else 1
        self.biblioteca.restaurar(
            estado.canciones, max(marca, estado.siguiente_cancion)
        )
        nuevas: ListaDoblementeEnlazada[Playlist] = ListaDoblementeEnlazada()
        for foto in estado.playlists:
            playlist = Playlist(foto.identificador, foto.nombre)
            for entrada in foto.entradas:
                playlist.entradas.agregar(entrada)
            if foto.actual_id is not None:
                playlist.entradas.seleccionar(
                    lambda e: e.identificador == foto.actual_id
                )
            nuevas.agregar_final(playlist)
        self.playlists = nuevas
        self._siguiente_playlist = max(
            self._siguiente_playlist if conservar_marcas else 1,
            estado.siguiente_playlist,
        )
        self._siguiente_entrada = max(
            self._siguiente_entrada if conservar_marcas else 1,
            estado.siguiente_entrada,
        )
        self._depurar_colas()

    def editar(self, etiqueta: str, operacion: Callable[[], T]) -> T:
        """Ejecute una edición atómica y registre solo si tuvo éxito.

        Una excepción restaura el estado anterior y se propaga. Capturar
        y reconstruir instantáneas domina el costo de la edición.
        """
        antes = self.estado()
        try:
            resultado = operacion()
        except Exception:
            self.restaurar(antes)
            raise
        despues = self.estado()
        if antes != despues:
            self.deshacer.apilar(Cambio(etiqueta, antes, despues))
            if len(self.deshacer) > 50:
                recientes = tuple(self.deshacer)[:50]
                self.deshacer = Pila()
                for cambio in reversed(recientes):
                    self.deshacer.apilar(cambio)
            self.rehacer = Pila()
        self._depurar_colas()
        self.ultimo_evento = etiqueta
        return resultado

    def deshacer_cambio(self) -> None:
        """Restaure el antes y mueva cambio a rehacer; ValueError si vacío."""
        cambio = self.deshacer.desapilar()
        self.restaurar(cambio.antes)
        self.rehacer.apilar(cambio)
        self.ultimo_evento = f"Deshacer: {cambio.etiqueta}"

    def rehacer_cambio(self) -> None:
        """Restaure el después y devuelva cambio a deshacer."""
        cambio = self.rehacer.desapilar()
        self.restaurar(cambio.despues)
        self.deshacer.apilar(cambio)
        self.ultimo_evento = f"Rehacer: {cambio.etiqueta}"

    def crear_playlist(self, nombre: str) -> Playlist:
        """Agregue playlist vacía con ID único; ValueError si nombre vacío."""

        def operacion() -> Playlist:
            """Construya la entidad antes de consumir su ID."""
            playlist = Playlist(self._siguiente_playlist, nombre)
            self.playlists.agregar_final(playlist)
            self._siguiente_playlist += 1
            return playlist

        return self.editar("Crear playlist", operacion)

    def playlist(self, identificador: int) -> Playlist:
        """Busque playlist por ID; O(p), ValueError si ausente."""
        playlist = self.playlists.buscar(
            lambda p: p.identificador == identificador
        )
        if playlist is None:
            raise ValueError("Selecciona una playlist existente.")
        return playlist

    def borrar_playlist(self, identificador: int) -> None:
        """Elimine playlist y su turno, conservando canciones del catálogo."""
        self.playlist(identificador)
        self.editar(
            "Eliminar playlist",
            lambda: self.playlists.eliminar(
                lambda p: p.identificador == identificador
            ),
        )

    def agregar_entrada(self, playlist_id: int, cancion_id: int) -> Entrada:
        """Añada una aparición independiente; permite repetir canciones."""
        self.biblioteca.obtener(cancion_id)
        playlist = self.playlist(playlist_id)

        def operacion() -> Entrada:
            """Asigne identidad y agregue al final del anillo."""
            entrada = Entrada(self._siguiente_entrada, cancion_id)
            playlist.entradas.agregar(entrada)
            self._siguiente_entrada += 1
            return entrada

        return self.editar("Añadir a playlist", operacion)

    def borrar_entrada(self, playlist_id: int, entrada_id: int) -> None:
        """Elimine solo la aparición elegida; ValueError si falta."""
        playlist = self.playlist(playlist_id)

        def operacion() -> None:
            """Quite por identidad y compruebe si estaba presente."""
            borrada = playlist.entradas.eliminar(
                lambda e: e.identificador == entrada_id
            )
            if borrada is None:
                raise ValueError("La entrada ya no existe.")

        self.editar("Quitar de playlist", operacion)

    def borrar_cancion(self, identificador: int) -> Cancion:
        """Quite canción y todas sus apariciones; undo conserva sus IDs."""
        self.biblioteca.obtener(identificador)

        def operacion() -> Cancion:
            """Borre coincidencias de cada anillo en un solo recorrido."""
            for playlist in self.playlists:
                playlist.entradas.eliminar_todos(
                    lambda e: e.cancion_id == identificador
                )
            return self.biblioteca.eliminar(identificador)

        return self.editar("Eliminar canción y apariciones", operacion)

    def mover(self, playlist_id: int, direccion: int) -> Cancion:
        """Mueva el cursor circular y resuelva la canción; O(p + n)."""
        entrada = self.playlist(playlist_id).entradas.mover(direccion)
        if entrada is None:
            raise ValueError("La playlist está vacía.")
        self.ultimo_evento = "Cursor circular: anterior/siguiente O(1)."
        return self.biblioteca.obtener(entrada.cancion_id)

    def seleccionar(self, playlist_id: int, entrada_id: int) -> Cancion:
        """Seleccione una aparición sin crear historial; O(p + e + n)."""
        entrada = self.playlist(playlist_id).entradas.seleccionar(
            lambda e: e.identificador == entrada_id
        )
        if entrada is None:
            raise ValueError("La entrada ya no existe.")
        return self.biblioteca.obtener(entrada.cancion_id)

    def solicitar(self, cancion_id: int, prioridad: int | None = None) -> None:
        """Encole canción en un solo modo; prioridad None significa FIFO."""
        self.biblioteca.obtener(cancion_id)
        if prioridad is None:
            self.fifo.encolar(cancion_id)
            self.ultimo_evento = "Solicitud agregada a la cola FIFO."
        else:
            self.prioridad.encolar(Prioridad(cancion_id, prioridad))
            self.ultimo_evento = "Solicitud agregada a la cola de prioridad."

    def agregar_turno(self, playlist_id: int) -> None:
        """Encole playlist no vacía una sola vez; máximo ocho turnos."""
        playlist = self.playlist(playlist_id)
        if not len(playlist.entradas):
            raise ValueError("Añade canciones antes de crear el turno.")
        if playlist_id in self.turnos:
            raise ValueError("La playlist ya tiene un turno.")
        self.turnos.encolar(playlist_id)
        self.ultimo_evento = "Turno agregado a la cola circular."

    def consumir(self, modo: str) -> Cancion:
        """Consuma FIFO, prioridad o un turno que se reencola al final.

        Un turno entrega su cursor actual y luego lo avanza. Cola vacía
        produce ValueError. No registra ediciones ni duplica solicitudes.
        """
        if modo == "fifo":
            identificador = self.fifo.desencolar()
        elif modo == "prioridad":
            identificador = self.prioridad.desencolar().dato
        elif modo == "turnos":
            turno = self.turnos.desencolar()
            playlist = self.playlist(turno)
            entrada = playlist.entradas.actual()
            identificador = entrada.cancion_id
            playlist.entradas.mover()
            self.turnos.encolar(turno)
        else:
            raise ValueError("Modo de reproducción desconocido.")
        self.ultimo_evento = f"Atender solicitud: {modo}."
        return self.biblioteca.obtener(identificador)

    def _depurar_colas(self) -> None:
        """Reconstruya colas conservando orden y solo IDs vigentes."""
        ids = {c.identificador for c in self.biblioteca.listar()}
        fifo: Cola[int] = Cola()
        for identificador in self.fifo:
            if identificador in ids:
                fifo.encolar(identificador)
        prioridad: ColaPrioridad[int] = ColaPrioridad()
        # Ya están ordenados: usar inserción FIFO conserva orden en O(q).
        for solicitud in self.prioridad:
            if solicitud.dato in ids:
                Cola.encolar(prioridad, solicitud)
        playlists = {
            p.identificador for p in self.playlists if len(p.entradas)
        }
        turnos: ColaCircular[int] = ColaCircular(8)
        for identificador in self.turnos:
            if identificador in playlists:
                turnos.encolar(identificador)
        self.fifo, self.prioridad, self.turnos = fifo, prioridad, turnos
