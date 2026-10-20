"""Experiencia musical: biblioteca, playlists y controles persistentes.

La clase reutiliza adaptadores de la vista base para archivos y
exposición, pero el flujo cotidiano se expresa en términos musicales.
"""

import asyncio
import inspect
import logging

import flet as ft

from services.ficha_audio import leer_ficha
from services.metadatos import leer_metadatos
from services.reproductor import Reproductor
from services.rutas_multimedia import fuente_multimedia
from views.vista_biblioteca import VistaBiblioteca
from views.visualizador import visualizar

FONDO = "#121212"
SUPERFICIE = "#181818"
TEXTO = "#F5F5F5"
SUAVE = "#A7A7A7"
ACENTO = "#1ED760"


def reloj(segundos: int | float) -> str:
    """Convierta segundos a minutos:segundos para el reproductor."""
    minutos, resto = divmod(max(0, int(segundos)), 60)
    return f"{minutos}:{resto:02d}"


def portada(semilla: int = 0, tamano: int = 160) -> ft.Container:
    """Dibuje arte abstracto local con gradientes, sin carátulas ficticias."""
    colores = (
        ("#65476D", "#CC896E"),
        ("#325A61", "#7CA69C"),
        ("#414E78", "#A17C9C"),
        ("#705B35", "#C2A274"),
    )
    return ft.Container(
        ft.Stack(
            [
                ft.Container(
                    width=tamano * 0.7,
                    height=tamano * 0.7,
                    border_radius=tamano,
                    bgcolor="#24000000",
                    right=-tamano * 0.14,
                    top=-tamano * 0.1,
                ),
                ft.Container(
                    width=tamano * 0.8,
                    height=tamano * 0.8,
                    border_radius=tamano,
                    border=ft.Border.all(1, "#50FFFFFF"),
                    left=-tamano * 0.24,
                    bottom=-tamano * 0.2,
                ),
                ft.Container(
                    ft.Icon(
                        ft.Icons.GRAPHIC_EQ,
                        size=tamano * 0.28,
                        color="#EAF5F0",
                    ),
                    alignment=ft.Alignment.CENTER,
                    expand=True,
                ),
            ]
        ),
        width=tamano,
        height=tamano,
        border_radius=max(8, tamano // 12),
        gradient=ft.LinearGradient(
            colors=colores[semilla % len(colores)],
            begin=ft.Alignment.TOP_LEFT,
            end=ft.Alignment.BOTTOM_RIGHT,
        ),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
    )


class VistaReproductor(VistaBiblioteca):
    """Mantenga la música como flujo principal y la exposición como apoyo.

    Reutiliza de VistaBiblioteca diálogos, respaldo y reglas de eventos.
    Modelo y controlador conservan sus estructuras manuales sin cambios.
    """

    def __init__(self, controlador, directorio=None, archivo_datos=None):
        """Prepare selección musical y controles estables entre canciones."""
        super().__init__(controlador, directorio, archivo_datos)
        self.seccion = "Biblioteca"
        self._seleccion = None
        self._contexto_id = None
        self._repetir = False
        self._compacto = False
        self._arrastrando = False
        self._importando = False
        self._mensaje.value = ""
        self._nombre.label = "Nombre de la playlist"
        self._filtro.label = "Buscar en tu música"
        self._filtro.border_radius = 24
        self._filtro.height = 44
        self._filtro.expand = True
        self._filtro.text_size = 13
        self._sidebar = ft.Column(
            expand=True, spacing=6, scroll=ft.ScrollMode.AUTO
        )
        self._lateral = ft.Container(width=200, bgcolor=FONDO, padding=20)
        self._central = ft.Column(expand=True, spacing=20)
        self._contenido = ft.Column(
            expand=True, scroll=ft.ScrollMode.AUTO, spacing=8
        )
        self._panel_actual = ft.Container(
            width=250, padding=22, bgcolor=SUPERFICIE
        )
        self._titulo_actual = ft.Text(
            "Nada sonando",
            size=14,
            weight=ft.FontWeight.W_600,
            max_lines=1,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self._artista_actual = ft.Text(
            "Elige una canción", color=SUAVE, size=12, max_lines=1
        )
        self._arte_actual = ft.Container(content=portada(0, 48))
        self._tiempo = ft.Text("0:00", color=SUAVE, size=11, width=34)
        self._total = ft.Text("0:00", color=SUAVE, size=11, width=34)
        self._progreso = ft.Slider(
            min=0,
            max=1,
            value=0,
            expand=True,
            disabled=True,
            active_color=ACENTO,
            inactive_color="#36353E",
            on_change_start=self._inicio_busqueda,
            on_change_end=self._accion(self._buscar_tiempo),
        )
        self._play = ft.IconButton(
            ft.Icons.PLAY_ARROW_ROUNDED,
            tooltip="Reproducir",
            bgcolor=ACENTO,
            icon_color=FONDO,
            icon_size=28,
            on_click=self._accion(self._pausar),
        )
        self._repeticion = ft.IconButton(
            ft.Icons.REPEAT,
            tooltip="Activar repetición",
            icon_color=SUAVE,
            on_click=self._accion(self._alternar_repeticion),
        )

    def montar(self, pagina: ft.Page) -> None:
        """Monte una ventana musical con barra de reproducción persistente."""
        self._pagina = pagina
        pagina.title = "Sonoteca"
        if getattr(pagina, "window", None) is not None:
            pagina.window.icon = str(self.archivos.assets / "sonoteca.ico")
        pagina.padding = 0
        pagina.bgcolor = FONDO
        pagina.theme_mode = ft.ThemeMode.DARK
        pagina.theme = ft.Theme(
            color_scheme_seed=ACENTO, font_family="Segoe UI"
        )
        pagina.on_resize = self._redimensionar
        self._audio = Reproductor(
            self.archivos, self._notificar_audio, self._fin_audio
        )
        self._picker_musica = ft.FilePicker(on_result=self._importar_musica)
        self._picker_audio = ft.FilePicker(on_result=self._archivo_audio)
        self._picker_json = ft.FilePicker(on_result=self._archivo_json)
        self._picker_guardar = ft.FilePicker()
        self._lateral.content = self._sidebar
        self._tabs = ft.Row(
            [
                self._boton("Mi música", lambda: self._navegar("Biblioteca")),
                self._boton(
                    "Mis playlists", lambda: self._navegar("Playlists")
                ),
                self._boton(
                    "A continuación", lambda: self._navegar("Siguientes")
                ),
            ],
            wrap=True,
        )
        self._icono_cabecera = ft.Image(
            src=fuente_multimedia(self.archivos.assets, "sonoteca.png"),
            width=26,
            height=26,
            fit=ft.BoxFit.CONTAIN,
            tooltip="Sonoteca",
        )
        self._boton_importar = self._importador()
        self._cabecera = ft.Row(
            [
                self._icono_cabecera,
                self._filtro,
                self._boton_importar,
                self._menu_herramientas(),
            ],
            spacing=12,
        )
        self._central.controls = [
            self._cabecera,
            self._tabs,
            self._mensaje,
            self._contenido,
        ]
        self._volumen_control = ft.Slider(
            min=0,
            max=1,
            value=self._audio.audio.volume,
            width=100,
            divisions=20,
            active_color=ACENTO,
            on_change=self._volumen,
        )
        self._volumen_panel = ft.Row(
            [
                ft.Icon(ft.Icons.VOLUME_UP_OUTLINED, size=18, color=SUAVE),
                self._volumen_control,
            ],
            width=145,
        )
        self._dock_info = ft.Container(
            ft.Row(
                [
                    self._arte_actual,
                    ft.Column(
                        [self._titulo_actual, self._artista_actual],
                        expand=True,
                        spacing=4,
                        tight=True,
                    ),
                ]
            ),
            width=235,
        )
        self._controles_transporte = ft.Column(
            [
                ft.Row(
                    [
                        self._icono(
                            ft.Icons.SKIP_PREVIOUS_ROUNDED,
                            "Anterior",
                            lambda: self._saltar(-1),
                        ),
                        self._play,
                        self._icono(
                            ft.Icons.SKIP_NEXT_ROUNDED,
                            "Siguiente",
                            lambda: self._saltar(1),
                        ),
                        self._repeticion,
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=14,
                ),
                ft.Row([self._tiempo, self._progreso, self._total], spacing=8),
            ],
            expand=True,
            spacing=0,
            tight=True,
        )
        self._centro_panel = ft.Container(
            self._central, padding=24, expand=True
        )
        self._barra_reproduccion = ft.Container(
            ft.Row(
                [
                    self._dock_info,
                    self._controles_transporte,
                    self._volumen_panel,
                ],
                spacing=22,
            ),
            bgcolor=SUPERFICIE,
            padding=ft.Padding.symmetric(horizontal=22, vertical=10),
            border=ft.Border(top=ft.BorderSide(1, "#303030")),
        )
        self._preparar_presentacion()
        pagina.add(
            ft.Column(
                [
                    ft.Row(
                        [
                            self._lateral,
                            self._centro_panel,
                            self._panel_actual,
                        ],
                        expand=True,
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.STRETCH,
                    ),
                    self._barra_reproduccion,
                ],
                expand=True,
                spacing=0,
            )
        )
        self._redimensionar()

    def _preparar_presentacion(self) -> None:
        """Permita personalizar controles antes de montarlos en la página."""

    def _icono(self, icono, texto, operacion) -> ft.IconButton:
        """Cree control musical por icono con tooltip accesible."""
        return ft.IconButton(
            icono,
            tooltip=texto,
            icon_color=TEXTO,
            on_click=self._accion(operacion),
        )

    def _importador(self, texto="Añadir música") -> ft.Button:
        """Abra selección múltiple por gesto cliente en web y escritorio."""
        return ft.Button(
            texto,
            icon=ft.Icons.ADD,
            color=FONDO,
            bgcolor=ACENTO,
            action=ft.PickFiles(
                self._picker_musica,
                allow_multiple=True,
                with_data=True,
                file_type=ft.FilePickerFileType.CUSTOM,
                allowed_extensions=["mp3", "wav", "flac", "ogg", "m4a"],
            ),
        )

    def _menu_herramientas(self) -> ft.PopupMenuButton:
        """Reúna respaldo y exposición sin ocupar la navegación musical."""
        return ft.PopupMenuButton(
            icon=ft.Icons.MORE_HORIZ,
            tooltip="Herramientas",
            items=[
                self._item(
                    "Vista académica", lambda: self._navegar("Académica")
                ),
                self._item(
                    "Deshacer edición", lambda: self.controlador.historial()
                ),
                self._item(
                    "Rehacer edición", lambda: self.controlador.historial(True)
                ),
                self._item("Crear respaldo", self._exportar),
                self._item("Restaurar respaldo", self._respaldo),
                self._item("Detener reproducción", self._detener),
            ],
        )

    def _item(self, texto, operacion) -> ft.PopupMenuItem:
        """Cree una acción secundaria con el mismo control de errores."""
        return ft.PopupMenuItem(
            content=texto, on_click=self._accion(operacion)
        )

    def _accion(self, operacion):
        """Serialice interacción y guarde ediciones sin un botón técnico."""

        async def ejecutar(_evento=None) -> None:
            """Conserve acciones y avise si fallan audio o guardado."""
            async with self._serial:
                antes = self.controlador.estado_vista()["estado"]
                try:
                    resultado = operacion()
                    if inspect.isawaitable(resultado):
                        await resultado
                    await self._validar_audio()
                    despues = self.controlador.estado_vista()["estado"]
                    if despues != antes:
                        await self._guardar_auto()
                    self.actualizar()
                except Exception as error:
                    logging.info("Acción musical no completada: %s", error)
                    self._arrastrando = False
                    self._avisar(
                        str(error) or "El dispositivo no respondió.", True
                    )
                    self.actualizar()

        return ejecutar

    async def _guardar_auto(self) -> None:
        """Persista cambios con la protección de concurrencia de la base."""
        if not self._pagina:
            return
        mensaje = self._mensaje.value
        await super()._guardar()
        self._mensaje.value = mensaje

    def _avisar(self, mensaje: str, error: bool = False) -> None:
        """Muestre avisos breves; el guardado automático permanece discreto."""
        self._mensaje.value = mensaje
        self._mensaje.color = "#F7A49D" if error else SUAVE
        self._mensaje.size = 12
        if self._pagina:
            self._pagina.update()

    def _redimensionar(self, _evento=None) -> None:
        """Mantenga el reproductor visible y adapte paneles al ancho."""
        ancho = self._pagina.width or 1280
        self._compacto = ancho < 720
        self._lateral.visible = ancho >= 1000
        self._tabs.visible = ancho < 1000
        self._panel_actual.visible = ancho >= 1250
        self._volumen_panel.visible = ancho >= 850
        self._repeticion.visible = ancho >= 520
        self._dock_info.width = 130 if self._compacto else 235
        self._arte_actual.visible = not self._compacto
        self._filtro.visible = ancho >= 520
        self.actualizar()

    def actualizar(self) -> None:
        """Componga la sección musical desde instantáneas sin exponer nodos."""
        datos = self.controlador.estado_vista()
        estado = datos["estado"]
        ids = tuple(p.identificador for p in estado.playlists)
        if self.playlist_id not in ids:
            self.playlist_id = ids[0] if ids else None
        self._sidebar.controls = [
            ft.Text(
                "sonoteca", size=28, weight=ft.FontWeight.BOLD, color=ACENTO
            ),
            ft.Text("TU MÚSICA, CONTIGO", color=SUAVE, size=9),
            ft.Container(height=30),
            self._boton(
                "Mi música",
                lambda: self._navegar("Biblioteca"),
                ft.Icons.LIBRARY_MUSIC_OUTLINED,
            ),
            self._boton(
                "A continuación",
                lambda: self._navegar("Siguientes"),
                ft.Icons.QUEUE_MUSIC,
            ),
            ft.Container(height=24),
            ft.Row(
                [
                    ft.Text(
                        "TUS PLAYLISTS", size=10, color=SUAVE, expand=True
                    ),
                    self._icono(
                        ft.Icons.ADD, "Crear playlist", self._nueva_playlist
                    ),
                ]
            ),
            *(
                self._boton(
                    p.nombre,
                    lambda pid=p.identificador: self._abrir_lista(pid),
                    ft.Icons.ALBUM_OUTLINED,
                )
                for p in estado.playlists
            ),
            *(
                []
                if ids
                else [
                    ft.Text(
                        "Un lugar para cada momento.", size=12, color=SUAVE
                    )
                ]
            ),
        ]
        if self.seccion == "Biblioteca":
            contenido = self._biblioteca(estado)
        elif self.seccion == "Playlists":
            contenido = self._playlists(estado)
        elif self.seccion == "Lista":
            contenido = self._lista(estado)
        elif self.seccion == "Siguientes":
            contenido = self._siguientes(datos)
        else:
            self._selector.options = [
                ft.DropdownOption(str(p.identificador), p.nombre)
                for p in estado.playlists
            ]
            self._selector.value = str(self.playlist_id) if ids else None
            contenido = [
                self._boton(
                    "Volver a mi música", lambda: self._navegar("Biblioteca")
                ),
                ft.Text("Vista académica", size=26),
                ft.Text(
                    "Implementación y estado interno para la exposición.",
                    color=SUAVE,
                ),
                self._selector,
                *super()._colas(datos),
                *visualizar(datos, self.playlist_id),
            ]
        self._contenido.controls = contenido
        self._panel_actual.content = self._ahora()
        self._actualizar_controles()
        if self._pagina and not getattr(self, "_diferir_refresco", False):
            self._pagina.update()

    def _biblioteca(self, estado) -> list:
        """Muestre una biblioteca de pistas con una sola acción principal."""
        canciones = self.controlador.listar(self._filtro.value or "")
        if not estado.canciones:
            return [
                self._hero(
                    "Tu música,\na tu ritmo.",
                    "Añade tus archivos y empieza a escuchar.",
                ),
                ft.Container(
                    ft.Column(
                        [
                            ft.Icon(
                                ft.Icons.LIBRARY_MUSIC_OUTLINED,
                                size=54,
                                color=SUAVE,
                            ),
                            ft.Text("Aquí empieza tu biblioteca", size=23),
                            ft.Text(
                                "Elige uno o varios archivos de música.\n"
                                "Leemos sus datos y los guardamos por ti.",
                                color=SUAVE,
                            ),
                            self._importador("Elegir canciones"),
                        ],
                        spacing=18,
                    ),
                    padding=30,
                ),
            ]
        segundos = sum(c.duracion_segundos for c in estado.canciones)
        return [
            self._hero(
                "Dale play\na tu día.",
                f"{len(estado.canciones)} canciones · "
                f"{reloj(segundos)} de música",
            ),
            ft.Row(
                [
                    ft.Text(
                        "Tus canciones",
                        size=22,
                        weight=ft.FontWeight.BOLD,
                        expand=True,
                    ),
                    self._boton(
                        "Reproducir todo",
                        self._reproducir_todo,
                        ft.Icons.PLAY_ARROW_ROUNDED,
                    ),
                ]
            ),
            ft.Divider(color="#282730"),
            *(self._pista(c, i + 1) for i, c in enumerate(canciones)),
            *(
                []
                if canciones
                else [ft.Text("No encontramos esa canción.", color=SUAVE)]
            ),
        ]

    def _hero(self, titulo: str, detalle: str) -> ft.Container:
        """Construya la cabecera musical con arte abstracto local."""
        return ft.Container(
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "TU COLECCIÓN PERSONAL",
                                size=10,
                                color="#DBC6D1",
                            ),
                            ft.Text(
                                titulo,
                                size=30 if self._compacto else 42,
                                weight=ft.FontWeight.BOLD,
                                color=TEXTO,
                            ),
                            ft.Text(detalle, color="#D7CBD4", size=12),
                        ],
                        expand=True,
                        spacing=12,
                    ),
                    portada(0, 110 if self._compacto else 160),
                ],
                spacing=12,
            ),
            padding=22 if self._compacto else 30,
            border_radius=20,
            gradient=ft.LinearGradient(colors=["#403244", "#242431"]),
            margin=ft.Margin.only(bottom=20),
        )

    def _pista(self, cancion, numero, entrada_id=None) -> ft.Container:
        """Dibuje una fila de música con acciones agrupadas en un menú."""
        activa = (
            self._seleccion is not None
            and self._seleccion.identificador == cancion.identificador
        )
        operacion = (
            (lambda: self._entrada(entrada_id))
            if entrada_id is not None
            else (lambda: self._escuchar(cancion))
        )
        return ft.Container(
            ft.Row(
                [
                    self._icono(
                        ft.Icons.PLAY_ARROW_ROUNDED,
                        f"Reproducir {cancion.titulo}",
                        operacion,
                    ),
                    portada(cancion.identificador, 38),
                    ft.Column(
                        [
                            ft.Text(
                                cancion.titulo,
                                size=14,
                                color=ACENTO if activa else TEXTO,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                cancion.artista,
                                size=12,
                                color=SUAVE,
                                max_lines=1,
                            ),
                        ],
                        expand=True,
                        spacing=3,
                    ),
                    ft.Text(
                        cancion.duracion_formateada(), size=12, color=SUAVE
                    ),
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_HORIZ,
                        tooltip=f"Opciones de {cancion.titulo}",
                        items=[
                            self._item(
                                "Reproducir después",
                                lambda: self._encolar(cancion, True),
                            ),
                            self._item(
                                "Añadir a continuación",
                                lambda: self._encolar(cancion),
                            ),
                            self._item(
                                "Añadir a una playlist",
                                lambda: self._elegir_lista(cancion),
                            ),
                            *(
                                [
                                    self._item(
                                        "Quitar de esta playlist",
                                        lambda: self._quitar_entrada(
                                            entrada_id
                                        ),
                                    )
                                ]
                                if entrada_id is not None
                                else []
                            ),
                            self._item(
                                "Cambiar archivo de audio",
                                lambda: self._elegir_audio(
                                    cancion.identificador
                                ),
                            ),
                            self._item(
                                "Quitar de mi música",
                                lambda: self._confirmar_baja(
                                    cancion.identificador
                                ),
                            ),
                        ],
                    ),
                ],
                spacing=12,
            ),
            padding=ft.Padding.symmetric(horizontal=6, vertical=6),
            bgcolor="#25212A" if activa else None,
            border_radius=10,
        )

    def _playlists(self, estado) -> list:
        """Presente playlists con acciones para crear y abrir."""
        return [
            ft.Row(
                [
                    ft.Text("Tus playlists", size=30, expand=True),
                    self._boton(
                        "Crear playlist", self._nueva_playlist, ft.Icons.ADD
                    ),
                ]
            ),
            ft.Text("Un lugar para cada momento.", color=SUAVE),
            *(
                ft.Container(
                    ft.Row(
                        [
                            portada(p.identificador, 76),
                            ft.Column(
                                [
                                    ft.Text(p.nombre, size=20),
                                    ft.Text(
                                        f"{len(p.entradas)} canciones",
                                        color=SUAVE,
                                    ),
                                ],
                                expand=True,
                            ),
                            self._boton(
                                "Abrir",
                                lambda pid=p.identificador: self._abrir_lista(
                                    pid
                                ),
                            ),
                        ]
                    ),
                    padding=14,
                    border_radius=14,
                    bgcolor=SUPERFICIE,
                )
                for p in estado.playlists
            ),
            *(
                []
                if estado.playlists
                else [
                    ft.Text(
                        "Crea una playlist y añade tus favoritas.", color=SUAVE
                    )
                ]
            ),
        ]

    def _abrir_lista(self, identificador: int) -> None:
        """Seleccione playlist por ID y muestre sus pistas."""
        self.playlist_id = identificador
        self.seccion = "Lista"

    def _lista(self, estado) -> list:
        """Muestre playlist y conserve la identidad de cada aparición."""
        playlist = next(
            (
                p
                for p in estado.playlists
                if p.identificador == self.playlist_id
            ),
            None,
        )
        if playlist is None:
            return self._playlists(estado)
        canciones = {c.identificador: c for c in estado.canciones}
        return [
            self._hero(
                playlist.nombre,
                f"PLAYLIST · {len(playlist.entradas)} canciones",
            ),
            ft.Row(
                [
                    self._boton(
                        "Reproducir",
                        self._iniciar_playlist,
                        ft.Icons.PLAY_ARROW_ROUNDED,
                    ),
                    self._boton(
                        "Añadir canciones",
                        lambda: self._navegar("Biblioteca"),
                        ft.Icons.ADD,
                    ),
                    ft.PopupMenuButton(
                        icon=ft.Icons.MORE_HORIZ,
                        tooltip="Opciones de playlist",
                        items=[
                            self._item(
                                "Eliminar playlist", self._confirmar_playlist
                            )
                        ],
                    ),
                ]
            ),
            *(
                self._pista(canciones[e.cancion_id], i + 1, e.identificador)
                for i, e in enumerate(playlist.entradas)
            ),
            *(
                []
                if playlist.entradas
                else [
                    ft.Text(
                        "Busca una canción y usa Añadir a una playlist.",
                        color=SUAVE,
                    )
                ]
            ),
        ]

    def _nueva_playlist(self) -> None:
        """Abra un diálogo breve; el formulario no ocupa la biblioteca."""
        self._nombre.value = ""
        self._pagina.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Nueva playlist"),
                content=self._nombre,
                actions=[
                    self._boton("Cancelar", self._pagina.pop_dialog),
                    self._boton("Crear", self._crear_playlist),
                ],
            )
        )

    def _crear_playlist(self) -> None:
        """Valide, cree y abra playlist; guarde desde el manejador común."""
        self.controlador.crear_playlist(self._nombre.value or "")
        self.playlist_id = (
            self.controlador.estado_vista()["estado"]
            .playlists[-1]
            .identificador
        )
        self.seccion = "Lista"
        self._pagina.pop_dialog()
        self._avisar("Playlist creada.")

    def _elegir_lista(self, cancion) -> None:
        """Ofrezca destinos explícitos para añadir una canción."""
        playlists = self.controlador.estado_vista()["estado"].playlists
        self._pagina.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Añadir a una playlist"),
                content=ft.Column(
                    [
                        *(
                            self._boton(
                                p.nombre,
                                lambda pid=p.identificador: self._anadir_lista(
                                    pid, cancion
                                ),
                            )
                            for p in playlists
                        ),
                        *(
                            []
                            if playlists
                            else [
                                ft.Text("Crea una playlist en Mis playlists.")
                            ]
                        ),
                    ],
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                actions=[self._boton("Cerrar", self._pagina.pop_dialog)],
            )
        )

    def _anadir_lista(self, playlist_id, cancion) -> None:
        """Añada una aparición y cierre el selector de destino."""
        self.controlador.agregar_entrada(playlist_id, cancion.identificador)
        self._pagina.pop_dialog()
        self._avisar(f"{cancion.titulo} añadida a la playlist.")

    def _quitar_entrada(self, entrada_id) -> None:
        """Retire una aparición conservando el archivo y la biblioteca."""
        self.controlador.borrar_entrada(self._id_playlist(), entrada_id)
        self._avisar("Canción quitada de la playlist.")

    def _encolar(self, cancion, inmediata=False) -> None:
        """Use prioridad para después y FIFO para el resto de siguientes."""
        self.controlador.solicitar(
            cancion.identificador, 10 if inmediata else None
        )
        self._avisar(
            "Sonará después." if inmediata else "Añadida a continuación."
        )

    def _siguientes(self, datos) -> list:
        """Muestre las próximas canciones en su orden de reproducción."""
        canciones = {c.identificador: c for c in datos["estado"].canciones}
        ids = tuple(p.dato for p in datos["prioridad"]) + datos["fifo"]
        return [
            ft.Text("A continuación", size=30),
            ft.Text("Lo que va a sonar después de esta canción.", color=SUAVE),
            *(self._pista(canciones[cid], i + 1) for i, cid in enumerate(ids)),
            *(
                []
                if ids
                else [
                    ft.Text(
                        "Añade canciones desde el menú de cada pista.",
                        color=SUAVE,
                    )
                ]
            ),
        ]

    def _ahora(self) -> ft.Column:
        """Muestre el tema actual en un panel musical, sin datos académicos."""
        c = self._seleccion
        return ft.Column(
            [
                ft.Text("SONANDO AHORA", size=10, color=SUAVE),
                ft.Container(height=18),
                portada(c.identificador if c else 0, 204),
                ft.Container(height=14),
                ft.Text(
                    c.titulo if c else "Tu próximo favorito",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    c.artista if c else "Está en tu biblioteca.", color=SUAVE
                ),
                ft.Container(height=22),
                ft.Icon(ft.Icons.GRAPHIC_EQ, color=ACENTO, size=32),
                ft.Text(
                    "Archivos locales · Sin interrupciones",
                    color=SUAVE,
                    size=11,
                ),
            ],
            spacing=10,
        )

    async def _reproducir_todo(self) -> None:
        """Inicie la primera pista con archivo de la biblioteca."""
        cancion = next(
            (c for c in self.controlador.listar() if c.archivo), None
        )
        if cancion is None:
            raise ValueError("Añade un archivo de música para empezar.")
        await self._escuchar(cancion)

    async def _reproducir(self, cancion) -> None:
        """Abra audio sin cambiar el contexto que continuará después."""
        await self._audio.reproducir(cancion.identificador, cancion.archivo)
        self._seleccion = cancion
        self._titulo_actual.value = cancion.titulo
        self._artista_actual.value = cancion.artista
        self._arte_actual.content = portada(cancion.identificador, 48)

    async def _escuchar(self, cancion, origen="biblioteca") -> None:
        """Reproduzca desde biblioteca o playlist y conserve su posición."""
        await self._reproducir(cancion)
        self._contexto_id = cancion.identificador
        self._origen = origen
        self._continuar = True

    async def _saltar(self, direccion: int) -> None:
        """Atienda siguientes, luego continúe biblioteca o playlist activa."""
        paso = self.controlador.navegar(
            self._origen,
            self._contexto_id,
            self._playlist_audio,
            direccion,
            self._repetir,
        )
        if paso.cancion is None:
            await self._detener()
            return
        self._contexto_id = paso.contexto_id
        await self._reproducir(paso.cancion)

    async def _pausar(self) -> None:
        """Pause, reanude o inicie la selección cuando todavía no suena."""
        if self._audio.actual_id is None:
            if self._seleccion:
                await self._escuchar(self._seleccion, self._origen)
            else:
                await self._reproducir_todo()
        else:
            await self._audio.pausar_reanudar()

    def _alternar_repeticion(self) -> None:
        """Active vuelta al inicio de biblioteca o anillo de playlist."""
        self._repetir = not self._repetir

    def _inicio_busqueda(self, _evento) -> None:
        """Suspenda el refresco de progreso mientras se arrastra el control."""
        self._arrastrando = True

    async def _buscar_tiempo(self) -> None:
        """Busque la posición elegida por el usuario en segundos reales."""
        try:
            await self._audio.buscar_posicion(self._progreso.value)
        finally:
            self._arrastrando = False

    def _notificar_audio(self, estado: str) -> None:
        """Refresque solo controles persistentes al recibir posición/estado."""
        self._estado_audio.value = estado
        self._actualizar_controles()
        if self._pagina:
            self._pagina.update()

    def _actualizar_controles(self) -> None:
        """Refresque play/pausa y progreso sin reconstruir las pistas."""
        if not self._audio:
            return
        reproduciendo = (
            self._audio.actual_id is not None and not self._audio.pausado
        )
        self._play.icon = (
            ft.Icons.PAUSE_ROUNDED
            if reproduciendo
            else ft.Icons.PLAY_ARROW_ROUNDED
        )
        self._play.tooltip = "Pausar" if reproduciendo else "Reproducir"
        duracion = (
            self._audio.duracion or self._seleccion.duracion_segundos
            if self._seleccion
            else 0
        )
        self._progreso.max = max(1, duracion)
        self._progreso.disabled = self._audio.actual_id is None
        if not self._arrastrando:
            self._progreso.value = min(
                self._audio.posicion, self._progreso.max
            )
        self._tiempo.value = reloj(self._audio.posicion)
        self._total.value = reloj(duracion)
        self._repeticion.icon_color = ACENTO if self._repetir else SUAVE
        self._repeticion.tooltip = (
            "Desactivar repetición" if self._repetir else "Activar repetición"
        )

    async def _importar_musica(self, evento) -> None:
        """Importe varios archivos con metadatos y guardado automático."""
        if not evento.files or self._importando:
            return
        self._importando = True

        async def importar() -> None:
            """Valide cada archivo; conserve los correctos si otro falla."""
            errores = []
            cantidad = 0
            for archivo in evento.files:
                try:
                    ruta = await asyncio.to_thread(
                        self.archivos.importar,
                        archivo.name,
                        archivo.bytes,
                        archivo.path,
                    )
                    titulo, artista, duracion = await asyncio.to_thread(
                        leer_metadatos,
                        self.archivos.assets / ruta,
                        archivo.name,
                    )
                    ficha = await asyncio.to_thread(
                        leer_ficha, self.archivos.assets / ruta, archivo.name
                    )
                    self.controlador.agregar(
                        titulo, artista, str(duracion), ruta, **ficha
                    )
                    cantidad += 1
                except (ValueError, OSError) as error:
                    errores.append(f"{archivo.name}: {error}")
            self.seccion = "Biblioteca"
            mensaje = (
                f"{cantidad} canciones añadidas."
                if cantidad
                else "No se añadió música."
            )
            if errores:
                mensaje += (
                    f" {len(errores)} no se pudieron importar. " + errores[0]
                )
            self._avisar(mensaje, bool(errores))

        try:
            await self._accion(importar)()
        finally:
            self._importando = False

    def _respaldo(self) -> None:
        """Abra restauración voluntaria desde las herramientas secundarias."""
        self._pagina.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Restaurar biblioteca"),
                content=ft.Text(
                    "Elige un respaldo. Confirma antes de restaurar."
                ),
                actions=[
                    self._boton("Cancelar", self._pagina.pop_dialog),
                    ft.Button(
                        "Elegir respaldo",
                        action=ft.PickFiles(
                            self._picker_json,
                            with_data=True,
                            allow_multiple=False,
                            file_type=ft.FilePickerFileType.CUSTOM,
                            allowed_extensions=["json"],
                        ),
                    ),
                ],
            )
        )

    async def _archivo_json(self, evento) -> None:
        """Cierre selección antes de confirmar restauración del respaldo."""
        if evento.files:
            self._pagina.pop_dialog()
        await super()._archivo_json(evento)

    async def _aplicar_importacion(self) -> None:
        """Restaure metadatos validados; la acción persiste los cambios."""
        await self._detener()
        self.controlador.importar(self._importacion)
        self._avisar("Biblioteca restaurada.")
