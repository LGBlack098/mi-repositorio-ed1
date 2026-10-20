"""Integración de catálogo, anillos, colas y transacciones de historial."""

import unittest

from controllers.controlador_biblioteca import ControladorBiblioteca


class TestSesion(unittest.TestCase):
    """Compruebe identidad estable y ausencia de referencias huérfanas."""

    def setUp(self) -> None:
        """Prepare tres canciones y dos playlists con repeticiones."""
        self.c = ControladorBiblioteca()
        for titulo in ("A", "B", "C"):
            self.c.agregar(titulo, "Artista", "60")
        self.c.crear_playlist("Una")
        self.c.crear_playlist("Dos")
        for pid, cid in ((1, 1), (1, 2), (1, 1), (2, 3)):
            self.c.agregar_entrada(pid, cid)

    def test_repeticiones_y_navegacion(self) -> None:
        """Quite solo una aparición y pruebe retorno en ambos extremos."""
        self.assertEqual(self.c.mover(1, -1).titulo, "A")
        self.c.borrar_entrada(1, 3)
        foto = self.c.estado_vista()["estado"].playlists[0]
        self.assertEqual(tuple(e.identificador for e in foto.entradas), (1, 2))
        self.assertEqual(foto.actual_id, 1)
        self.assertEqual(self.c.mover(1, -1).titulo, "B")
        self.assertEqual(self.c.mover(1, 1).titulo, "A")

    def test_deshacer_baja_restaura_orden_y_cursor(self) -> None:
        """Recupere IDs, orden y cursor de todas las apariciones borradas."""
        self.c.seleccionar(1, 3)
        antes = self.c.estado_vista()["estado"]
        self.c.eliminar(1)
        self.assertEqual(
            len(self.c.estado_vista()["estado"].playlists[0].entradas), 1
        )
        self.c.historial()
        despues = self.c.estado_vista()["estado"]
        self.assertEqual(antes.canciones, despues.canciones)
        self.assertEqual(antes.playlists, despues.playlists)
        self.c.historial(True)
        self.assertEqual(tuple(c.titulo for c in self.c.listar()), ("B", "C"))

    def test_accion_nueva_invalida_rehacer_sin_reutilizar_ids(self) -> None:
        """Conserve marcas aunque se deshaga una inserción."""
        agregada = self.c.agregar("D", "Artista", "60")
        self.c.historial()
        with self.assertRaises(ValueError):
            self.c.agregar("", "Artista", "60")
        self.assertEqual(len(self.c.estado_vista()["rehacer"]), 1)
        siguiente = self.c.agregar("E", "Artista", "60")
        self.assertGreater(siguiente.identificador, agregada.identificador)
        self.assertEqual(self.c.estado_vista()["rehacer"], ())

    def test_edicion_fallida_es_atomica(self) -> None:
        """Restaure un cambio parcial y no registre acción fallida."""
        antes = self.c.estado_vista()

        def fallar() -> None:
            """Simule fallo después de modificar el catálogo."""
            self.c.sesion.biblioteca.eliminar(1)
            raise ValueError("fallo simulado")

        with self.assertRaises(ValueError):
            self.c.sesion.editar("Fallida", fallar)
        self.assertEqual(self.c.listar(), antes["estado"].canciones)
        self.assertEqual(self.c.estado_vista()["deshacer"], antes["deshacer"])

    def test_colas_y_limpieza_de_ids(self) -> None:
        """Purgue solicitudes borradas sin recuperarlas al deshacer."""
        for cid in (1, 2, 1):
            self.c.solicitar(cid)
        self.c.solicitar(1, 5)
        self.c.solicitar(2, 5)
        self.c.eliminar(1)
        self.assertEqual(self.c.estado_vista()["fifo"], (2,))
        self.assertEqual(
            tuple(p.dato for p in self.c.estado_vista()["prioridad"]), (2,)
        )
        self.c.historial()
        self.assertEqual(self.c.consumir("fifo").identificador, 2)
        self.assertEqual(self.c.consumir("prioridad").identificador, 2)
        with self.assertRaises(ValueError):
            self.c.consumir("fifo")

    def test_turnos_round_robin(self) -> None:
        """Alterne playlists y avance cada cursor después de atender."""
        self.c.agregar_turno(1)
        self.c.agregar_turno(2)
        with self.assertRaises(ValueError):
            self.c.agregar_turno(1)
        salida = tuple(
            self.c.consumir("turnos").identificador for _ in range(4)
        )
        self.assertEqual(salida, (1, 3, 2, 3))
        self.c.borrar_playlist(2)
        self.assertEqual(self.c.estado_vista()["turnos"], (1,))

    def test_playlist_vacia_y_capacidad_turnos(self) -> None:
        """Rechace playlist vacía y noveno turno sin perder los ocho."""
        self.c.crear_playlist("Vacía")
        with self.assertRaises(ValueError):
            self.c.agregar_turno(3)
        for pid in range(4, 12):
            self.c.crear_playlist(str(pid))
            self.c.agregar_entrada(pid, 1)
            self.c.agregar_turno(pid)
        self.c.agregar_entrada(3, 1)
        with self.assertRaises(ValueError):
            self.c.agregar_turno(3)
        self.assertEqual(len(self.c.estado_vista()["turnos"]), 8)

    def test_historial_acotado_y_audio_reversible(self) -> None:
        """Limite historial y permita deshacer la asociación de audio."""
        self.c.asociar_audio(1, "audio/demo.wav")
        self.c.historial()
        self.assertEqual(self.c.listar()[0].archivo, "")
        self.c.historial(True)
        self.assertEqual(self.c.listar()[0].archivo, "audio/demo.wav")
        for i in range(60):
            self.c.crear_playlist(str(i))
        self.assertEqual(len(self.c.estado_vista()["deshacer"]), 50)
