# ---------------------------------------------------------------------
# Desafio 6: TDA Linea (Inmutabilidad Conceptual con Objetos Mutables)
# Asignatura: Estructura de Datos 1 - UAGRM
# ---------------------------------------------------------------------
class Punto:
    """TDA Punto con coordenadas (x, y)."""
 
    def __init__(self, x, y):
        self.x = x
        self.y = y
 
    def __str__(self):
        return f"({self.x}, {self.y})"
 
 
class Linea:
    """TDA Linea definida por un punto de inicio y un punto final."""
 
    def __init__(self, inicio, fin):
        # ERROR original: se guardaban las referencias directas a los
        # Puntos recibidos. Se copian para que la Linea quede
        # "congelada" al momento de crearse.
        self.inicio = copy(inicio)
        self.fin = copy(fin)
 
    def __str__(self):
        return f"Linea de {self.inicio} a {self.fin}"
 
 
def desafio_6():
    """Verifica que la linea no cambie al modificar los puntos originales."""
    punto_a = Punto(0, 0)
    punto_b = Punto(5, 5)
 
    mi_linea = Linea(punto_a, punto_b)
    print(f"Linea original: {mi_linea}")
 
    punto_a.x = 10
    punto_a.y = 10
 
    print(f"Linea despues de modificar el punto 'A': {mi_linea}")