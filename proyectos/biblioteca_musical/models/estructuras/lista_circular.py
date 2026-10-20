"""Lista doble circular manual con cursor y recorridos acotados."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Generic, TypeVar

from models.estructuras.memoria import estimar_nodos

T = TypeVar("T")


@dataclass(eq=False)
class _NodoCircular(Generic[T]):
    """Conserve un dato y enlaces a los dos vecinos del anillo."""

    dato: T
    anterior: _NodoCircular[T] | None = None
    siguiente: _NodoCircular[T] | None = None


class ListaCircular(Generic[T]):
    """Mantenga cabeza y actual; la cola es cabeza.anterior.

    En un anillo de un nodo ambos enlaces apuntan al propio nodo.
    Nunca se espera None al recorrer: se limita por el tamaño.
    """

    def __init__(self) -> None:
        """Cree el anillo vacío en O(1)."""
        self._cabeza: _NodoCircular[T] | None = None
        self._actual: _NodoCircular[T] | None = None
        self._tamano = 0

    def __len__(self) -> int:
        """Devuelva el tamaño en O(1)."""
        return self._tamano

    def memoria_nodos(self) -> int:
        """Estime bytes de nodos, sin seguir indefinidamente el ciclo."""
        return estimar_nodos(self._cabeza, self._tamano)

    def agregar(self, dato: T) -> None:
        """Inserte antes de cabeza, conservando el cursor; O(1)."""
        nuevo = _NodoCircular(dato)
        if self._cabeza is None:
            nuevo.anterior = nuevo.siguiente = nuevo
            self._cabeza = self._actual = nuevo
        else:
            cola = self._cabeza.anterior
            nuevo.anterior, nuevo.siguiente = cola, self._cabeza
            cola.siguiente = self._cabeza.anterior = nuevo
        self._tamano += 1

    def actual(self) -> T | None:
        """Consulte el dato actual o None sin moverlo; O(1)."""
        return self._actual.dato if self._actual else None

    def mover(self, direccion: int = 1) -> T | None:
        """Avance (+1) o retroceda (-1); O(1), None si vacío.

        ValueError indica una dirección distinta de +1 o -1.
        """
        if type(direccion) is not int or direccion not in (-1, 1):
            raise ValueError("La dirección debe ser +1 o -1.")
        if self._actual:
            self._actual = (
                self._actual.siguiente
                if direccion == 1
                else self._actual.anterior
            )
        return self.actual()

    def seleccionar(self, coincide: Callable[[T], bool]) -> T | None:
        """Sitúe actual en la primera coincidencia; O(n), None si falta."""
        nodo = self._cabeza
        for _ in range(self._tamano):
            if coincide(nodo.dato):
                self._actual = nodo
                return nodo.dato
            nodo = nodo.siguiente
        return None

    def eliminar(self, coincide: Callable[[T], bool]) -> T | None:
        """Quite primera coincidencia; O(n), conservando el anillo.

        Si se quita actual, se selecciona su siguiente. Si era el único
        nodo, cabeza y actual quedan en None. No altera nada si falta.
        """
        nodo = self._cabeza
        for _ in range(self._tamano):
            if coincide(nodo.dato):
                self._quitar_nodo(nodo)
                return nodo.dato
            nodo = nodo.siguiente
        return None

    def _quitar_nodo(self, nodo: _NodoCircular[T]) -> None:
        """Reconecte un nodo conocido en O(1), incluyendo extremos."""
        if self._tamano == 1:
            self._cabeza = self._actual = None
        else:
            nodo.anterior.siguiente = nodo.siguiente
            nodo.siguiente.anterior = nodo.anterior
            if self._cabeza is nodo:
                self._cabeza = nodo.siguiente
            if self._actual is nodo:
                self._actual = nodo.siguiente
        self._tamano -= 1
        nodo.anterior = nodo.siguiente = None

    def eliminar_todos(self, coincide: Callable[[T], bool]) -> int:
        """Quite todas las coincidencias en O(n); devuelva cuántas quitó.

        Conserva siguiente antes de soltar enlaces. El recorrido usa el
        tamaño inicial para no repetir nodos ni detenerse prematuramente.
        """
        nodo = self._cabeza
        eliminados = 0
        for _ in range(self._tamano):
            siguiente = nodo.siguiente
            if coincide(nodo.dato):
                self._quitar_nodo(nodo)
                eliminados += 1
            nodo = siguiente
        return eliminados

    def __iter__(self) -> Iterator[T]:
        """Produzca exactamente n datos desde cabeza; O(n), sin copia."""
        nodo = self._cabeza
        for _ in range(self._tamano):
            yield nodo.dato
            nodo = nodo.siguiente
