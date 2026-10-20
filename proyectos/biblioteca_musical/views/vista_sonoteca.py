"""Reproductor musical adaptable con ficha de archivos y panel técnico."""

import asyncio

import flet as ft

from services.experimento import comparar
from services.ficha_audio import leer_ficha, peso_legible
from services.rutas_multimedia import fuente_multimedia
from views.recorrido_circular import RecorridoCircular
from views.vista_reproductor import (
    SUAVE,
    SUPERFICIE,
    VistaReproductor,
    portada,
    reloj,
)
from views.visualizador import visualizar


class VistaSonoteca(VistaReproductor):
    """Presente música como experiencia principal y análisis por separado."""

    def __init__(self, controlador, directorio=None, archivo_datos=None):
        """Prepare componentes que se mantienen entre actualizaciones."""
        super().__init__(controlador, directorio, archivo_datos)
        self._anillo = RecorridoCircular()
        self._medida = ft.Text()
        self._latencia = ft.Text()
        self._memoria = ft.Column(spacing=5)
        self._resultado = ft.Column(spacing=8)
        self._benchmark_activo = False
        self._tarea_metricas = None
        self._destinos = ("Biblioteca", "Playlists", "Siguientes")
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
            bgcolor=SUPERFICIE,
            on_change=self._cambiar_destino,
        )

    def montar(self, pagina):
        """Monte la experiencia musical y el muestreo en segundo plano."""
        super().montar(pagina)
        pagina.title = "Sonoteca · Música local"
        self._play.width = self._play.height = 48
        self._estado_audio.size = 11
        self._estado_audio.color = SUAVE
        self._dock_info.content.controls[1].controls.append(self._estado_audio)
        if hasattr(pagina, "run_task"):
            self._tarea_metricas = pagina.run_task(self._pulso_metricas)
            pagina.on_disconnect = self._desconectar
            pagina.on_connect = self._reconectar

    def _desconectar(self, _evento):
        """Cancele el muestreo al desconectarse el cliente."""
        if self._tarea_metricas:
            self._tarea_metricas.cancel()

    def _reconectar(self, _evento):
        """Reanude un único muestreo al recuperar la conexión."""
        if self._tarea_metricas is None or self._tarea_metricas.done():
            self._tarea_metricas = self._pagina.run_task(self._pulso_metricas)

    def _icono(self, icono, texto, operacion):
        """Reserve un objetivo táctil mínimo de 48 por 48 puntos."""
        control = super()._icono(icono, texto, operacion)
        control.width = control.height = 48
        return control

    def _redimensionar(self, evento=None):
        """Adapte navegación, búsqueda y controles para teléfono."""
        super()._redimensionar(evento)
        ancho = self._pagina.width or 1280
        movil = ancho < 720
        self._tabs.visible = False
        self._pagina.navigation_bar = (
            self._barra_movil if ancho < 1000 else None
        )
        self._dock_info.width = 98 if movil else 235
        self._filtro.visible = True
        self._filtro.label = "Buscar" if movil else "Buscar en tu música"
        cabecera = self._central.controls[0].controls
        cabecera[0].visible = not movil
        cabecera[2].content = "Añadir" if movil else "Añadir música"
        cabecera[2].height = 48
        self._pagina.update()

    def _cambiar_destino(self, evento):
        """Abra la sección indicada por la navegación táctil inferior."""
        self.seccion = self._destinos[evento.control.selected_index]
        self.actualizar()

    def _menu_herramientas(self):
        """Ofrezca opciones musicales y acceso secundario a diagnóstico."""
        return ft.PopupMenuButton(
            icon=ft.Icons.MORE_HORIZ,
            tooltip="Más opciones",
            items=[
                self._item("Repetir lista", self._alternar_repeticion),
                self._item("Volumen", self._abrir_volumen),
                self._item("Deshacer edición", self.controlador.historial),
                self._item(
                    "Rehacer edición", lambda: self.controlador.historial(True)
                ),
                self._item("Crear respaldo", self._exportar),
                self._item("Restaurar respaldo", self._respaldo),
                self._item("Panel técnico", lambda: self._navegar("Tecnica")),
            ],
        )

    def _abrir_volumen(self):
        """Permita ajustar volumen también cuando se oculta su barra."""
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
        """Refresque música; construya diagramas solo en el panel técnico."""
        self._diferir_refresco = True
        try:
            super().actualizar()
        finally:
            self._diferir_refresco = False
        datos = self.controlador.estado_vista()
        estado = datos["estado"]
        self._sidebar.controls = [
            ft.Text("sonoteca", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("MÚSICA LOCAL", size=10, color=SUAVE),
            ft.Container(height=24),
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
            ft.Container(height=24),
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
        if self.seccion == "Tecnica":
            self._contenido.controls = self._tecnica(datos)
            self._refrescar_metricas()
        seccion = "Playlists" if self.seccion == "Lista" else self.seccion
        if seccion in self._destinos:
            self._barra_movil.selected_index = self._destinos.index(seccion)
        if self._pagina:
            self._pagina.update()

    def _biblioteca(self, estado):
        """Muestre canciones y búsqueda sin un banner que reste espacio."""
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
            ft.Text("Tus canciones", size=16, color=SUAVE),
            ft.Divider(color="#282730"),
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
                spacing=8,
            ),
            padding=ft.Padding.symmetric(vertical=16),
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

    def _pista(self, cancion, numero, entrada_id=None):
        """Complete cada pista con carátula y acceso a su ficha real."""
        control = super()._pista(cancion, numero, entrada_id)
        fila = control.content.controls
        fila[1] = self._imagen(cancion, 38)
        fila[-1].items.insert(
            0,
            self._item(
                "Información del archivo", lambda: self._ficha(cancion)
            ),
        )
        return control

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

    def _ahora(self):
        """Combine canción actual y próximos temas en el lateral musical."""
        datos = self.controlador.estado_vista()
        canciones = {c.identificador: c for c in datos["estado"].canciones}
        ids = tuple(p.dato for p in datos["prioridad"]) + datos["fifo"]
        c = self._seleccion
        return ft.Column(
            [
                ft.Text("SONANDO AHORA", size=10, color=SUAVE),
                self._imagen(c, 204) if c else portada(0, 204),
                ft.Text(
                    c.titulo if c else "Elige una canción",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    c.artista if c else "Tu música te espera", color=SUAVE
                ),
                ft.Divider(height=28, color="#303039"),
                ft.Text("A CONTINUACIÓN", size=10, color=SUAVE),
                *(ft.Text(canciones[cid].titulo, size=13) for cid in ids[:5]),
                *([] if ids else [ft.Text("La cola está vacía", color=SUAVE)]),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
        )

    def _siguientes(self, datos):
        """Añada alternancia de playlists al orden de próximas canciones."""
        controles = super()._siguientes(datos)
        controles.extend(
            [
                ft.Divider(height=30),
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

    def _tecnica(self, datos):
        """Reúna métricas, recorrido y diagramas fuera del flujo musical."""
        listas = datos["estado"].playlists
        self._selector.options = [
            ft.DropdownOption(str(p.identificador), p.nombre) for p in listas
        ]
        self._selector.value = str(self.playlist_id) if listas else None
        foto = next(
            (p for p in listas if p.identificador == self.playlist_id), None
        )
        return [
            ft.Text("Panel técnico", size=28, weight=ft.FontWeight.BOLD),
            ft.Text("Mediciones de esta sesión", color=SUAVE),
            self._medida,
            self._latencia,
            ft.Text("Memoria superficial de nodos", size=18),
            self._memoria,
            ft.Text(
                "Excluye canciones, audios, imágenes e instantáneas. "
                "No representa la RAM total del proceso.",
                color=SUAVE,
            ),
            self._boton("Comparar O(1) y O(n)", self._comparar),
            self._resultado,
            ft.Divider(height=24),
            ft.Text("Recorrido circular de playlist", size=22),
            self._selector,
            ft.Text(
                "Cada bloque identifica una aparición. ⇄ muestra ambos "
                "sentidos; el último enlaza al primero.",
                color=SUAVE,
            ),
            ft.Row(
                [self._anillo.actualizar(foto, self._pagina)],
                scroll=ft.ScrollMode.AUTO,
            )
            if foto
            else ft.Text("Crea una playlist para visualizar su recorrido."),
            ft.Row(
                [
                    self._boton("Anterior", lambda: self._mover_cursor(-1)),
                    self._boton("Siguiente", lambda: self._mover_cursor(1)),
                ]
            ),
            ft.Text(
                "Mover el cursor: O(1). Resolver playlist/canción: "
                "O(p+n). El dibujo se calcula después.",
                color=SUAVE,
            ),
            *visualizar(datos, self.playlist_id),
        ]

    def _mover_cursor(self, direccion):
        """Mueva el cursor real sin iniciar ni simular reproducción."""
        self.controlador.mover(self._id_playlist(), direccion)

    def _refrescar_metricas(self):
        """Actualice tasas observadas, latencia y bytes medidos en Python."""
        datos = self.controlador.metricas.resumen()
        self._medida.value = (
            f"{datos['acciones_s']:.2f} acciones/s · "
            f"{datos['muestras']} acciones en {datos['ventana_s']:.1f} s"
        )
        ultima = datos["ultima"]
        self._latencia.value = (
            f"{ultima.accion}: {ultima.segundos * 1000:.3f} ms · "
            f"{'correcta' if ultima.exito else 'fallida'}"
            if ultima
            else "Todavía no hay acciones medidas."
        )
        self._memoria.controls = [
            ft.Text(
                f"{nombre}: {cantidad} nodos · {tamano} B · "
                + (
                    f"{tamano / cantidad:.1f} B/nodo"
                    if cantidad
                    else "sin nodos"
                ),
                size=12,
            )
            for nombre, cantidad, tamano in self.controlador.memoria()
        ]

    async def _pulso_metricas(self):
        """Refresque cada segundo mientras la página siga conectada."""
        try:
            while True:
                await asyncio.sleep(1)
                if self.seccion == "Tecnica":
                    self._refrescar_metricas()
                    self._pagina.update()
        except (asyncio.CancelledError, RuntimeError):
            return

    async def _comparar(self):
        """Mida lotes de operaciones en un hilo sin cambiar la biblioteca."""
        if self._benchmark_activo:
            return
        self._benchmark_activo = True
        try:
            resultados = await asyncio.to_thread(comparar)
            self._resultado.controls = [
                ft.Text(
                    "Mediana de 5 lotes × 100 operaciones. Inserción "
                    "incluye crear nodo; búsqueda usa dato ausente.",
                    color=SUAVE,
                ),
                *(
                    ft.Text(
                        f"n={n} · insertar O(1): {insertar:.0f} ns/op · "
                        f"buscar O(n): {buscar:.0f} ns/op · "
                        f"{1e9 / max(buscar, 1):.0f} búsquedas/s"
                    )
                    for n, insertar, buscar in resultados
                ),
                ft.Text(
                    "Resultados locales: el ruido del equipo afecta los "
                    "tiempos; la teoría se justifica por el algoritmo.",
                    color=SUAVE,
                ),
            ]
        finally:
            self._benchmark_activo = False
