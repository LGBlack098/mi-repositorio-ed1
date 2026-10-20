"""Estime memoria superficial de nodos sin recorrer sus datos."""

from sys import getsizeof


def estimar_nodos(primero, cantidad: int) -> int:
    """Sume nodo y diccionario de atributos; excluya datos y referidos.

    Acota el recorrido por cantidad, incluso en estructuras circulares.
    Es una aproximación de Python, no RAM del proceso ni tamaño profundo.
    Solo las estructuras llaman a esta función con sus nodos privados.
    """
    total = 0
    nodo = primero
    for _ in range(cantidad):
        total += getsizeof(nodo) + getsizeof(vars(nodo))
        nodo = nodo.siguiente
    return total
