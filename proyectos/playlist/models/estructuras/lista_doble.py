"""Lista doble manual: los datos residen en nodos, no en una list."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(eq=False)
class _Nodo(Generic[T]):
    """Agrupe un dato y referencias a ambos vecinos.

    Es privado: solo la estructura modifica sus enlaces. eq=False evita
    comparar recursivamente cadenas de nodos con enlaces de retorno.
    """

    dato: T
    anterior: _Nodo[T] | None = None
    siguiente: _Nodo[T] | None = None


class ListaDoblementeEnlazada(Generic[T]):
    """Mantenga cabeza, cola y tamaño para recorridos bidireccionales.

    Vacía: ambos extremos son None. No vacía: cabeza.anterior y
    cola.siguiente son None; cada par de vecinos se enlaza en ambos
    sentidos. No modifique la lista mientras recorre un iterador.
    """

    def __init__(self) -> None:
        """Inicialice una estructura vacía sin colecciones auxiliares."""
        self._cabeza: _Nodo[T] | None = None
        self._cola: _Nodo[T] | None = None
        self._tamano = 0

    def __len__(self) -> int:
        """Devuelva el tamaño registrado sin recorrer nodos; O(1)."""
        return self._tamano

    def agregar_final(self, dato: T) -> None:
        """Enlace un dato nuevo después de la cola; O(1).

        Si la lista está vacía, el nuevo nodo ocupa ambos extremos.
        No retorna un nodo: los enlaces permanecen encapsulados.
        """
        nuevo = _Nodo(dato=dato, anterior=self._cola)
        if self._cola is None:
            self._cabeza = nuevo
        else:
            self._cola.siguiente = nuevo
        self._cola = nuevo
        self._tamano += 1

    def buscar(self, coincide: Callable[[T], bool]) -> T | None:
        """Devuelva el primer dato que cumpla el predicado, o None.

        No modifica enlaces. O(n) si el predicado cuesta O(1).
        """
        for dato in self:
            if coincide(dato):
                return dato
        return None

    def eliminar(self, coincide: Callable[[T], bool]) -> T | None:
        """Quite la primera coincidencia y devuelva su dato, o None.

        Localizar cuesta O(n); reconectar vecinos cuesta O(1).
        Actualiza extremos, tamaño y ambos enlaces de los vecinos.
        """
        actual = self._cabeza
        while actual is not None:
            if coincide(actual.dato):
                if actual.anterior is None:
                    self._cabeza = actual.siguiente
                else:
                    actual.anterior.siguiente = actual.siguiente
                if actual.siguiente is None:
                    self._cola = actual.anterior
                else:
                    actual.siguiente.anterior = actual.anterior
                self._tamano -= 1
                # Soltar ambos enlaces evita retener vecinos desde el nodo.
                actual.anterior = None
                actual.siguiente = None
                return actual.dato
            actual = actual.siguiente
        return None

    def __iter__(self) -> Iterator[T]:
        """Produzca datos desde la cabeza; O(n) al consumirlos todos.

        yield entrega un dato a la vez sin copiar la estructura.
        """
        actual = self._cabeza
        while actual is not None:
            yield actual.dato
            actual = actual.siguiente

    def recorrer_inverso(self) -> Iterator[T]:
        """Produzca datos desde la cola usando anterior; recorrido O(n)."""
        actual = self._cola
        while actual is not None:
            yield actual.dato
            actual = actual.anterior
