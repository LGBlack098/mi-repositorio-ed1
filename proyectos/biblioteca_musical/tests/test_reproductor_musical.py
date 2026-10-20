"""Contratos musicales de importación, navegación y pantalla principal."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import flet as ft
from mutagen.id3 import TIT2, TPE1
from mutagen.wave import WAVE

from controllers.controlador_biblioteca import ControladorBiblioteca
from demo import crear_demo
from generar_demo import generar
from main import construir_controlador
from services.metadatos import leer_metadatos
from views.vista_reproductor import VistaReproductor


class TestMetadatos(unittest.TestCase):
    """Lea datos reales de WAV, etiquetas ID3 y nombre alternativo."""

    def test_tags_y_nombre_sin_inventar_duracion(self) -> None:
        """Respete etiquetas y mida segundos desde el archivo real."""
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "prueba.wav"
            generar(ruta)
            self.assertEqual(
                leer_metadatos(ruta, "Artista - Título.wav"),
                ("Título", "Artista", 6),
            )
            audio = WAVE(ruta)
            audio.add_tags()
            audio.tags.add(TIT2(encoding=3, text=["Título etiquetado"]))
            audio.tags.add(TPE1(encoding=3, text=["Artista etiquetado"]))
            audio.save()
            self.assertEqual(
                leer_metadatos(ruta, "nombre.wav"),
                ("Título etiquetado", "Artista etiquetado", 6),
            )

    def test_rechaza_archivo_no_musical(self) -> None:
        """No convierta bytes arbitrarios en una canción de duración falsa."""
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "invalido.wav"
            ruta.write_bytes(b"no es audio")
            with self.assertRaises(ValueError):
                leer_metadatos(ruta, ruta.name)

    def test_arranque_nuevo_sin_catalogo_ficticio(self) -> None:
        """Inicie vacío por defecto y reserve las muestras para --demo."""
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "musica.json"
            controlador, _ = construir_controlador(ruta)
            self.assertEqual(controlador.listar(), ())
            demo, _ = construir_controlador(ruta, demo=True)
            self.assertEqual(len(demo.listar()), 3)


class TestFlujoMusical(unittest.IsolatedAsyncioTestCase):
    """Compruebe que biblioteca, cola y controles funcionan al escuchar."""

    def setUp(self) -> None:
        """Prepare audio simulado y catálogo para probar la navegación."""
        self.vista = VistaReproductor(crear_demo())
        self.vista._audio = SimpleNamespace(
            reproducir=AsyncMock(),
            detener=AsyncMock(),
            actual_id=None,
            pausado=False,
            posicion=0,
            duracion=6,
        )

    async def test_siguiente_anterior_desde_biblioteca(self) -> None:
        """Navegue canciones sin tener que crear o iniciar una playlist."""
        pistas = self.vista.controlador.listar()
        await self.vista._escuchar(pistas[0])
        await self.vista._saltar(1)
        self.assertEqual(self.vista._seleccion.identificador, 2)
        await self.vista._saltar(-1)
        self.assertEqual(self.vista._seleccion.identificador, 1)
        await self.vista._saltar(-1)
        self.assertEqual(self.vista._seleccion.identificador, 1)

    async def test_repeticion_opcional(self) -> None:
        """Detenga al final o vuelva al inicio solo si se activó repetir."""
        pistas = self.vista.controlador.listar()
        await self.vista._escuchar(pistas[-1])
        await self.vista._saltar(1)
        self.vista._audio.detener.assert_awaited_once()
        self.vista._alternar_repeticion()
        await self.vista._escuchar(pistas[-1])
        await self.vista._saltar(1)
        self.assertEqual(self.vista._seleccion.identificador, 1)

    async def test_reproducir_despues_antes_de_fila_normal(self) -> None:
        """Consuma prioridad y luego FIFO, conservando el contexto musical."""
        pistas = self.vista.controlador.listar()
        await self.vista._escuchar(pistas[0])
        self.vista._encolar(pistas[2])
        self.vista._encolar(pistas[1], inmediata=True)
        await self.vista._saltar(1)
        self.assertEqual(self.vista._seleccion.identificador, 2)
        await self.vista._saltar(1)
        self.assertEqual(self.vista._seleccion.identificador, 3)
        self.assertEqual(self.vista._contexto_id, 1)

    async def test_playlist_navega_y_respeta_repeticion(self) -> None:
        """Use cursor circular internamente y respete el control de repetir."""
        self.vista.playlist_id = 1
        await self.vista._entrada(2)
        await self.vista._saltar(1)
        self.vista._audio.detener.assert_awaited_once()
        self.vista._alternar_repeticion()
        await self.vista._entrada(2)
        await self.vista._saltar(1)
        self.assertEqual(self.vista._seleccion.identificador, 1)

    async def test_importacion_multiple_y_guardado_automatico(self) -> None:
        """Importe pistas reales y conserve las válidas si otra está dañada."""
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio)
            ruta = base / "original.wav"
            generar(ruta)
            vista = VistaReproductor(
                ControladorBiblioteca(), base, base / "data/musica.json"
            )
            self.montar_sin_dispositivo(vista)
            archivo = SimpleNamespace(
                name="Artista - Canción.wav",
                bytes=ruta.read_bytes(),
                path=None,
            )
            invalido = SimpleNamespace(
                name="malo.wav", bytes=b"mal", path=None
            )
            await vista._importar_musica(
                SimpleNamespace(files=[archivo, invalido])
            )
            self.assertEqual(len(vista.controlador.listar()), 1)
            cancion = vista.controlador.listar()[0]
            self.assertEqual(
                (cancion.titulo, cancion.artista), ("Canción", "Artista")
            )
            self.assertEqual(cancion.duracion_segundos, 6)
            self.assertTrue((base / "data/musica.json").exists())
            self.assertIn("1 canciones añadidas", vista._mensaje.value)
            self.assertIn("1 no se pudieron importar", vista._mensaje.value)

    def montar_sin_dispositivo(self, vista) -> list:
        """Monte controles con una página de prueba, sin ventana."""
        controles = []
        pagina = SimpleNamespace(width=1320, update=Mock())
        pagina.add = lambda *nuevos: controles.extend(nuevos)
        vista.montar(pagina)
        return controles

    async def test_pantalla_inicial_sin_panel_tecnico(self) -> None:
        """Mantenga funciones académicas fuera de los controles visibles."""
        controles = self.montar_sin_dispositivo(self.vista)
        textos = []

        def visitar(control) -> None:
            """Lea contenido visible sin expandir menús cerrados."""
            if not getattr(control, "visible", True):
                return
            if isinstance(control, ft.Text):
                textos.append(control.value or "")
            contenido = getattr(control, "content", None)
            if isinstance(contenido, str):
                textos.append(contenido)
            elif isinstance(contenido, ft.Control):
                visitar(contenido)
            for hijo in getattr(control, "controls", []):
                visitar(hijo)

        for control in controles:
            visitar(control)
        texto = "\n".join(textos)
        for tecnico in ("JSON", "Deshacer", "Rehacer", "FIFO", "Estructuras"):
            self.assertNotIn(tecnico, texto)
        self.assertIn("Añadir música", texto)
        self.assertIn("Tus canciones", texto)
        self.assertIsNotNone(self.vista._play.on_click)
        self.assertIsNotNone(self.vista._progreso.on_change_end)
