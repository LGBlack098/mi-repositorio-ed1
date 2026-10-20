"""Regresiones de la experiencia musical sin paneles educativos."""

import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import flet as ft

from demo import crear_demo
from views.vista_reproductor import VistaReproductor
from views.vista_sonoteca import VistaSonoteca


def recorrer(control):
    """Recorra controles, incluidos los contenidos de menús cerrados."""
    yield control
    contenido = getattr(control, "content", None)
    if isinstance(contenido, ft.Control):
        yield from recorrer(contenido)
    for atributo in ("controls", "items"):
        for hijo in getattr(control, atributo, ()):
            yield from recorrer(hijo)


def textos(control):
    """Obtenga textos de una sección para comprobar su contenido."""
    valores = []
    for hijo in recorrer(control):
        if isinstance(hijo, ft.Text):
            valores.append(hijo.value or "")
        contenido = getattr(hijo, "content", None)
        if isinstance(contenido, str):
            valores.append(contenido)
    return "\n".join(valores)


class TestSonoteca(unittest.IsolatedAsyncioTestCase):
    """Pruebe interacciones con controles reales y audio simulado."""

    def montar(self, ancho=1366):
        """Prepare una página aislada sin tareas ni archivos de usuario."""
        vista = VistaSonoteca(crear_demo())
        pagina = SimpleNamespace(
            width=ancho,
            update=Mock(),
            add=Mock(),
            run_task=Mock(),
            show_dialog=Mock(),
            pop_dialog=Mock(),
        )
        vista.montar(pagina)
        vista._guardar_auto = AsyncMock()
        return vista, pagina

    async def test_sin_diagnostico_ni_tarea_periodica(self):
        """No dibuje herramientas académicas ni programe su muestreo."""
        vista, pagina = self.montar()
        pagina.run_task.assert_not_called()
        for seccion in ("Biblioteca", "Playlists", "Lista", "Siguientes"):
            vista.seccion = seccion
            vista.actualizar()
            contenido = textos(vista._contenido)
            for termino in ("FIFO", "O(1)", "Panel técnico", "nodos"):
                self.assertNotIn(termino, contenido)
        menu = textos(vista._menu_herramientas())
        self.assertNotIn("Panel técnico", menu)
        self.assertNotIn("académica", menu)
        self.assertNotIn(vista._estado_audio, list(recorrer(vista._dock_info)))

    async def test_refresco_y_resize_sin_construccion_duplicada(self):
        """Construya una sola instantánea y publique un único refresco."""
        vista, pagina = self.montar()
        pagina.update.reset_mock()
        with (
            patch.object(VistaReproductor, "actualizar") as heredado,
            patch.object(
                vista.controlador,
                "estado_vista",
                wraps=vista.controlador.estado_vista,
            ) as estado,
        ):
            vista._redimensionar()
        heredado.assert_not_called()
        estado.assert_called_once()
        pagina.update.assert_called_once()

    async def test_resalta_solo_la_aparicion_y_playlist_reproducida(self):
        """Distinga repeticiones y no marque otra lista con el mismo tema."""
        vista, _ = self.montar()
        vista._audio = SimpleNamespace(
            reproducir=AsyncMock(),
            actual_id=None,
            pausado=False,
            posicion=0,
            duracion=6,
        )
        vista.controlador.agregar_entrada(1, 1)
        vista.controlador.agregar_entrada(2, 1)
        vista.playlist_id = 1
        await vista._entrada(1)
        vista.actualizar()
        foto = vista._playlist_visible
        pista = vista.controlador.listar()[0]
        repetidas = [e for e in foto.entradas if e.cancion_id == 1]
        self.assertEqual(len(repetidas), 2)
        self.assertEqual(
            [
                vista._es_pista_activa(pista, e.identificador)
                for e in repetidas
            ],
            [True, False],
        )
        vista.playlist_id = 2
        vista.actualizar()
        otra = vista._playlist_visible.entradas[-1]
        self.assertFalse(vista._es_pista_activa(pista, otra.identificador))

    async def test_fila_completa_reproduce_y_muestra_numero(self):
        """Conecte la fila a una sola acción de reproducción de esa pista."""
        vista, _ = self.montar()
        pista = vista.controlador.listar()[0]
        vista._escuchar = AsyncMock()
        fila = vista._pista(pista, 7)
        self.assertIn("7", textos(fila))
        await fila.on_click(None)
        vista._escuchar.assert_awaited_once_with(pista)

    async def test_cola_separada_y_alternancia_del_panel(self):
        """Separe solicitudes destacadas y normales sin vocabulario técnico."""
        vista, _ = self.montar()
        pistas = vista.controlador.listar()
        vista._encolar(pistas[0], True)
        vista._encolar(pistas[1])
        vista._alternar_cola()
        vista.actualizar()
        contenido = textos(vista._panel_actual.content)
        self.assertIn("REPRODUCIR DESPUÉS", contenido)
        self.assertIn("EN TU COLA", contenido)
        self.assertLess(
            contenido.index(pistas[0].titulo),
            contenido.index(pistas[1].titulo),
        )
        self.assertNotIn("Prioridad", contenido)
        self.assertNotIn("FIFO", contenido)
        vista._alternar_cola()
        vista.actualizar()
        self.assertIn("SONANDO AHORA", textos(vista._panel_actual.content))

    async def test_cola_accesible_en_telefono_y_redimensionado(self):
        """Mantenga acceso a la cola en la barra compacta y al ampliar."""
        vista, pagina = self.montar(390)
        self.assertTrue(vista._volumen_panel.visible)
        self.assertTrue(vista._boton_cola.visible)
        self.assertFalse(vista._volumen_control.visible)
        vista._alternar_cola()
        vista.actualizar()
        self.assertEqual(vista.seccion, "Siguientes")
        self.assertEqual(pagina.navigation_bar.selected_index, 2)
        pagina.width = 1366
        vista._redimensionar()
        self.assertTrue(vista._volumen_control.visible)
        self.assertIsNone(pagina.navigation_bar)
        self.assertEqual(
            vista._volumen_panel.controls.count(vista._boton_cola), 1
        )

    async def test_volumen_inicial_bajo_y_duracion_sin_seleccion(self):
        """Inicie al cinco por ciento y no muestre duración de la precarga."""
        vista, _ = self.montar()
        self.assertEqual(vista._audio.audio.volume, 0.05)
        self.assertEqual(vista._volumen_control.value, 0.05)
        vista._audio.duracion = 6
        vista._actualizar_controles()
        self.assertEqual(vista._total.value, "0:00")

    async def test_ficha_desde_barra_y_atajos_de_historial(self):
        """Abra la ficha seleccionada y deshaga/rehaga mediante controlador."""
        vista, pagina = self.montar()
        vista._ficha = AsyncMock()
        await vista._dock_info.on_click(None)
        vista._ficha.assert_not_awaited()
        vista._seleccion = vista.controlador.listar()[0]
        await vista._dock_info.on_click(None)
        vista._ficha.assert_awaited_once_with(vista._seleccion)
        vista.controlador.crear_playlist("Nueva")
        evento = SimpleNamespace(
            key="Z", ctrl=True, meta=False, alt=False, shift=False
        )
        await pagina.on_keyboard_event(evento)
        self.assertEqual(
            len(vista.controlador.estado_vista()["estado"].playlists), 2
        )
        evento.key = "Y"
        await pagina.on_keyboard_event(evento)
        self.assertEqual(
            len(vista.controlador.estado_vista()["estado"].playlists), 3
        )
