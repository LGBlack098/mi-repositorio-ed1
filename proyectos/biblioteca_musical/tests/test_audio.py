"""Contrato asíncrono del reproductor, sin requerir altavoces en pruebas."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import flet as ft
import flet_audio as fa

from services.archivos_audio import ArchivosAudio
from services.reproductor import Reproductor


class TestReproductor(unittest.IsolatedAsyncioTestCase):
    """Pruebe transición, errores y fin de pista con servicio simulado."""

    def setUp(self) -> None:
        """Prepare archivo temporal, eventos y servicio sin dispositivo."""
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        base = Path(self.temporal.name)
        (base / "audio").mkdir()
        (base / "audio/test.wav").write_bytes(b"test")
        self.avisos = []
        self.fin = AsyncMock()
        self.r = Reproductor(ArchivosAudio(base), self.avisos.append, self.fin)
        self.r.audio = SimpleNamespace(
            src=None,
            play=AsyncMock(),
            release=AsyncMock(),
            pause=AsyncMock(),
            resume=AsyncMock(),
            volume=0.5,
            update=Mock(side_effect=lambda: self.r._listo.set()),
            seek=AsyncMock(),
        )

    async def test_reproducir_pausar_reanudar_detener(self) -> None:
        """Verifique llamadas y selección sin adelantar al detener."""
        await self.r.reproducir(1, "audio/test.wav")
        self.assertEqual(self.r.actual_id, 1)
        await self.r.pausar_reanudar()
        self.assertTrue(self.r.pausado)
        self.r.audio.pause.assert_awaited_once()
        await self.r.pausar_reanudar()
        self.r.audio.resume.assert_awaited_once()
        self.r.volumen(0.25)
        self.assertEqual(self.r.audio.volume, 0.25)
        await self.r.detener()
        self.assertIsNone(self.r.actual_id)
        self.fin.assert_not_awaited()

    async def test_fin_una_vez(self) -> None:
        """Un evento repetido de fin no consuma dos canciones."""
        await self.r.reproducir(1, "audio/test.wav")
        evento = SimpleNamespace(state=fa.AudioState.COMPLETED)
        await self.r._estado(evento)
        await self.r._estado(evento)
        self.fin.assert_awaited_once()
        self.r._posicion(SimpleNamespace(position=0))
        self.assertEqual(self.avisos[-1], "Pista finalizada")

    async def test_buscar_posicion_real(self) -> None:
        """Convierta segundos de la barra a milisegundos del dispositivo."""
        await self.r.reproducir(1, "audio/test.wav")
        self.r._duracion(SimpleNamespace(duration=6000))
        await self.r.buscar_posicion(2.5)
        self.r.audio.seek.assert_awaited_with(2500)
        self.assertEqual(self.r.posicion, 2)
        with self.assertRaises(ValueError):
            await self.r.buscar_posicion(7)

    async def test_error_y_archivo_ausente(self) -> None:
        """Rechace audio ausente y limpie identidad tras fallo de códec."""
        with self.assertRaises(ValueError):
            await self.r.reproducir(1, "audio/ausente.wav")
        self.r.audio.play.assert_not_awaited()
        self.r.audio.play.side_effect = RuntimeError("códec inválido")
        with self.assertRaises(RuntimeError):
            await self.r.reproducir(1, "audio/test.wav")
        self.assertIsNone(self.r.actual_id)

    async def test_posicion_volumen_y_timeout(self) -> None:
        """Propague tiempo límite y valide volumen antes de modificar."""
        self.r._posicion(SimpleNamespace(position=ft.Duration(seconds=3)))
        self.assertEqual(self.r.posicion, 3)
        self.r._posicion(SimpleNamespace(position=4500))
        self.assertEqual(self.r.posicion, 4)
        with self.assertRaises(ValueError):
            self.r.volumen(2)
        with self.assertRaises(ValueError):
            await self.r.pausar_reanudar()
        with patch(
            "services.reproductor.asyncio.wait_for", side_effect=TimeoutError
        ):
            # Cerrar la coroutine evita advertencias artificiales del mock.
            async def agotar(coroutine, timeout):
                """Simule timeout y cierre la coroutine sin esperar."""
                coroutine.close()
                raise TimeoutError("sin respuesta")

            with patch("services.reproductor.asyncio.wait_for", agotar):
                with self.assertRaises(TimeoutError):
                    await self.r.reproducir(1, "audio/test.wav")
        self.assertIsNone(self.r.actual_id)
