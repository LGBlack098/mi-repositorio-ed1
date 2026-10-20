"""Reproductor musical adaptable con diseño estilo Spotify y ficha local."""

import asyncio

import flet as ft

from services.ficha_audio import leer_ficha, peso_legible
from services.rutas_multimedia import fuente_multimedia
from views.vista_reproductor import (
    ACENTO,
    SUAVE,
    TEXTO,
    VistaReproductor,
    portada,
    reloj,
)

FONDO_SPOTIFY = "#121212"
NEGRO_LATERAL = "#09090B"
BARRA_INFERIOR = "#18181B"
FILA_ACTIVA = "#27272A"


class VistaSonoteca(VistaReproductor):
    """Presente el reproductor musical sin controles educativos visibles."""

    def __init__(self, controlador, directorio=None, archivo_datos=None):
        """Prepare componentes persistentes de navegación y reproducción."""
        super().__init__(controlador, directorio, archivo_datos)
        self._destinos = ("Biblioteca", "Playlists", "Siguientes")
        self._playlist_visible = None
        self._cola_abierta = False
        self._lateral.width = 220
        self._panel_actual.width = 280
        self._boton_cola = self._icono(
            ft.Icons.QUEUE_MUSIC,
            "Ver cola de reproducción",
            self._alternar_cola,
        )
        self._barra_movil = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(
                    icon=ft.Icons.LIBRARY_MUSIC, label="Mi música"
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.ALBUM, label="Playlists"
                ),
                ft.NavigationBarDestination(
                    icon=ft.Icons.QUEUE_MUSIC, label="Cola"
                ),
            ],
            bgcolor=BARRA_INFERIOR,
            on_change=self._cambiar_destino,
        )

    def _preparar_presentacion(self):
        """Configure los controles musicales antes del primer dibujo."""
        pagina = self._pagina
        pagina.title = "Sonoteca"
        pagina.bgcolor = FONDO_SPOTIFY
        self._lateral.bgcolor = NEGRO_LATERAL
        self._panel_actual.bgcolor = NEGRO_LATERAL
        self._play.width = self._play.height = 48
        self._dock_info.on_click = self._accion(self._ficha_actual)
        self._dock_info.tooltip = "Ver información del archivo"
        self._volumen_panel.controls.insert(0, self._boton_cola)
        self._barra_reproduccion.bgcolor = BARRA_INFERIOR
        self._contenido.spacing = 4
        pagina.on_keyboard_event = self._teclado

    async def _teclado(self, evento):
        """Aplique el historial con Ctrl+Z/Ctrl+Y y Cmd+Z en escritorio."""
        if not (evento.ctrl or evento.meta) or evento.alt:
            return
        tecla = evento.key.upper()
        if tecla == "Z":
            await self._accion(
                lambda: self.controlador.historial(evento.shift)
            )()
        elif tecla == "Y" and not evento.shift:
            await self._accion(lambda: self.controlador.historial(True))()

    def _alternar_cola(self):
        """Abra el panel lateral o la página de cola según el ancho."""
        if (self._pagina.width or 1280) >= 1250:
            self._cola_abierta = not self._cola_abierta
        else:
            self._navegar(
                "Biblioteca" if self.seccion == "Siguientes" else "Siguientes"
            )

    async def _ficha_actual(self):
        """Abra la información de la canción seleccionada desde la barra."""
        if self._seleccion is not None:
            await self._ficha(self._seleccion)

    def _icono(self, icono, texto, operacion):
        """Reserve un objetivo táctil mínimo de 48 por 48 puntos."""
        control = super()._icono(icono, texto, operacion)
        control.width = control.height = 48
        return control

    def _redimensionar(self, _evento=None):
        """Adapte paneles, barra móvil y controles en una sola pasada."""
        ancho = self._pagina.width or 1280
        movil = ancho < 720
        self._compacto = movil
        self._lateral.visible = ancho >= 1000
        self._tabs.visible = False
        self._pagina.navigation_bar = (
            self._barra_movil if ancho < 1000 else None
        )
        self._panel_actual.visible = ancho >= 1250
        self._volumen_panel.visible = True
        self._volumen_panel.width = 195 if ancho >= 850 else 48
        for control in self._volumen_panel.controls:
            control.visible = control is self._boton_cola or ancho >= 850
        self._repeticion.visible = ancho >= 600
        self._dock_info.width = 98 if movil else 235
        self._arte_actual.visible = not movil
        self._filtro.visible = True
        self._filtro.label = "Buscar" if movil else "Buscar en tu música"
        self._icono_cabecera.visible = not movil
        self._boton_importar.content = "Añadir" if movil else "Añadir música"
        self._boton_importar.height = 48
        self._centro_panel.padding = 12 if movil else 24
        self._central.spacing = 12 if movil else 20
        self._barra_reproduccion.padding = ft.Padding.symmetric(
            horizontal=12 if movil else 22, vertical=10
        )
        self._barra_reproduccion.content.spacing = 8 if movil else 22
        self._controles_transporte.controls[0].spacing = 4 if movil else 14
        self.actualizar()

    def _cambiar_destino(self, evento):
        """Abra la sección indicada por la navegación táctil inferior."""
        self.seccion = self._destinos[evento.control.selected_index]
        self.actualizar()

    def _menu_herramientas(self):
        """Ofrezca historial, respaldos y ajustes musicales."""
        return ft.PopupMenuButton(
            icon=ft.Icons.SETTINGS_OUTLINED,
            tooltip="Opciones de música",
            items=[
                self._item("Deshacer edición", self.controlador.historial),
                self._item(
                    "Rehacer edición", lambda: self.controlador.historial(True)
                ),
                self._item("Repetir lista", self._alternar_repeticion),
                self._item("Ajustar volumen", self._abrir_volumen),
                self._item("Crear respaldo", self._exportar),
                self._item("Restaurar respaldo", self._respaldo),
            ],
        )

    def _abrir_volumen(self):
        """Permita ajustar volumen en pantallas donde se oculta la barra."""
        self._pagina.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Volumen"),
                content=ft.Slider(
                    min=0,
                    max=1,
                    value=self._audio.audio.volume,
                    divisions=20,
                    on_change=self._volumen,
                ),
                actions=[self._boton("Listo", self._pagina.pop_dialog)],
            )
        )

    def actualizar(self):
        """Componga el reproductor evitando construir vistas por duplicado."""
        datos = self.controlador.estado_vista()
        estado = datos["estado"]
        ids = tuple(p.identificador for p in estado.playlists)
        if self.playlist_id not in ids:
            self.playlist_id = ids[0] if ids else None
        self._playlist_visible = next(
            (
                p
                for p in estado.playlists
                if p.identificador == self.playlist_id
            ),
            None,
        )
        self._sidebar.controls = [
            ft.Text("sonoteca", size=26, weight=ft.FontWeight.BOLD),
            ft.Text("MÚSICA LOCAL", size=10, color=SUAVE),
            ft.Container(height=20),
            self._boton(
                "Mi música",
                lambda: self._navegar("Biblioteca"),
                ft.Icons.LIBRARY_MUSIC,
            ),
            self._boton(
                "Playlists", lambda: self._navegar("Playlists"), ft.Icons.ALBUM
            ),
            self._boton(
                "Cola",
                lambda: self._navegar("Siguientes"),
                ft.Icons.QUEUE_MUSIC,
            ),
            ft.Container(height=20),
            ft.Row(
                [
                    ft.Text(
                        "TUS PLAYLISTS", expand=True, size=10, color=SUAVE
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
                    ft.Icons.PLAYLIST_PLAY,
                )
                for p in estado.playlists
            ),
        ]
        if self.seccion == "Biblioteca":
            self._contenido.controls = self._biblioteca(estado)
        elif self.seccion == "Playlists":
            self._contenido.controls = self._playlists(estado)
        elif self.seccion == "Lista":
            self._contenido.controls = self._lista(estado)
        elif self.seccion == "Siguientes":
            self._contenido.controls = self._siguientes(datos)
        else:
            self.seccion = "Biblioteca"
            self._contenido.controls = self._biblioteca(estado)
        self._panel_actual.content = (
            self._cola_lateral(datos)
            if self._cola_abierta
            else self._ahora(datos)
        )
        self._actualizar_controles()
        self._boton_cola.icon_color = (
            ACENTO
            if self.seccion == "Siguientes" or self._cola_abierta
            else TEXTO
        )
        self._boton_cola.tooltip = (
            "Cerrar cola de reproducción"
            if self._cola_abierta
            else "Ver cola de reproducción"
        )
        seccion = "Playlists" if self.seccion == "Lista" else self.seccion
        if seccion in self._destinos:
            self._barra_movil.selected_index = self._destinos.index(seccion)
        if self._pagina:
            self._pagina.update()

    def _biblioteca(self, estado):
        """Muestre cabecera limpia y listado numerado de canciones."""
        canciones = self.controlador.listar(self._filtro.value or "")
        total = sum(c.duracion_segundos for c in estado.canciones)
        return [
            ft.Row(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "Tu biblioteca",
                                size=30,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Text(
                                f"{len(estado.canciones)} canciones · "
                                f"{reloj(total)}",
                                color=SUAVE,
                            ),
                        ],
                        expand=True,
                    ),
                    self._icono(
                        ft.Icons.PLAY_CIRCLE_FILL,
                        "Reproducir todo",
                        self._reproducir_todo,
                    ),
                ]
            ),
            ft.Text("Tus canciones", size=14, color=SUAVE),
            ft.Divider(color="#27272A"),
            *(self._pista(c, i + 1) for i, c in enumerate(canciones)),
            *(
                []
                if canciones
                else [
                    ft.Container(height=20),
                    ft.Icon(
                        ft.Icons.LIBRARY_MUSIC_OUTLINED, size=56, color=SUAVE
                    ),
                    ft.Text(
                        "Añade tu música para empezar"
                        if not estado.canciones
                        else "No hay canciones con esa búsqueda.",
                        size=20,
                    ),
                ]
            ),
        ]

    def _hero(self, titulo, subtitulo):
        """Presente un encabezado compacto de playlist, sin promoción."""
        return ft.Container(
            ft.Column(
                [
                    ft.Text("PLAYLIST", size=11, color=SUAVE),
                    ft.Text(titulo, size=30, weight=ft.FontWeight.BOLD),
                    ft.Text(subtitulo, color=SUAVE),
                ],
                spacing=6,
            ),
            padding=ft.Padding.symmetric(vertical=12),
        )

    def _imagen(self, cancion, tamano):
        """Use carátula incrustada o arte predeterminado local."""
        if (
            cancion.portada
            and (self.archivos.assets / cancion.portada).is_file()
        ):
            return ft.Image(
                src=fuente_multimedia(self.archivos.assets, cancion.portada),
                width=tamano,
                height=tamano,
                fit=ft.BoxFit.COVER,
                border_radius=8,
            )
        return portada(cancion.identificador, tamano)

    def _es_pista_activa(self, cancion, entrada_id=None) -> bool:
        """Distinga la aparición reproducida dentro de su playlist."""
        if self._seleccion is None or (
            self._seleccion.identificador != cancion.identificador
        ):
            return False
        if entrada_id is None:
            return True
        playlist = self._playlist_visible
        return (
            self._origen == "playlist"
            and playlist is not None
            and playlist.identificador == self._playlist_audio
            and entrada_id == playlist.actual_id
        )

    def _pista(self, cancion, numero, entrada_id=None):
        """Dibuje fila estilo Spotify con número, portada y menú completo."""
        activa = self._es_pista_activa(cancion, entrada_id)
        operacion = (
            (lambda: self._entrada(entrada_id))
            if entrada_id is not None
            else (lambda: self._escuchar(cancion))
        )
        indice = ft.Text(
            "▶" if activa else str(numero),
            width=24,
            size=13,
            color=ACENTO if activa else SUAVE,
            text_align=ft.TextAlign.RIGHT,
        )
        menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_HORIZ,
            tooltip=f"Opciones de {cancion.titulo}",
            items=[
                self._item(
                    "Información del archivo", lambda: self._ficha(cancion)
                ),
                self._item(
                    "Reproducir después",
                    lambda: self._encolar(cancion, True),
                ),
                self._item(
                    "Añadir a la cola",
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
                            lambda: self._quitar_entrada(entrada_id),
                        )
                    ]
                    if entrada_id is not None
                    else []
                ),
                self._item(
                    "Cambiar archivo de audio",
                    lambda: self._elegir_audio(cancion.identificador),
                ),
                self._item(
                    "Quitar de mi música",
                    lambda: self._confirmar_baja(cancion.identificador),
                ),
            ],
        )
        return ft.Container(
            ft.Row(
                [
                    ft.Container(
                        indice,
                        width=32,
                        height=48,
                        alignment=ft.Alignment.CENTER,
                        tooltip=f"Reproducir {cancion.titulo}",
                    ),
                    self._imagen(cancion, 32 if self._compacto else 40),
                    ft.Column(
                        [
                            ft.Text(
                                cancion.titulo,
                                size=14,
                                weight=(
                                    ft.FontWeight.W_600
                                    if activa
                                    else ft.FontWeight.NORMAL
                                ),
                                color=ACENTO if activa else TEXTO,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                cancion.artista,
                                size=12,
                                color=SUAVE,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        expand=True,
                        spacing=2,
                    ),
                    ft.Text(
                        cancion.duracion_formateada(), size=12, color=SUAVE
                    ),
                    menu,
                ],
                spacing=10,
            ),
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            bgcolor=FILA_ACTIVA if activa else None,
            border_radius=8,
            on_click=self._accion(operacion),
        )

    async def _ficha(self, cancion):
        """Lea metadatos de canciones antiguas y muestre su identidad."""
        if cancion.archivo:
            self.archivos.comprobar(cancion.archivo)
            ficha = await asyncio.to_thread(
                leer_ficha,
                self.archivos.assets / cancion.archivo,
                cancion.nombre_archivo or cancion.archivo.split("/")[-1],
            )
            self.controlador.asociar_audio(
                cancion.identificador, cancion.archivo, **ficha
            )
            cancion = next(
                c
                for c in self.controlador.listar()
                if c.identificador == cancion.identificador
            )
        self._pagina.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Información del archivo"),
                content=ft.Column(
                    [
                        self._imagen(cancion, 150),
                        ft.Text(
                            cancion.titulo, size=20, weight=ft.FontWeight.BOLD
                        ),
                        ft.Text(cancion.artista, color=SUAVE),
                        ft.Text(f"ID de canción: {cancion.identificador}"),
                        ft.Text(
                            f"Archivo: {cancion.nombre_archivo or 'Sin datos'}"
                        ),
                        ft.Text(f"Tipo: {cancion.formato or 'Sin datos'}"),
                        ft.Text(f"Peso: {peso_legible(cancion.tamano_bytes)}"),
                        ft.Text(f"Duración: {cancion.duracion_formateada()}"),
                    ],
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                    width=300,
                ),
                actions=[self._boton("Cerrar", self._pagina.pop_dialog)],
            )
        )

    async def _reproducir(self, cancion):
        """Actualice carátula junto con el audio y los controles estables."""
        await super()._reproducir(cancion)
        self._arte_actual.content = self._imagen(cancion, 48)

    def _ahora(self, datos=None):
        """Combine canción actual y próximos temas en el lateral musical."""
        if datos is None:
            datos = self.controlador.estado_vista()
        canciones = {c.identificador: c for c in datos["estado"].canciones}
        prioritarias = tuple(p.dato for p in datos["prioridad"])
        en_cola = datos["fifo"]
        c = self._seleccion
        return ft.Column(
            [
                ft.Text("SONANDO AHORA", size=10, color=SUAVE),
                self._imagen(c, 204) if c else portada(0, 204),
                ft.Text(
                    c.titulo if c else "Elige una canción",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    c.artista if c else "Tu música te espera", color=SUAVE
                ),
                ft.Divider(height=24, color="#27272A"),
                *self._resumen_cola(
                    "REPRODUCIR DESPUÉS", prioritarias, canciones
                ),
                *self._resumen_cola("EN TU COLA", en_cola, canciones),
                *(
                    []
                    if prioritarias or en_cola
                    else [ft.Text("La cola está vacía", color=SUAVE)]
                ),
            ],
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
        )

    def _cola_lateral(self, datos):
        """Presente próximos temas en el espacio del panel derecho."""
        canciones = {c.identificador: c for c in datos["estado"].canciones}
        prioridad = tuple(p.dato for p in datos["prioridad"])
        normal = datos["fifo"]
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Tu cola", size=20, expand=True),
                        self._icono(
                            ft.Icons.CLOSE, "Cerrar cola", self._alternar_cola
                        ),
                    ]
                ),
                *self._resumen_cola(
                    "REPRODUCIR DESPUÉS", prioridad, canciones
                ),
                *self._resumen_cola("EN TU COLA", normal, canciones),
                *(
                    []
                    if prioridad or normal
                    else [ft.Text("La cola está vacía", color=SUAVE)]
                ),
                self._boton(
                    "Ver toda la cola", lambda: self._navegar("Siguientes")
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=12,
        )

    def _resumen_cola(self, titulo, ids, canciones):
        """Muestre un grupo musical sin exponer el tipo de estructura."""
        return (
            [
                ft.Text(titulo, size=10, color=SUAVE),
                *(
                    ft.Row(
                        [
                            self._imagen(canciones[cid], 32),
                            ft.Column(
                                [
                                    ft.Text(
                                        canciones[cid].titulo,
                                        size=13,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        canciones[cid].artista,
                                        size=11,
                                        color=SUAVE,
                                        max_lines=1,
                                    ),
                                ],
                                spacing=1,
                                expand=True,
                            ),
                        ],
                        spacing=8,
                    )
                    for cid in ids[:5]
                    if cid in canciones
                ),
            ]
            if ids
            else []
        )

    def _siguientes(self, datos):
        """Presente cola prioritaria, cola normal y turnos de playlists."""
        canciones = {c.identificador: c for c in datos["estado"].canciones}
        prioridad = [
            canciones[p.dato]
            for p in datos["prioridad"]
            if p.dato in canciones
        ]
        normal = [canciones[cid] for cid in datos["fifo"] if cid in canciones]
        controles = [
            ft.Text(
                "Cola de reproducción", size=30, weight=ft.FontWeight.BOLD
            ),
            ft.Text(
                "Lo que va a sonar después de la pista actual.", color=SUAVE
            ),
        ]
        if prioridad:
            controles.append(
                ft.Text("Reproducir después", size=16, color=ACENTO)
            )
            controles.extend(
                self._pista(c, i + 1) for i, c in enumerate(prioridad)
            )
        if normal:
            controles.append(
                ft.Text("Más adelante en la cola", size=16, color=SUAVE)
            )
            controles.extend(
                self._pista(c, len(prioridad) + i + 1)
                for i, c in enumerate(normal)
            )
        if not prioridad and not normal:
            controles.append(
                ft.Text(
                    "Añade canciones desde el menú (•••) de cada pista.",
                    color=SUAVE,
                )
            )
        controles.extend(
            [
                ft.Divider(height=30, color="#27272A"),
                ft.Text("Alternar playlists", size=22),
                ft.Text("Una canción de cada lista, por turnos.", color=SUAVE),
                ft.Row(
                    [
                        self._boton("Añadir playlist", self._elegir_turno),
                        self._boton("Iniciar turnos", self._iniciar_turnos),
                    ],
                    wrap=True,
                ),
                ft.Text(
                    " → ".join(
                        p.nombre
                        for pid in datos["turnos"]
                        for p in datos["estado"].playlists
                        if p.identificador == pid
                    )
                    or "Todavía no hay playlists en los turnos.",
                    color=SUAVE,
                ),
            ]
        )
        return controles

    def _elegir_turno(self):
        """Permita incorporar una playlist no vacía a los turnos."""
        listas = self.controlador.estado_vista()["estado"].playlists
        self._pagina.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Alternar playlists"),
                content=ft.Column(
                    [
                        self._boton(
                            p.nombre,
                            lambda pid=p.identificador: self._anadir_turno(
                                pid
                            ),
                        )
                        for p in listas
                        if p.entradas
                    ],
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                actions=[self._boton("Cerrar", self._pagina.pop_dialog)],
            )
        )

    def _anadir_turno(self, identificador):
        """Delegue el alta de turno y cierre el selector."""
        self.controlador.agregar_turno(identificador)
        self._pagina.pop_dialog()

    async def _iniciar_turnos(self):
        """Empiece por el frente y continúe usando la cola circular."""
        await self._escuchar(self.controlador.consumir("turnos"), "turnos")
