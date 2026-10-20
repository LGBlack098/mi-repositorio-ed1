"""Invariantes de circularidad, LIFO, FIFO y prioridad estable."""

import random
import unittest

from models.estructuras.lineales import (
    Cola,
    ColaCircular,
    ColaPrioridad,
    Pila,
    Prioridad,
)
from models.estructuras.lista_circular import ListaCircular


class TestCircular(unittest.TestCase):
    """Verifique ambos sentidos y cierres del anillo después de mutar."""

    def comprobar(self, lista, esperados) -> None:
        """Recorra n nodos y compruebe retorno y enlaces recíprocos."""
        self.assertEqual(tuple(lista), tuple(esperados))
        self.assertEqual(len(lista), len(esperados))
        if not esperados:
            self.assertIsNone(lista._cabeza)
            self.assertIsNone(lista._actual)
            return
        nodo = lista._cabeza
        for _ in esperados:
            self.assertIs(nodo.siguiente.anterior, nodo)
            self.assertIs(nodo.anterior.siguiente, nodo)
            nodo = nodo.siguiente
        self.assertIs(nodo, lista._cabeza)
        inversos = []
        for _ in esperados:
            nodo = nodo.anterior
            inversos.append(nodo.dato)
        self.assertEqual(inversos, list(reversed(esperados)))

    def test_vacia_y_unico(self) -> None:
        """Compruebe None vacío y autoenlaces con un nodo."""
        lista = ListaCircular()
        self.assertIsNone(lista.actual())
        self.assertIsNone(lista.mover())
        self.assertIsNone(lista.eliminar(lambda x: True))
        lista.agregar(1)
        self.comprobar(lista, (1,))
        self.assertEqual(lista.mover(-1), 1)
        lista.eliminar(lambda x: True)
        self.comprobar(lista, ())
        lista.agregar(2)
        self.comprobar(lista, (2,))

    def test_cursor_y_borrados(self) -> None:
        """Elimine cabeza, medio y cola y conserve cursor cuando procede."""
        for borrar in (1, 2, 3):
            with self.subTest(borrar=borrar):
                lista = ListaCircular()
                for x in (1, 2, 3):
                    lista.agregar(x)
                self.assertEqual(lista.mover(-1), 3)
                self.assertEqual(lista.mover(), 1)
                lista.seleccionar(lambda x: x == borrar)
                self.assertEqual(lista.eliminar(lambda x: x == borrar), borrar)
                self.comprobar(
                    lista, tuple(x for x in (1, 2, 3) if x != borrar)
                )
                self.assertEqual(lista.actual(), {1: 2, 2: 3, 3: 1}[borrar])
                self.assertIsNone(lista.seleccionar(lambda x: x == 99))
                with self.assertRaises(ValueError):
                    lista.mover(0)

    def test_operaciones_aleatorias(self) -> None:
        """Compare 300 mutaciones con un oráculo de secuencia."""
        azar = random.Random(220)
        lista = ListaCircular()
        esperados = []
        for x in range(300):
            if not esperados or azar.random() < 0.6:
                lista.agregar(x)
                esperados.append(x)
            else:
                valor = azar.choice(esperados)
                lista.eliminar(lambda dato: dato == valor)
                esperados.remove(valor)
            self.comprobar(lista, esperados)

    def test_eliminar_todos_conserva_anillo(self) -> None:
        """Quite coincidencias consecutivas y luego vacíe el anillo."""
        lista = ListaCircular()
        for dato in (1, 1, 2, 1, 3, 1):
            lista.agregar(dato)
        self.assertEqual(lista.eliminar_todos(lambda x: x == 1), 4)
        self.comprobar(lista, (2, 3))
        self.assertEqual(lista.actual(), 2)
        self.assertEqual(lista.eliminar_todos(lambda x: True), 2)
        self.comprobar(lista, ())


class TestLineales(unittest.TestCase):
    """Compruebe políticas de salida y extremos tras vaciar/reinsertar."""

    def test_pila_lifo(self) -> None:
        """Compruebe el último en entrar y errores de pila vacía."""
        pila = Pila()
        for x in (1, 2, 3):
            pila.apilar(x)
        self.assertEqual(tuple(pila), (3, 2, 1))
        self.assertEqual(pila.ver_tope(), 3)
        self.assertEqual(tuple(pila.desapilar() for _ in range(3)), (3, 2, 1))
        for operacion in (pila.desapilar, pila.ver_tope):
            with self.assertRaises(ValueError):
                operacion()
        pila.apilar(4)
        self.assertEqual(len(pila), 1)

    def test_fifo(self) -> None:
        """Compruebe FIFO y reinicio de ambos extremos al vaciar."""
        cola = Cola()
        for x in (1, 2, 3):
            cola.encolar(x)
        self.assertEqual(cola.ver_frente(), 1)
        self.assertEqual(tuple(cola.desencolar() for _ in range(3)), (1, 2, 3))
        self.assertIsNone(cola._final)
        self.assertIsNone(cola._frente)
        with self.assertRaises(ValueError):
            cola.desencolar()
        cola.encolar(4)
        self.assertEqual(tuple(cola), (4,))

    def test_prioridad_estable(self) -> None:
        """Compruebe orden descendente y llegada para empates."""
        cola = ColaPrioridad()
        for dato, prioridad in (("a", 1), ("b", 5), ("c", 5), ("d", 0)):
            cola.encolar(Prioridad(dato, prioridad))
        self.assertEqual(tuple(x.dato for x in cola), ("b", "c", "a", "d"))
        for invalida in (-1, True, "3"):
            with self.assertRaises(ValueError):
                cola.encolar(Prioridad("x", invalida))
        self.assertEqual(len(cola), 4)
        self.assertEqual(cola.desencolar().dato, "b")

    def test_cola_circular_llena_y_rotacion(self) -> None:
        """Compruebe capacidad, cierre y reutilización sin sobrescritura."""
        cola = ColaCircular(2)
        cola.encolar(1)
        cola.encolar(2)
        with self.assertRaises(ValueError):
            cola.encolar(3)
        self.assertEqual(tuple(cola), (1, 2))
        self.assertIs(cola._final.siguiente.siguiente, cola._final)
        self.assertEqual(cola.desencolar(), 1)
        cola.encolar(3)
        self.assertEqual(tuple(cola), (2, 3))
        self.assertEqual(cola.ver_frente(), 2)
        cola.desencolar()
        cola.desencolar()
        self.assertIsNone(cola._final)
        with self.assertRaises(ValueError):
            cola.ver_frente()
        cola.encolar(9)
        self.assertIs(cola._final.siguiente, cola._final)
        for capacidad in (0, -1, True):
            with self.assertRaises(ValueError):
                ColaCircular(capacidad)
