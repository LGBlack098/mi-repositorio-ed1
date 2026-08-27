# ---------------------------------------------------------------------
# Desafio 2: Implementacion de TDA Pila (Stack)
# ---------------------------------------------------------------------
class Stack:
    """Representa una pila (LIFO) con sus operaciones principales."""

    def __init__(self):
        self.items = []

    def is_empty(self):
        """Comprueba si la pila se encuentra sin elementos."""
        # En el codigo original la condicion estaba al reves, ya que
        # se comprobaba si la cantidad de elementos era mayor que cero.
        return len(self.items) == 0

    def push(self, item):
        """Incorpora un nuevo elemento en la parte superior de la pila."""
        # El problema anterior reemplazaba toda la lista por el nuevo
        # elemento. Con append() se conserva lo anterior y se agrega
        # el nuevo elemento al final de la pila.
        self.items.append(item)

    def pop(self):
        """Retira y devuelve el elemento que esta en el tope."""
        # Antes se utilizaba remove(-1), lo cual no permite obtener
        # correctamente el ultimo elemento de la lista. Tambien es
        # necesario comprobar primero que la pila tenga elementos.
        if self.is_empty():
            raise IndexError("No se puede hacer pop: la pila esta vacia")
        return self.items.pop()


def desafio_2():
    """Realiza una prueba sencilla de las operaciones de la pila."""
    mi_pila = Stack()
    mi_pila.push("A")
    mi_pila.push("B")

    print("Esta vacia?", mi_pila.is_empty())
    print("Elemento sacado:", mi_pila.pop())