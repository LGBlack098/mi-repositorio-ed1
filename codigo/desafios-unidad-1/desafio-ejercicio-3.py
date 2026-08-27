# ---------------------------------------------------------------------
# Modulo para el Desafio 3: Enlazado de Nodos en el Heap (Nodos Dinamicos)
# Asignatura: Estructura de Datos 1 - UAGRM
# ---------------------------------------------------------------------
class Nodo:
    """Nodo simple para una lista enlazada."""
 
    def __init__(self, valor):
        self.valor = valor
        self.siguiente = None  # "puntero" al siguiente nodo en el heap
 
 
def desafio_3():
    """Encadena dos nodos sin perder la referencia al primero."""
    nodo_1 = Nodo("Datos Importantes 1")
    nodo_2 = Nodo("Datos Importantes 2")
 
    # ERROR original: "contenedor = Nodo(...)" reasignaba la variable
    # de control al segundo nodo en vez de enlazarlo al primero.
    nodo_1.siguiente = nodo_2
    contenedor = nodo_1  # "contenedor" sigue siendo el inicio de la lista
 
    print(f"Contenido actual: {contenedor.valor}")
    if contenedor.siguiente is not None:
        print(f"Siguiente nodo: {contenedor.siguiente.valor}")
    else:
        print("ERROR: se perdio la referencia al segundo nodo.")