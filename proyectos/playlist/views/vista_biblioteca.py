"""Acciones compartidas de archivos, guardado y reproducción musical."""

import asyncio
import inspect
import logging
from pathlib import Path

import flet as ft

from controllers.controlador_biblioteca import ControladorBiblioteca
from services.archivos_audio import ArchivosAudio
from services.persistencia import decodificar, guardar

ACENTO = "#70E0B1"


class VistaBiblioteca:
    """Presente instantáneas y envíe acciones al controlador, sin nodos."""

    def __init__(
        self,
        controlador: ControladorBiblioteca,
        directorio: Path | None = None,
        archivo_datos: Path | None = None,
    ) -> None:
        """Prepare dependencias, campos y estado de presentación."""
        self.controlador = controlador
        self.directorio = directorio or Path(__file__).resolve().parents[1]
        self.archivo_datos = (
            archivo_datos or self.directorio / "data/musica.json"
        )
        self._version_disco = self._version_guardado()
        self.archivos = ArchivosAudio(self.directorio / "assets")
        self.seccion = "Biblioteca"
        self.playlist_id = None
        self._origen = "individual"
        self._continuar = False
        self._playlist_audio = None
        self._serial = asyncio.Lock()
        self._pagina = None
        self._audio = None
        self._audio_destino = None
        self._importacion = None
        self._filtro = ft.TextField(
            label="Buscar título o artista",
            on_change=self._buscar,
            prefix_icon=ft.Icons.SEARCH,
        )
        self._nombre = ft.TextField(label="Nombre de nueva playlist")
        self._mensaje = ft.Text("Los cambios se conservan al pulsar Guardar.")
        self._contenido = ft.Column(spacing=16)
        self._estado_audio = ft.Text("Detenido", color=ACENTO)

    def _boton(self, texto: str, operacion, icono=None) -> ft.Button:
        """Cree botón con manejador asíncrono y errores visibles."""
        return ft.Button(texto, icon=icono, on_click=self._accion(operacion))

    def _accion(self, operacion):
        """Envuelva acciones para evitar reentradas y conservar formularios."""

        async def ejecutar(_evento=None) -> None:
            """Ejecute, espere si procede y refresque tras éxito."""
            async with self._serial:
                try:
                    evento_anterior = self.controlador.estado_vista()["evento"]
                    mensaje_anterior = self._mensaje.value
                    resultado = operacion()
                    if inspect.isawaitable(resultado):
                        await resultado
                    await self._validar_audio()
                    evento_actual = self.controlador.estado_vista()["evento"]
                    if (
                        evento_actual != evento_anterior
                        and self._mensaje.value == mensaje_anterior
                    ):
                        self._avisar(evento_actual)
                    self.actualizar()
                except (ValueError, OSError, TimeoutError) as error:
                    self._avisar(
                        str(error) or "El dispositivo no respondió.", True
                    )
                except Exception as error:
                    logging.exception("Fallo en una acción de la interfaz")
                    self._avisar(f"No se pudo completar: {error}", True)

        return ejecutar

    def _avisar(self, mensaje: str, error: bool = False) -> None:
        """Actualice el mensaje visible sin acumular diálogos."""
        self._mensaje.value = mensaje
        self._mensaje.color = "#FFB4AB" if error else ACENTO
        if self._pagina:
            self._pagina.update()

    def actualizar(self) -> None:
        """Publique cambios; las vistas musicales construyen su contenido."""
        if self._pagina:
            self._pagina.update()

    def _navegar(self, nombre: str) -> None:
        """Cambie sección sin editar datos del modelo."""
        self.seccion = nombre

    def _buscar(self, _evento) -> None:
        """Filtre catálogo al escribir sin reiniciar los campos."""
        self.actualizar()

    def _id_playlist(self) -> int:
        """Exija selección antes de operar una playlist."""
        if self.playlist_id is None:
            raise ValueError("Primero crea y selecciona una playlist.")
        return self.playlist_id

    def _confirmar(self, titulo: str, texto: str, operacion) -> None:
        """Pida confirmación concreta antes de borrar o reemplazar datos."""

        async def aceptar() -> None:
            """Cierre el diálogo y aplique la operación elegida."""
            self._pagina.pop_dialog()
            resultado = operacion()
            if inspect.isawaitable(resultado):
                await resultado

        self._pagina.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text(titulo),
                content=ft.Text(texto),
                actions=[
                    self._boton("Cancelar", self._pagina.pop_dialog),
                    self._boton("Confirmar", aceptar),
                ],
            )
        )

    def _confirmar_baja(self, identificador: int) -> None:
        """Explique que la baja también quita apariciones en playlists."""
        self._confirmar(
            "Eliminar canción",
            "Se quitará de todas las playlists. Puedes deshacer este cambio.",
            lambda: self.controlador.eliminar(identificador),
        )

    def _confirmar_playlist(self) -> None:
        """Confirme baja de playlist conservando el catálogo."""
        identificador = self._id_playlist()
        self._confirmar(
            "Eliminar playlist",
            "Las canciones seguirán en la biblioteca.",
            lambda: self.controlador.borrar_playlist(identificador),
        )

    async def _iniciar_playlist(self) -> None:
        """Reproduzca actual sin saltar la primera canción del anillo."""
        identificador = self._id_playlist()
        foto = next(
            p
            for p in self.controlador.estado_vista()["estado"].playlists
            if p.identificador == identificador
        )
        if foto.actual_id is None:
            raise ValueError("La playlist está vacía.")
        await self._entrada(foto.actual_id)

    async def _entrada(self, entrada_id: int) -> None:
        """Seleccione aparición y conserve playlist para avance automático."""
        self._playlist_audio = self._id_playlist()
        cancion = self.controlador.seleccionar(
            self._playlist_audio, entrada_id
        )
        await self._escuchar(cancion, "playlist")

    async def _fin_audio(self) -> None:
        """Continúe tras fin real; detenga si cola vacía o archivo inválido."""
        async with self._serial:
            if not self._continuar or self._origen == "individual":
                return
            try:
                await self._saltar(1)
                self.actualizar()
            except Exception as error:
                await self._detener()
                self._avisar(f"Reproducción finalizada: {error}", True)

    async def _detener(self) -> None:
        """Detenga sin retirar otra solicitud ni mover el cursor."""
        self._continuar = False
        await self._audio.detener()

    async def _validar_audio(self) -> None:
        """Detenga si una edición quitó o cambió el archivo reproducido."""
        if self._audio and self._audio.actual_id is not None:
            actual = next(
                (
                    c
                    for c in self.controlador.listar()
                    if c.identificador == self._audio.actual_id
                ),
                None,
            )
            archivo_actual = getattr(
                self._audio, "archivo_actual", self._audio.audio.src
            )
            if actual is None or actual.archivo != archivo_actual:
                await self._detener()

    def _volumen(self, evento) -> None:
        """Cambie amplitud sin crear una edición de catálogo."""
        self._audio.volumen(float(evento.control.value))

    def _elegir_audio(self, identificador: int) -> None:
        """Abra selector mediante acción cliente compatible con web."""
        self._audio_destino = identificador
        self._pagina.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Asociar archivo de audio"),
                content=ft.Text(
                    "Se copiará al proyecto. Máximo 50 MB por archivo."
                ),
                actions=[
                    self._boton("Cancelar", self._pagina.pop_dialog),
                    ft.Button(
                        "Elegir archivo",
                        action=ft.PickFiles(
                            self._picker_audio,
                            allow_multiple=False,
                            with_data=True,
                            file_type=ft.FilePickerFileType.CUSTOM,
                            allowed_extensions=[
                                "wav",
                                "mp3",
                                "ogg",
                                "m4a",
                                "flac",
                            ],
                        ),
                    ),
                ],
            )
        )

    async def _archivo_audio(self, evento) -> None:
        """Copie selección a assets y registre asociación reversible."""
        if not evento.files:
            return
        archivo = evento.files[0]

        async def importar() -> None:
            """Copie fuera del bucle UI y conserve el original."""
            self._pagina.pop_dialog()
            ruta = await asyncio.to_thread(
                self.archivos.importar,
                archivo.name,
                archivo.bytes,
                archivo.path,
            )
            self.controlador.asociar_audio(self._audio_destino, ruta)
            self._avisar("Audio asociado. Pulsa Escuchar para reproducir.")

        await self._accion(importar)()

    async def _guardar(self) -> None:
        """Guarde atómicamente sin congelar el bucle de interfaz."""
        if self._version_disco != self._version_guardado():
            raise ValueError(
                "El guardado cambió en otra sesión. Exporta tus cambios "
                "antes de cargar el archivo actualizado."
            )
        await asyncio.to_thread(
            guardar,
            self.archivo_datos,
            self.controlador.estado_vista()["estado"],
        )
        self._version_disco = self._version_guardado()
        self._avisar(f"Guardado en {self.archivo_datos.name}.")

    async def _exportar(self) -> None:
        """Descargue JSON en web o permita elegir destino en escritorio."""
        await self._picker_guardar.save_file(
            dialog_title="Exportar biblioteca",
            file_name="biblioteca.json",
            src_bytes=self.controlador.exportar().encode("utf-8"),
        )

    async def _archivo_json(self, evento) -> None:
        """Valide la selección y confirme antes de aplicar la importación."""
        if not evento.files:
            return

        def preparar() -> None:
            """Lea hasta 5 MB sin modificar todavía la sesión."""
            archivo = evento.files[0]
            if archivo.size > 5 * 1024 * 1024:
                raise ValueError("El JSON supera 5 MB.")
            contenido = archivo.bytes
            if contenido is None and archivo.path:
                contenido = Path(archivo.path).read_bytes()
            self._importacion = (contenido or b"").decode("utf-8-sig")
            decodificar(self._importacion)
            self._confirmar(
                "Importar biblioteca",
                "Reemplazará catálogo y playlists. "
                "Los audios se conservan por separado.",
                self._aplicar_importacion,
            )

        await self._accion(preparar)()

    def _version_guardado(self) -> tuple[int, int] | None:
        """Observe fecha/tamaño para detectar escrituras de otra pestaña."""
        try:
            datos = self.archivo_datos.stat()
            return datos.st_mtime_ns, datos.st_size
        except FileNotFoundError:
            return None
