"""Interfaz adaptable de biblioteca, playlists, colas y audio con Flet."""

import asyncio
import inspect
import logging
from pathlib import Path

import flet as ft

from controllers.controlador_biblioteca import ControladorBiblioteca
from services.archivos_audio import ArchivosAudio
from services.persistencia import cargar, codificar, decodificar, guardar
from services.reproductor import Reproductor
from views.visualizador import visualizar

PANEL = "#1A2332"
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
        self._titulo = ft.TextField(label="Título", col={"xs": 12, "md": 5})
        self._artista = ft.TextField(label="Artista", col={"xs": 12, "md": 5})
        self._duracion = ft.TextField(
            label="Duración (segundos)", col={"xs": 12, "md": 2}
        )
        self._nombre = ft.TextField(label="Nombre de nueva playlist")
        self._prioridad = ft.TextField(label="Prioridad", value="5", width=120)
        self._mensaje = ft.Text("Los cambios se conservan al pulsar Guardar.")
        self._contenido = ft.Column(spacing=16)
        self._reproduccion = ft.Text(
            "Elige una canción para escuchar", size=18
        )
        self._estado_audio = ft.Text("Detenido", color=ACENTO)
        self._selector = ft.Dropdown(
            label="Playlist seleccionada",
            on_select=self._cambiar_playlist,
        )
        self._modo = ft.Dropdown(
            label="Modo para atender solicitudes",
            value="fifo",
            options=[
                ft.DropdownOption(k, t)
                for k, t in (
                    ("fifo", "Orden de llegada (FIFO)"),
                    ("prioridad", "Mayor prioridad primero"),
                    ("turnos", "Turnos de playlists"),
                )
            ],
        )

    def montar(self, pagina: ft.Page) -> None:
        """Monte controles y servicios sin autoplay ni alterar el catálogo."""
        self._pagina = pagina
        pagina.title = "Sonoteca"
        pagina.theme_mode = ft.ThemeMode.DARK
        pagina.theme = ft.Theme(color_scheme_seed=ACENTO)
        pagina.bgcolor = "#10151F"
        pagina.padding = 20
        pagina.scroll = ft.ScrollMode.AUTO
        self._audio = Reproductor(
            self.archivos, self._notificar_audio, self._fin_audio
        )
        self._picker_audio = ft.FilePicker(on_result=self._archivo_audio)
        self._picker_json = ft.FilePicker(on_result=self._archivo_json)
        self._picker_guardar = ft.FilePicker()
        pagina.add(
            ft.Row(
                [
                    ft.Icon(ft.Icons.LIBRARY_MUSIC, color=ACENTO, size=36),
                    ft.Column(
                        [
                            ft.Text(
                                "SONOTECA", size=30, weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                "Tu música. Tus listas. "
                                "Cada estructura a la vista."
                            ),
                        ],
                        expand=True,
                    ),
                ]
            ),
            ft.Row(
                [
                    self._boton("Guardar", self._guardar, ft.Icons.SAVE),
                    self._boton("Cargar guardado", self._confirmar_carga),
                    self._boton("Exportar JSON", self._exportar),
                    ft.Button(
                        "Importar JSON",
                        action=ft.PickFiles(
                            self._picker_json,
                            allow_multiple=False,
                            with_data=True,
                            allowed_extensions=["json"],
                            file_type=ft.FilePickerFileType.CUSTOM,
                        ),
                    ),
                    self._boton(
                        "Deshacer", lambda: self.controlador.historial()
                    ),
                    self._boton(
                        "Rehacer", lambda: self.controlador.historial(True)
                    ),
                ],
                wrap=True,
            ),
            ft.Container(self._mensaje, padding=12, bgcolor=PANEL),
            ft.Row(
                [
                    self._boton(nombre, lambda n=nombre: self._navegar(n))
                    for nombre in (
                        "Biblioteca",
                        "Playlists",
                        "Colas",
                        "Estructuras",
                    )
                ],
                wrap=True,
            ),
            ft.Divider(),
            self._contenido,
            ft.Divider(),
            ft.Container(
                ft.Column(
                    [
                        ft.Text("REPRODUCTOR", color=ACENTO),
                        self._reproduccion,
                        self._estado_audio,
                        ft.Row(
                            [
                                self._boton(
                                    "Anterior", lambda: self._saltar(-1)
                                ),
                                self._boton("Pausa / Seguir", self._pausar),
                                self._boton("Detener", self._detener),
                                self._boton(
                                    "Siguiente", lambda: self._saltar(1)
                                ),
                            ],
                            wrap=True,
                        ),
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.VOLUME_UP),
                                ft.Slider(
                                    min=0,
                                    max=1,
                                    value=0.5,
                                    divisions=20,
                                    expand=True,
                                    on_change=self._volumen,
                                ),
                            ]
                        ),
                    ]
                ),
                bgcolor=PANEL,
                padding=18,
                border_radius=16,
            ),
        )
        self.actualizar()

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
        """Renderice datos del controlador y conserve selección vigente."""
        datos = self.controlador.estado_vista()
        estado = datos["estado"]
        ids = tuple(p.identificador for p in estado.playlists)
        if self.playlist_id not in ids:
            self.playlist_id = ids[0] if ids else None
        self._selector.options = [
            ft.DropdownOption(str(p.identificador), p.nombre)
            for p in estado.playlists
        ]
        self._selector.value = (
            str(self.playlist_id) if self.playlist_id is not None else None
        )
        construir = {
            "Biblioteca": lambda: self._biblioteca(estado),
            "Playlists": lambda: self._playlists(estado),
            "Colas": lambda: self._colas(datos),
            "Estructuras": lambda: visualizar(datos, self.playlist_id),
        }
        self._contenido.controls = construir[self.seccion]()
        if self._pagina:
            self._pagina.update()

    def _navegar(self, nombre: str) -> None:
        """Cambie sección sin editar datos del modelo."""
        self.seccion = nombre

    def _buscar(self, _evento) -> None:
        """Filtre catálogo al escribir sin reiniciar los campos."""
        self.actualizar()

    def _cambiar_playlist(self, _evento) -> None:
        """Guarde ID elegido y refresque entradas visibles."""
        self.playlist_id = int(self._selector.value)
        self.actualizar()

    def _id_playlist(self) -> int:
        """Exija selección antes de operar una playlist."""
        if self.playlist_id is None:
            raise ValueError("Primero crea y selecciona una playlist.")
        return self.playlist_id

    def _biblioteca(self, estado) -> list[ft.Control]:
        """Construya formulario adaptable y catálogo filtrado."""
        canciones = self.controlador.listar(self._filtro.value or "")
        return [
            ft.Text("Biblioteca", size=26, weight=ft.FontWeight.BOLD),
            ft.Text(
                f"{len(estado.canciones)} canciones · "
                f"{len(estado.playlists)} playlists · archivos locales"
            ),
            ft.Container(
                ft.Column(
                    [
                        ft.Text("Añadir una canción", size=18),
                        ft.ResponsiveRow(
                            [self._titulo, self._artista, self._duracion]
                        ),
                        self._boton("Agregar canción", self._agregar),
                    ]
                ),
                padding=18,
                bgcolor=PANEL,
                border_radius=16,
            ),
            self._filtro,
            self._selector,
            ft.Text(
                "La playlist seleccionada recibe las canciones que añadas."
            ),
            *(self._tarjeta(c) for c in canciones),
            *([] if canciones else [ft.Text("No hay canciones que mostrar.")]),
        ]

    def _tarjeta(self, cancion) -> ft.Container:
        """Muestre identidad, archivo y acciones de una canción."""
        cid = cancion.identificador
        return ft.Container(
            ft.Column(
                [
                    ft.Text(
                        cancion.titulo, size=20, weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        f"{cancion.artista} · "
                        f"{cancion.duracion_formateada()} · ID {cid}"
                    ),
                    ft.Text(
                        "Audio asociado" if cancion.archivo else "Sin audio",
                        color=ACENTO,
                    ),
                    ft.Row(
                        [
                            self._boton(
                                "Escuchar", lambda: self._escuchar(cancion)
                            ),
                            self._boton(
                                "A playlist",
                                lambda: self.controlador.agregar_entrada(
                                    self._id_playlist(), cid
                                ),
                            ),
                            self._boton(
                                "A cola FIFO",
                                lambda: self.controlador.solicitar(cid),
                            ),
                            self._boton(
                                "Dar prioridad", lambda: self._solicitar(cid)
                            ),
                            self._boton(
                                "Asociar audio",
                                lambda: self._elegir_audio(cid),
                            ),
                            self._boton(
                                "Eliminar", lambda: self._confirmar_baja(cid)
                            ),
                        ],
                        wrap=True,
                    ),
                ]
            ),
            bgcolor=PANEL,
            padding=18,
            border_radius=16,
        )

    def _agregar(self) -> None:
        """Envíe campos al controlador y límpielos solo si se insertó."""
        self._titulo.error_text = (
            None
            if (self._titulo.value or "").strip()
            else "Escribe un título."
        )
        self._artista.error_text = (
            None
            if (self._artista.value or "").strip()
            else "Escribe un artista."
        )
        try:
            valida = int(self._duracion.value or "") > 0
        except ValueError:
            valida = False
        self._duracion.error_text = (
            None if valida else "Usa segundos enteros positivos."
        )
        self.controlador.agregar(
            self._titulo.value or "",
            self._artista.value or "",
            self._duracion.value or "",
        )
        self._titulo.value = self._artista.value = self._duracion.value = ""
        self._avisar("Canción agregada. Puedes asociarle audio.")

    def _solicitar(self, cancion_id: int) -> None:
        """Convierta prioridad del campo y delegue solicitud destacada."""
        try:
            prioridad = int(self._prioridad.value or "")
        except ValueError as error:
            raise ValueError("Indica prioridad entera en Colas.") from error
        self.controlador.solicitar(cancion_id, prioridad)
        self._avisar(f"Solicitud con prioridad {prioridad} agregada.")

    def _playlists(self, estado) -> list[ft.Control]:
        """Muestre creación, bajas y apariciones de la playlist elegida."""
        playlist = next(
            (
                p
                for p in estado.playlists
                if p.identificador == self.playlist_id
            ),
            None,
        )
        canciones = {c.identificador: c for c in estado.canciones}
        controles = [
            ft.Text("Tus playlists", size=26),
            self._nombre,
            self._boton("Crear playlist", self._crear_playlist),
            self._selector,
        ]
        if playlist is None:
            return controles + [ft.Text("Crea tu primera playlist arriba.")]
        controles.extend(
            [
                ft.Row(
                    [
                        self._boton(
                            "Escuchar playlist", self._iniciar_playlist
                        ),
                        self._boton(
                            "Añadir turno",
                            lambda: self.controlador.agregar_turno(
                                self._id_playlist()
                            ),
                        ),
                        self._boton(
                            "Eliminar playlist", self._confirmar_playlist
                        ),
                    ],
                    wrap=True,
                ),
                ft.Text(
                    "Añade canciones desde Biblioteca. "
                    "Se permiten repeticiones."
                ),
            ]
        )
        for entrada in playlist.entradas:
            cancion = canciones[entrada.cancion_id]
            marca = "▶ " if entrada.identificador == playlist.actual_id else ""
            controles.append(
                ft.Container(
                    ft.Column(
                        [
                            ft.Text(
                                f"{marca}{cancion.titulo} · {cancion.artista}",
                                size=18,
                            ),
                            ft.Text(
                                f"Aparición {entrada.identificador} · "
                                f"canción {entrada.cancion_id}"
                            ),
                            ft.Row(
                                [
                                    self._boton(
                                        "Escuchar aquí",
                                        lambda eid=entrada.identificador: (
                                            self._entrada(eid)
                                        ),
                                    ),
                                    self._boton(
                                        "Quitar aparición",
                                        lambda eid=entrada.identificador: (
                                            self.controlador.borrar_entrada(
                                                self._id_playlist(), eid
                                            )
                                        ),
                                    ),
                                ],
                                wrap=True,
                            ),
                        ]
                    ),
                    padding=16,
                    bgcolor=PANEL,
                    border_radius=12,
                )
            )
        if not playlist.entradas:
            controles.append(ft.Text("Esta playlist está vacía."))
        return controles

    def _crear_playlist(self) -> None:
        """Cree playlist y seleccione su nueva identidad."""
        self.controlador.crear_playlist(self._nombre.value or "")
        foto = self.controlador.estado_vista()["estado"].playlists[-1]
        self.playlist_id = foto.identificador
        self._nombre.value = ""
        self._avisar("Playlist creada. Añade canciones desde Biblioteca.")

    def _colas(self, datos) -> list[ft.Control]:
        """Muestre modos de atención independientes y sus diagramas."""
        return [
            ft.Text("Solicitudes y turnos", size=26),
            ft.Text(
                "Encola canciones desde Biblioteca; "
                "aquí eliges cómo atenderlas."
            ),
            self._prioridad,
            self._selector,
            self._boton(
                "Añadir playlist a turnos",
                lambda: self.controlador.agregar_turno(self._id_playlist()),
            ),
            self._modo,
            self._boton("Atender y escuchar", self._atender),
            *visualizar(datos, self.playlist_id, solo_colas=True),
        ]

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

    async def _escuchar(self, cancion, origen="individual") -> None:
        """Reproduzca desde inicio o muestre error por archivo ausente."""
        await self._audio.reproducir(cancion.identificador, cancion.archivo)
        self._origen = origen
        self._continuar = origen != "individual"
        self._reproduccion.value = f"{cancion.titulo} · {cancion.artista}"

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

    async def _saltar(self, direccion: int) -> None:
        """Avance según origen; anterior solo está disponible en playlists."""
        if self._origen == "playlist":
            cancion = self.controlador.mover(self._playlist_audio, direccion)
            await self._escuchar(cancion, "playlist")
        elif (
            self._origen in ("fifo", "prioridad", "turnos") and direccion == 1
        ):
            await self._escuchar(
                self.controlador.consumir(self._origen), self._origen
            )
        else:
            raise ValueError(
                "Inicia una playlist o atiende una cola para navegar."
            )

    async def _atender(self) -> None:
        """Retire la próxima solicitud del modo elegido y reproduzca."""
        modo = self._modo.value
        await self._escuchar(self.controlador.consumir(modo), modo)

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

    async def _pausar(self) -> None:
        """Alterne pausa/reanudación mediante el adaptador asíncrono."""
        await self._audio.pausar_reanudar()

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

    def _notificar_audio(self, estado: str) -> None:
        """Muestre estado y segundos recibidos del servicio real de audio."""
        self._estado_audio.value = f"{estado} · {self._audio.posicion} s"
        if self._pagina:
            self._pagina.update()

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

    def _confirmar_carga(self) -> None:
        """Avise pérdida de cambios sin guardar antes del reemplazo."""
        self._confirmar(
            "Cargar guardado",
            "Reemplazará esta sesión y limpiará "
            "el historial. Se perderán los cambios sin guardar.",
            self._cargar,
        )

    async def _cargar(self) -> None:
        """Valide todo antes de reemplazar y detenga el audio anterior."""
        estado = await asyncio.to_thread(cargar, self.archivo_datos)
        await self._detener()
        self.controlador.importar(codificar(estado))
        self._version_disco = self._version_guardado()
        self._avisar("Biblioteca cargada correctamente.")

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

    async def _aplicar_importacion(self) -> None:
        """Aplique JSON validado con audio detenido e historial limpio."""
        await self._detener()
        self.controlador.importar(self._importacion)
        self._avisar("JSON importado. Pulsa Guardar para conservarlo aquí.")

    def _version_guardado(self) -> tuple[int, int] | None:
        """Observe fecha/tamaño para detectar escrituras de otra pestaña."""
        try:
            datos = self.archivo_datos.stat()
            return datos.st_mtime_ns, datos.st_size
        except FileNotFoundError:
            return None
