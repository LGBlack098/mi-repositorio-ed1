"""
Módulo que implementa un Árbol Binario de Búsqueda (BST) para números enteros.
"""


class NodoArbol:
    """Nodo individual de un árbol binario de búsqueda."""

    def __init__(self, valor: int):
        """Inicializa un nodo con un valor y sin hijos.

        Args:
            valor (int): Valor numérico almacenado en el nodo.
        """
        self.valor = valor
        self.izquierdo = None
        self.derecho = None


class ArbolBinarioBusqueda:
    """Árbol binario de búsqueda (BST) para números enteros."""

    def __init__(self):
        """Inicializa un árbol vacío."""
        self._raiz = None

    # ---------- Inserción ----------
    def insertar(self, valor: int) -> None:
        """Inserta un nuevo valor en el árbol.

        Args:
            valor (int): Valor entero a insertar.
        """
        if self._raiz is None:
            self._raiz = NodoArbol(valor)
        else:
            self._insertar_recursivo(self._raiz, valor)

    def _insertar_recursivo(self, nodo_actual: NodoArbol, valor: int) -> None:
        """Inserta recursivamente en el subárbol correcto.

        Args:
            nodo_actual (NodoArbol): Nodo desde donde se evalúa.
            valor (int): Valor a insertar.
        """
        if valor < nodo_actual.valor:
            if nodo_actual.izquierdo is None:
                nodo_actual.izquierdo = NodoArbol(valor)
            else:
                self._insertar_recursivo(nodo_actual.izquierdo, valor)
        else:
            if nodo_actual.derecho is None:
                nodo_actual.derecho = NodoArbol(valor)
            else:
                self._insertar_recursivo(nodo_actual.derecho, valor)

    # ---------- Búsqueda ----------
    def buscar(self, valor: int) -> bool:
        """Busca un valor en el árbol.

        Args:
            valor (int): Valor a buscar.

        Returns:
            bool: True si el valor existe, False en caso contrario.
        """
        return self._buscar_recursivo(self._raiz, valor)

    def _buscar_recursivo(self, nodo_actual: NodoArbol, valor: int) -> bool:
        """Busca recursivamente en el subárbol.

        Args:
            nodo_actual (NodoArbol): Nodo actual de la búsqueda.
            valor (int): Valor a buscar.

        Returns:
            bool: True si el valor existe, False en caso contrario.
        """
        if nodo_actual is None:
            return False
        if valor == nodo_actual.valor:
            return True
        elif valor < nodo_actual.valor:
            return self._buscar_recursivo(nodo_actual.izquierdo, valor)
        else:
            return self._buscar_recursivo(nodo_actual.derecho, valor)

    # ---------- Recorridos ----------
    def recorrido_inorden(self) -> list[int]:
        """Devuelve los valores del árbol en orden ascendente.

        Returns:
            list[int]: Lista de valores en orden inorden.
        """
        resultado = []
        self._inorden(self._raiz, resultado)
        return resultado

    def _inorden(self, nodo: NodoArbol, resultado: list[int]) -> None:
        """Recorrido inorden (izquierdo, raíz, derecho)."""
        if nodo:
            self._inorden(nodo.izquierdo, resultado)
            resultado.append(nodo.valor)
            self._inorden(nodo.derecho, resultado)

    def recorrido_preorden(self) -> list[int]:
        """Devuelve los valores en preorden (raíz, izquierdo, derecho).

        Returns:
            list[int]: Lista de valores en preorden.
        """
        resultado = []
        self._preorden(self._raiz, resultado)
        return resultado

    def _preorden(self, nodo: NodoArbol, resultado: list[int]) -> None:
        """Recorrido preorden (raíz, izquierdo, derecho)."""
        if nodo:
            resultado.append(nodo.valor)
            self._preorden(nodo.izquierdo, resultado)
            self._preorden(nodo.derecho, resultado)

    def recorrido_postorden(self) -> list[int]:
        """Devuelve los valores en postorden (izquierdo, derecho, raíz).

        Returns:
            list[int]: Lista de valores en postorden.
        """
        resultado = []
        self._postorden(self._raiz, resultado)
        return resultado

    def _postorden(self, nodo: NodoArbol, resultado: list[int]) -> None:
        """Recorrido postorden (izquierdo, derecho, raíz)."""
        if nodo:
            self._postorden(nodo.izquierdo, resultado)
            self._postorden(nodo.derecho, resultado)
            resultado.append(nodo.valor)

    # ---------- Eliminación ----------
    def eliminar(self, valor: int) -> None:
        """Elimina un valor del árbol si existe.

        Args:
            valor (int): Valor a eliminar.
        """
        self._raiz = self._eliminar_recursivo(self._raiz, valor)

    def _eliminar_recursivo(self, nodo: NodoArbol, valor: int) -> NodoArbol:
        """Elimina recursivamente el valor del subárbol.

        Args:
            nodo (NodoArbol): Raíz del subárbol actual.
            valor (int): Valor a eliminar.

        Returns:
            NodoArbol: La nueva raíz del subárbol modificado.
        """
        if nodo is None:
            return nodo

        if valor < nodo.valor:
            nodo.izquierdo = self._eliminar_recursivo(nodo.izquierdo, valor)
        elif valor > nodo.valor:
            nodo.derecho = self._eliminar_recursivo(nodo.derecho, valor)
        else:
            # Nodo con un solo hijo o sin hijos
            if nodo.izquierdo is None:
                return nodo.derecho
            elif nodo.derecho is None:
                return nodo.izquierdo

            # Nodo con dos hijos: obtener el sucesor inorden (mínimo del subárbol derecho)
            nodo.valor = self._minimo_valor(nodo.derecho)
            nodo.derecho = self._eliminar_recursivo(nodo.derecho, nodo.valor)

        return nodo

    def _minimo_valor(self, nodo: NodoArbol) -> int:
        """Encuentra el valor mínimo en un subárbol.

        Args:
            nodo (NodoArbol): Raíz del subárbol.

        Returns:
            int: Valor mínimo encontrado.
        """
        actual = nodo
        while actual.izquierdo is not None:
            actual = actual.izquierdo
        return actual.valor


if __name__ == "__main__":
    # Crear un árbol y añadir valores
    arbol = ArbolBinarioBusqueda()
    valores = [50, 30, 70, 20, 40, 60, 80]

    for valor in valores:
        arbol.insertar(valor)

    # Mostrar recorridos
    print("Recorrido inorden:", arbol.recorrido_inorden())
    print("Recorrido preorden:", arbol.recorrido_preorden())
    print("Recorrido postorden:", arbol.recorrido_postorden())

    # Probar búsqueda
    print("Buscar 40:", arbol.buscar(40))
    print("Buscar 100:", arbol.buscar(100))

    # Probar eliminación
    arbol.eliminar(20)
    print("Después de eliminar 20, inorden:", arbol.recorrido_inorden())
    arbol.eliminar(30)
    print("Después de eliminar 30, inorden:", arbol.recorrido_inorden())
    arbol.eliminar(50)
    print("Después de eliminar 50 (raíz), inorden:", arbol.recorrido_inorden())