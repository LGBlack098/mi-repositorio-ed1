"""Integración asíncrona de acciones sin depender de capturas o píxeles."""

import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from demo import crear_demo
from views.vista_biblioteca import VistaBiblioteca


class TestAcciones(unittest.IsolatedAsyncioTestCase):
    """Compruebe orden de eventos y protección del guardado local."""

    async def test_acciones_serializadas(self) -> None:
        """No intercale una edición mientras otra acción está esperando."""
        vista = VistaBiblioteca(crear_demo())
        orden = []

        async def primera() -> None:
            """Simule una acción de disco que cede al bucle de eventos."""
            orden.append("inicio")
            await asyncio.sleep(0)
            orden.append("fin")

        await asyncio.gather(
            vista._accion(primera)(),
            vista._accion(lambda: orden.append("segunda"))(),
        )
        self.assertEqual(orden, ["inicio", "fin", "segunda"])

    async def test_detener_cancela_continuacion_pendiente(self) -> None:
        """Evite reinicio por fin de pista que estaba esperando una acción."""
        vista = VistaBiblioteca(crear_demo())
        vista._audio = SimpleNamespace(detener=AsyncMock())
        vista._origen = "playlist"
        vista._continuar = True
        vista._saltar = AsyncMock()
        async with vista._serial:
            pendiente = asyncio.create_task(vista._fin_audio())
            await asyncio.sleep(0)
            await vista._detener()
        await pendiente
        vista._saltar.assert_not_awaited()
        self.assertFalse(vista._continuar)

    async def test_otro_guardado_no_se_sobrescribe(self) -> None:
        """Detecte el archivo escrito por otra sesión antes de guardar."""
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "datos.json"
            vista = VistaBiblioteca(crear_demo(), archivo_datos=ruta)
            ruta.write_text("cambio externo", encoding="utf-8")
            with self.assertRaises(ValueError):
                await vista._guardar()
            self.assertEqual(ruta.read_text(), "cambio externo")
