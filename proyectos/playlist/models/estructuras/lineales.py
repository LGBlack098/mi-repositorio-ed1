"""Pila, FIFO, prioridad estable y cola circular mediante nodos."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(eq=False)
class _NodoSimple(Generic[T]):
    """Guarde dato y referencia siguiente para estructuras simples."""

    dato: T
    siguiente: _NodoSimple[T] | None = None


class Pila(Generic[T]):
    """Implemente LIFO sin list; el primer nodo es el tope."""

    def __init__(self) -> None:
        """Inicialice tope y tamaño; O(1)."""
        self._tope: _NodoSimple[T] | None = None
        self._tamano = 0

    def __len__(self) -> int:
        """Devuelva el tamaño sin recorrer; O(1)."""
        return self._tamano

    def apilar(self, dato: T) -> None:
        """Inserte un nuevo tope; O(1)."""
        self._tope = _NodoSimple(dato, self._tope)
        self._tamano += 1

    def desapilar(self) -> T:
        """Retire el tope en O(1); ValueError si vacía."""
        if self._tope is None:
            raise ValueError("La pila está vacía.")
        nodo = self._tope
        self._tope = nodo.siguiente
        self._tamano -= 1
        return nodo.dato

    def ver_tope(self) -> T:
        """Consulte sin retirar; O(1), ValueError si vacía."""
        if self._tope is None:
            raise ValueError("La pila está vacía.")
        return self._tope.dato

    def __iter__(self) -> Iterator[T]:
        """Produzca los datos de tope a fondo; O(n)."""
        nodo = self._tope
        while nodo:
            yield nodo.dato
            nodo = nodo.siguiente


class Cola(Generic[T]):
    """Implemente FIFO con frente y final enlazados."""

    def __init__(self) -> None:
        """Inicialice extremos vacíos y tamaño; O(1)."""
        self._frente: _NodoSimple[T] | None = None
        self._final: _NodoSimple[T] | None = None
        self._tamano = 0

    def __len__(self) -> int:
        """Devuelva la cantidad en O(1)."""
        return self._tamano

    def encolar(self, dato: T) -> None:
        """Inserte al final en O(1)."""
        nodo = _NodoSimple(dato)
        if self._final:
            self._final.siguiente = nodo
        else:
            self._frente = nodo
        self._final = nodo
        self._tamano += 1

    def desencolar(self) -> T:
        """Retire frente en O(1); ValueError si vacía."""
        if not self._frente:
            raise ValueError("La cola está vacía.")
        nodo = self._frente
        self._frente = nodo.siguiente
        self._tamano -= 1
        if not self._frente:
            self._final = None
        return nodo.dato

    def ver_frente(self) -> T:
        """Consulte frente sin retirar; O(1), ValueError si vacía."""
        if not self._frente:
            raise ValueError("La cola está vacía.")
        return self._frente.dato

    def __iter__(self) -> Iterator[T]:
        """Produzca datos en orden de salida; O(n)."""
        nodo = self._frente
        while nodo:
            yield nodo.dato
            nodo = nodo.siguiente


@dataclass(frozen=True)
class Prioridad(Generic[T]):
    """Asocie una prioridad entera al dato sin alterar su identidad."""

    dato: T
    prioridad: int


class ColaPrioridad(Cola[Prioridad[T]]):
    """Mantenga nodos ordenados: mayor prioridad primero, empate FIFO."""

    def encolar(self, dato: Prioridad[T]) -> None:
        """Inserte después de los empates en O(n); Valide prioridad."""
        if type(dato.prioridad) is not int or dato.prioridad < 0:
            raise ValueError("La prioridad debe ser un entero no negativo.")
        nuevo = _NodoSimple(dato)
        anterior = None
        actual = self._frente
        while actual and actual.dato.prioridad >= dato.prioridad:
            anterior, actual = actual, actual.siguiente
        nuevo.siguiente = actual
        if anterior:
            anterior.siguiente = nuevo
        else:
            self._frente = nuevo
        if actual is None:
            self._final = nuevo
        self._tamano += 1


class ColaCircular(Generic[T]):
    """FIFO acotada de nodos: final.siguiente es el frente."""

    def __init__(self, capacidad: int = 8) -> None:
        """Defina capacidad positiva o lance ValueError; O(1)."""
        if type(capacidad) is not int or capacidad <= 0:
            raise ValueError("La capacidad debe ser un entero positivo.")
        self.capacidad = capacidad
        self._final: _NodoSimple[T] | None = None
        self._tamano = 0

    def __len__(self) -> int:
        """Devuelva tamaño en O(1)."""
        return self._tamano

    def encolar(self, dato: T) -> None:
        """Agregue al final; O(1), ValueError si llena sin sobrescribir."""
        if self._tamano == self.capacidad:
            raise ValueError(
                f"La cola circular está llena ({self.capacidad} turnos)."
            )
        nodo = _NodoSimple(dato)
        if self._final:
            nodo.siguiente = self._final.siguiente
            self._final.siguiente = nodo
        else:
            nodo.siguiente = nodo
        self._final = nodo
        self._tamano += 1

    def desencolar(self) -> T:
        """Retire frente; O(1), ValueError si vacía."""
        if not self._final:
            raise ValueError("La cola circular está vacía.")
        frente = self._final.siguiente
        if self._tamano == 1:
            self._final = None
        else:
            self._final.siguiente = frente.siguiente
        self._tamano -= 1
        frente.siguiente = None
        return frente.dato

    def ver_frente(self) -> T:
        """Consulte sin retirar; O(1), ValueError si vacía."""
        if not self._final:
            raise ValueError("La cola circular está vacía.")
        return self._final.siguiente.dato

    def __iter__(self) -> Iterator[T]:
        """Recorra exactamente n turnos desde el frente; O(n)."""
        nodo = self._final.siguiente if self._final else None
        for _ in range(self._tamano):
            yield nodo.dato
            nodo = nodo.siguiente
