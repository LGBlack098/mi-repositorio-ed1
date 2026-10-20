"""Adaptador de entradas; no conoce nodos ni importa Flet."""

from models.biblioteca import Biblioteca
from models.cancion import Cancion
from models.navegacion import navegar
from models.sesion import SesionMusical


class ControladorBiblioteca:
    """Exponga operaciones musicales para la interfaz."""

    def __init__(self, biblioteca: Biblioteca | None = None) -> None:
        """Reciba un modelo o cree uno para esta sesión."""
        self._biblioteca = (
            biblioteca if biblioteca is not None else Biblioteca()
        )
        self.sesion = SesionMusical(self._biblioteca)

    def agregar(
        self,
        titulo: str,
        artista: str,
        duracion_texto: str,
        archivo: str = "",
        **metadatos,
    ) -> Cancion:
        """Convierta segundos escritos a entero y solicite la inserción.

        Retorna la canción. ValueError informa duración o campos
        inválidos. La conversión textual es responsabilidad del
        controlador; la validación del dominio pertenece al modelo.
        """
        try:
            duracion = int(duracion_texto)
        except ValueError as error:
            raise ValueError(
                "Escribe la duración en segundos enteros."
            ) from error
        return self.sesion.editar(
            "Agregar canción",
            lambda: self._biblioteca.agregar(
                titulo, artista, duracion, archivo, **metadatos
            ),
        )

    def listar(self, filtro: str = "") -> tuple[Cancion, ...]:
        """Solicite datos filtrados para mostrar, sin exponer nodos."""
        return self._biblioteca.listar(filtro)

    def eliminar(self, identificador: int) -> Cancion:
        """Solicite la eliminación por ID; propaga ValueError si falta."""
        return self.sesion.borrar_cancion(identificador)

    def asociar_audio(
        self, identificador: int, archivo: str, **metadatos
    ) -> None:
        """Reemplace una entidad inmutable conservando ID y posición."""
        from dataclasses import replace

        anterior = self._biblioteca.obtener(identificador)
        if archivo != anterior.archivo:
            metadatos = {
                "nombre_archivo": "",
                "tamano_bytes": 0,
                "formato": "",
                "portada": "",
                **metadatos,
            }
        nueva = replace(anterior, archivo=archivo, **metadatos)
        self.sesion.editar(
            "Asociar audio",
            lambda: self._biblioteca.restaurar(
                tuple(
                    nueva if c.identificador == identificador else c
                    for c in self._biblioteca.listar()
                ),
                self._biblioteca.siguiente_id,
            ),
        )

    def estado_vista(self) -> dict:
        """Entregue instantáneas para dibujar; nunca entregue nodos."""
        sesion = self.sesion
        return {
            "estado": sesion.estado(),
            "fifo": tuple(sesion.fifo),
            "prioridad": tuple(sesion.prioridad),
            "turnos": tuple(sesion.turnos),
            "deshacer": tuple(c.etiqueta for c in sesion.deshacer),
            "rehacer": tuple(c.etiqueta for c in sesion.rehacer),
            "evento": sesion.ultimo_evento,
        }

    def crear_playlist(self, nombre: str) -> None:
        """Valide nombre mediante el modelo y cree una playlist."""
        self.sesion.crear_playlist(nombre)

    def borrar_playlist(self, identificador: int) -> None:
        """Delegue baja de playlist y depuración de turnos."""
        self.sesion.borrar_playlist(identificador)

    def agregar_entrada(self, playlist_id: int, cancion_id: int) -> None:
        """Delegue inserción de una aparición en el anillo."""
        self.sesion.agregar_entrada(playlist_id, cancion_id)

    def borrar_entrada(self, playlist_id: int, entrada_id: int) -> None:
        """Delegue baja de una sola aparición."""
        self.sesion.borrar_entrada(playlist_id, entrada_id)

    def mover(self, playlist_id: int, direccion: int) -> Cancion:
        """Devuelva la canción del cursor tras avanzar o retroceder."""
        return self.sesion.mover(playlist_id, direccion)

    def seleccionar(self, playlist_id: int, entrada_id: int) -> Cancion:
        """Devuelva la canción de una entrada seleccionada."""
        return self.sesion.seleccionar(playlist_id, entrada_id)

    def solicitar(self, cancion_id: int, prioridad: int | None = None) -> None:
        """Envíe solicitud FIFO o prioritaria sin duplicarla."""
        self.sesion.solicitar(cancion_id, prioridad)

    def agregar_turno(self, playlist_id: int) -> None:
        """Envíe playlist a la cola circular de turnos."""
        self.sesion.agregar_turno(playlist_id)

    def consumir(self, modo: str) -> Cancion:
        """Devuelva la próxima solicitud del modo elegido."""
        return self.sesion.consumir(modo)

    def historial(self, rehacer: bool = False) -> None:
        """Delegue deshacer/rehacer; ValueError si no hay acciones."""
        if rehacer:
            self.sesion.rehacer_cambio()
        else:
            self.sesion.deshacer_cambio()

    def exportar(self) -> str:
        """Genere JSON portable de catálogo y playlists, sin colas."""
        from services.persistencia import codificar

        return codificar(self.sesion.estado())

    def importar(self, texto: str) -> None:
        """Valide todo antes de reemplazar; cargue con historial limpio."""
        from models.estructuras.lineales import Pila
        from services.persistencia import decodificar

        estado = decodificar(texto)
        nueva = SesionMusical()
        nueva.restaurar(estado, conservar_marcas=False)
        self.sesion = nueva
        self._biblioteca = nueva.biblioteca
        nueva.deshacer = Pila()
        nueva.rehacer = Pila()
        nueva.ultimo_evento = "Biblioteca cargada; colas e historial vacíos."

    def navegar(self, origen, actual_id, playlist_id, direccion, repetir):
        """Delegue la política de avance al modelo, sin usar Flet."""
        return navegar(
            self.sesion, origen, actual_id, playlist_id, direccion, repetir
        )
