"""Pruebas del catálogo y de enlaces en ambos sentidos."""

import unittest

from controllers.controlador_biblioteca import ControladorBiblioteca
from models.biblioteca import Biblioteca
from models.cancion import Cancion
from models.estructuras.lista_doble import ListaDoblementeEnlazada


class TestListaDoble(unittest.TestCase):
    """Verifique extremos, vecinos y tamaño tras insertar y eliminar."""

    def comprobar_enlaces(
        self, lista: ListaDoblementeEnlazada[int], esperados: tuple[int, ...]
    ) -> None:
        """Compruebe referencias reales además de los datos devueltos."""
        self.assertEqual(len(lista), len(esperados))
        actual = lista._cabeza
        anterior = None
        for esperado in esperados:
            self.assertIsNotNone(actual)
            self.assertEqual(actual.dato, esperado)
            self.assertIs(actual.anterior, anterior)
            anterior = actual
            actual = actual.siguiente
        self.assertIsNone(actual)
        self.assertIs(lista._cola, anterior)
        actual = lista._cola
        siguiente = None
        for esperado in reversed(esperados):
            self.assertIsNotNone(actual)
            self.assertEqual(actual.dato, esperado)
            self.assertIs(actual.siguiente, siguiente)
            siguiente = actual
            actual = actual.anterior
        self.assertIsNone(actual)
        self.assertIs(lista._cabeza, siguiente)

    def crear_lista(self) -> ListaDoblementeEnlazada[int]:
        """Cree tres nodos para los casos de eliminación."""
        lista: ListaDoblementeEnlazada[int] = ListaDoblementeEnlazada()
        for valor in (10, 20, 30):
            lista.agregar_final(valor)
        return lista

    def test_lista_vacia(self) -> None:
        """Compruebe buscar y eliminar sin nodos."""
        lista: ListaDoblementeEnlazada[int] = ListaDoblementeEnlazada()
        self.assertIsNone(lista.buscar(lambda dato: True))
        self.assertIsNone(lista.eliminar(lambda dato: True))
        self.comprobar_enlaces(lista, ())

    def test_insercion_y_recorrido(self) -> None:
        """Compruebe ambos extremos y los dos sentidos del recorrido."""
        lista = self.crear_lista()
        self.comprobar_enlaces(lista, (10, 20, 30))
        self.assertEqual(tuple(lista), (10, 20, 30))
        self.assertEqual(tuple(lista.recorrer_inverso()), (30, 20, 10))
        self.assertEqual(lista.buscar(lambda dato: dato == 20), 20)

    def test_eliminar_extremos_e_intermedio(self) -> None:
        """Verifique por separado cabeza, nodo intermedio y cola."""
        for valor, restantes in (
            (10, (20, 30)),
            (20, (10, 30)),
            (30, (10, 20)),
        ):
            with self.subTest(valor=valor):
                lista = self.crear_lista()
                self.assertEqual(
                    lista.eliminar(lambda dato: dato == valor), valor
                )
                self.comprobar_enlaces(lista, restantes)

    def test_eliminar_unico_y_reinsertar(self) -> None:
        """Verifique que vaciar permita crear una nueva cadena válida."""
        lista: ListaDoblementeEnlazada[int] = ListaDoblementeEnlazada()
        lista.agregar_final(10)
        lista.eliminar(lambda dato: True)
        self.comprobar_enlaces(lista, ())
        lista.agregar_final(20)
        self.comprobar_enlaces(lista, (20,))

    def test_eliminar_ausente(self) -> None:
        """Compruebe que una búsqueda fallida conserve todos los enlaces."""
        lista = self.crear_lista()
        self.assertIsNone(lista.eliminar(lambda dato: dato == 99))
        self.comprobar_enlaces(lista, (10, 20, 30))


class TestBiblioteca(unittest.TestCase):
    """Verifique reglas de identidad, búsqueda y validación."""

    def test_titulos_repetidos_e_ids(self) -> None:
        """Elimine una identidad sin borrar otro título repetido."""
        biblioteca = Biblioteca()
        primera = biblioteca.agregar("Luz", "Ana", 180)
        segunda = biblioteca.agregar("Luz", "Ana", 190)
        self.assertNotEqual(primera.identificador, segunda.identificador)
        self.assertEqual(biblioteca.eliminar(primera.identificador), primera)
        self.assertEqual(biblioteca.listar(), (segunda,))
        tercera = biblioteca.agregar("Otra", "Ana", 200)
        self.assertGreater(tercera.identificador, segunda.identificador)

    def test_busqueda_y_limpieza(self) -> None:
        """Busque por título y artista sin distinguir mayúsculas."""
        biblioteca = Biblioteca()
        cancion = biblioteca.agregar("  Luz  ", "  Ana  ", 185)
        self.assertEqual(cancion.titulo, "Luz")
        self.assertEqual(cancion.artista, "Ana")
        self.assertEqual(biblioteca.listar("LUZ"), (cancion,))
        self.assertEqual(biblioteca.listar(" ana "), (cancion,))
        self.assertEqual(biblioteca.listar("ausente"), ())
        self.assertEqual(cancion.duracion_formateada(), "3:05")

    def test_validacion_no_modifica_catalogo(self) -> None:
        """Rechace datos inválidos sin consumir IDs ni insertar nodos."""
        biblioteca = Biblioteca()
        for titulo, artista, duracion in (
            (" ", "Ana", 180),
            ("Luz", "", 180),
            ("Luz", "Ana", 0),
            ("Luz", "Ana", -1),
            ("Luz", "Ana", True),
            ("Luz", "Ana", 1.5),
        ):
            with self.subTest(datos=(titulo, artista, duracion)):
                with self.assertRaises(ValueError):
                    biblioteca.agregar(titulo, artista, duracion)
                self.assertEqual(biblioteca.cantidad(), 0)
        self.assertEqual(biblioteca.agregar("Luz", "Ana", 1).identificador, 1)

    def test_eliminar_id_inexistente(self) -> None:
        """Informe un ID ausente y conserve el catálogo."""
        biblioteca = Biblioteca()
        with self.assertRaises(ValueError):
            biblioteca.eliminar(99)
        self.assertEqual(biblioteca.cantidad(), 0)

    def test_controlador_conversion_e_inyeccion(self) -> None:
        """Conserve el modelo recibido y rechace segundos no enteros."""
        biblioteca = Biblioteca()
        controlador = ControladorBiblioteca(biblioteca)
        cancion = controlador.agregar("Luz", "Ana", "185")
        self.assertEqual(biblioteca.listar(), (cancion,))
        for texto in ("", "abc", "1.5", "0", "-1"):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    controlador.agregar("Otra", "Ana", texto)
        self.assertEqual(biblioteca.cantidad(), 1)
        self.assertEqual(controlador.eliminar(cancion.identificador), cancion)

    def test_entidad_valida_identificador(self) -> None:
        """Rechace IDs inválidos incluso al crear la entidad directamente."""
        for identificador in (0, -1, True):
            with self.subTest(identificador=identificador):
                with self.assertRaises(ValueError):
                    Cancion(identificador, "Luz", "Ana", 180)


if __name__ == "__main__":
    unittest.main()
