"""Recorrido animado del cursor real de una playlist circular doble."""

import asyncio
import math

import flet as ft


class RecorridoCircular:
    """Dibuje todas las apariciones y ambos sentidos del cierre circular."""

    def __init__(self):
        """Prepare un marcador persistente para animar sin alterar nodos."""
        self.pista = ft.Stack(width=400, height=350)
        self.marcador = ft.Container(
            ft.Icon(ft.Icons.PLAY_ARROW, color="#101015", size=18),
            width=24,
            height=24,
            border_radius=12,
            bgcolor="#EFC689",
        )
        self.clave = None
        self.indice = None
        self.generacion = 0
        self._tarea = None

    def punto(self, indice, cantidad):
        """Sitúe un nodo o marcador en una elipse mediante su índice."""
        angulo = -math.pi / 2 + 2 * math.pi * indice / cantidad
        return 180 + 150 * math.cos(angulo), 150 + 115 * math.sin(angulo)

    def actualizar(self, foto, pagina=None):
        """Sincronice identidades y anime solo transiciones del cursor."""
        entradas = foto.entradas
        clave = (foto.identificador, tuple(e.identificador for e in entradas))
        if not entradas:
            self.generacion += 1
            self.clave, self.indice = clave, None
            self.pista.controls = [ft.Text("Playlist vacía · actual = None")]
            return self.pista
        indice = next(
            i
            for i, e in enumerate(entradas)
            if e.identificador == foto.actual_id
        )
        if clave != self.clave:
            self.generacion += 1
            self.clave = clave
            self.pista.controls = []
            for i, entrada in enumerate(entradas):
                x, y = self.punto(i, len(entradas))
                self.pista.controls.append(
                    ft.Container(
                        ft.Text(f"#{entrada.identificador}", size=12),
                        left=x,
                        top=y,
                        width=48,
                        height=36,
                        bgcolor="#293549",
                        border_radius=8,
                        alignment=ft.Alignment.CENTER,
                        tooltip=f"Aparición {entrada.identificador}, "
                        f"canción {entrada.cancion_id}",
                    )
                )
                x, y = self.punto(i + 0.5, len(entradas))
                self.pista.controls.append(
                    ft.Text(
                        "⇄",
                        left=x,
                        top=y,
                        color="#9ABBAF",
                        size=20,
                    )
                )
            self.pista.controls.append(self.marcador)
            self.indice = indice
            self.marcador.left, self.marcador.top = self.punto(
                indice, len(entradas)
            )
            self.marcador.top -= 24
        elif self.indice != indice:
            anterior = self.indice
            self.indice = indice
            self.generacion += 1
            version = self.generacion
            if pagina and hasattr(pagina, "run_task"):
                self._tarea = pagina.run_task(
                    self._animar, anterior, indice, len(entradas), version
                )
            else:
                self.marcador.left, self.marcador.top = self.punto(
                    indice, len(entradas)
                )
                self.marcador.top -= 24
        return self.pista

    async def _animar(self, anterior, nuevo, cantidad, version):
        """Interpole sobre el arco e invalide animaciones anteriores."""
        salto = (nuevo - anterior) % cantidad
        if salto > cantidad / 2:
            salto -= cantidad
        for paso in range(1, 13):
            if version != self.generacion:
                return
            x, y = self.punto(anterior + salto * paso / 12, cantidad)
            self.marcador.left, self.marcador.top = x, y - 24
            try:
                self.marcador.update()
            except (RuntimeError, AssertionError):
                return
            await asyncio.sleep(0.025)
