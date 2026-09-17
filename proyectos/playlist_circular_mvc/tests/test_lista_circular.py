"""Pruebas del modelo y el controlador, sin abrir Tkinter."""

import unittest

from controllers.controlador_playlist import (
    ControladorPlaylist,
    ErrorDeValidacion,
)
from models.lista_circular import ListaCircular


class PruebasListaCircular(unittest.TestCase):
    def setUp(self) -> None:
        self.lista = ListaCircular()

    def test_lista_nueva_esta_vacia(self) -> None:
        self.assertTrue(self.lista.esta_vacia())
        self.assertEqual(0, len(self.lista))
        self.assertEqual([], self.lista.listar())

    def test_agregar_conserva_orden_y_asigna_ids(self) -> None:
        primera = self.lista.agregar("Uno", "Artista A")
        segunda = self.lista.agregar("Dos", "Artista B")

        self.assertEqual([primera, segunda], self.lista.listar())
        self.assertEqual((1, 2), (primera.identificador, segunda.identificador))

    def test_avanzar_es_circular(self) -> None:
        primera = self.lista.agregar("Uno", "A")
        segunda = self.lista.agregar("Dos", "B")

        self.assertEqual(segunda, self.lista.avanzar())
        self.assertEqual(primera, self.lista.avanzar())

    def test_eliminar_usa_id_aunque_haya_titulos_repetidos(self) -> None:
        primera = self.lista.agregar("Repetida", "A")
        segunda = self.lista.agregar("Repetida", "A")

        self.assertTrue(self.lista.eliminar(segunda.identificador))
        self.assertEqual([primera], self.lista.listar())

    def test_eliminar_actual_avanza_a_la_siguiente(self) -> None:
        primera = self.lista.agregar("Uno", "A")
        segunda = self.lista.agregar("Dos", "B")
        self.lista.seleccionar(primera.identificador)

        self.assertTrue(self.lista.eliminar(primera.identificador))
        self.assertEqual(segunda, self.lista.obtener_actual())

    def test_eliminar_unico_elemento_deja_lista_vacia(self) -> None:
        cancion = self.lista.agregar("Única", "A")

        self.assertTrue(self.lista.eliminar(cancion.identificador))
        self.assertTrue(self.lista.esta_vacia())
        self.assertIsNone(self.lista.obtener_actual())

    def test_busqueda_ignora_mayusculas(self) -> None:
        esperada = self.lista.agregar("Viva mi Patria", "Grupo Bolivia")
        self.lista.agregar("Otra", "Artista")

        self.assertEqual([esperada], self.lista.buscar("BOLIVIA"))


class PruebasControlador(unittest.TestCase):
    def setUp(self) -> None:
        self.controlador = ControladorPlaylist()

    def test_limpia_los_datos_de_entrada(self) -> None:
        cancion = self.controlador.agregar_cancion("  Título  ", "  Artista  ")
        self.assertEqual("Título", cancion.titulo)
        self.assertEqual("Artista", cancion.artista)

    def test_rechaza_campos_vacios(self) -> None:
        with self.assertRaises(ErrorDeValidacion):
            self.controlador.agregar_cancion("", "Artista")
        with self.assertRaises(ErrorDeValidacion):
            self.controlador.agregar_cancion("Título", "   ")

    def test_siguiente_en_lista_vacia_informa_error(self) -> None:
        with self.assertRaises(ErrorDeValidacion):
            self.controlador.reproducir_siguiente()


if __name__ == "__main__":
    unittest.main()
