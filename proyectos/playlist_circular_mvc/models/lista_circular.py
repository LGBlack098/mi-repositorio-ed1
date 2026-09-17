"""Implementación del TDA lista enlazada circular simple."""

from __future__ import annotations

from dataclasses import dataclass

from models.cancion import Cancion


@dataclass(slots=True)
class _NodoCancion:
    """Nodo interno; no forma parte de la interfaz pública del TDA."""

    dato: Cancion
    siguiente: _NodoCancion | None = None


class ListaCircular:
    """Playlist basada en una lista enlazada circular simple.

    Conserva referencias a la cabeza, la cola y la canción actual. Gracias a
    la cola, insertar al final es O(1). La cola siempre enlaza con la cabeza.
    """

    def __init__(self) -> None:
        self._cabeza: _NodoCancion | None = None
        self._cola: _NodoCancion | None = None
        self._actual: _NodoCancion | None = None
        self._tamanio = 0
        self._siguiente_id = 1

    def agregar(self, titulo: str, artista: str) -> Cancion:
        """Agrega una canción al final y la retorna. Complejidad O(1)."""
        cancion = Cancion(self._siguiente_id, titulo, artista)
        self._siguiente_id += 1
        nuevo = _NodoCancion(cancion)

        if self._cabeza is None:
            nuevo.siguiente = nuevo
            self._cabeza = nuevo
            self._cola = nuevo
            self._actual = nuevo
        else:
            nuevo.siguiente = self._cabeza
            assert self._cola is not None
            self._cola.siguiente = nuevo
            self._cola = nuevo

        self._tamanio += 1
        return cancion

    def seleccionar(self, identificador: int) -> Cancion | None:
        """Selecciona una canción por ID. Complejidad O(n)."""
        nodo = self._buscar_nodo(identificador)
        if nodo is None:
            return None
        self._actual = nodo
        return nodo.dato

    def avanzar(self) -> Cancion | None:
        """Avanza a la canción siguiente, volviendo al inicio. O(1)."""
        if self._actual is None:
            return None
        assert self._actual.siguiente is not None
        self._actual = self._actual.siguiente
        return self._actual.dato

    def obtener_actual(self) -> Cancion | None:
        """Retorna la canción actual sin modificar la lista. O(1)."""
        return self._actual.dato if self._actual is not None else None

    def eliminar(self, identificador: int) -> bool:
        """Elimina exactamente la canción indicada por su ID. O(n)."""
        if self._cabeza is None or self._cola is None:
            return False

        anterior = self._cola
        nodo = self._cabeza

        for _ in range(self._tamanio):
            if nodo.dato.identificador == identificador:
                if self._tamanio == 1:
                    self._cabeza = None
                    self._cola = None
                    self._actual = None
                else:
                    assert nodo.siguiente is not None
                    anterior.siguiente = nodo.siguiente

                    if nodo is self._cabeza:
                        self._cabeza = nodo.siguiente
                    if nodo is self._cola:
                        self._cola = anterior
                    if nodo is self._actual:
                        self._actual = nodo.siguiente

                    assert self._cola is not None
                    self._cola.siguiente = self._cabeza

                self._tamanio -= 1
                return True

            anterior = nodo
            assert nodo.siguiente is not None
            nodo = nodo.siguiente

        return False

    def listar(self) -> list[Cancion]:
        """Retorna una copia lineal de las canciones. Complejidad O(n)."""
        canciones: list[Cancion] = []
        nodo = self._cabeza

        for _ in range(self._tamanio):
            assert nodo is not None
            canciones.append(nodo.dato)
            nodo = nodo.siguiente

        return canciones

    def buscar(self, texto: str) -> list[Cancion]:
        """Busca coincidencias en título o artista. Complejidad O(n)."""
        consulta = texto.casefold()
        return [
            cancion
            for cancion in self.listar()
            if consulta in cancion.titulo.casefold()
            or consulta in cancion.artista.casefold()
        ]

    def esta_vacia(self) -> bool:
        """Indica si la lista no contiene canciones. Complejidad O(1)."""
        return self._tamanio == 0

    def __len__(self) -> int:
        """Retorna el número de canciones en O(1)."""
        return self._tamanio

    def _buscar_nodo(self, identificador: int) -> _NodoCancion | None:
        nodo = self._cabeza
        for _ in range(self._tamanio):
            assert nodo is not None
            if nodo.dato.identificador == identificador:
                return nodo
            nodo = nodo.siguiente
        return None
