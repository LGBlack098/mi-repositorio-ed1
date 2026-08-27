# ---------------------------------------------------------------------
# Desafio 4: TDA Punto y Circunferencia (Paso por Referencia vs. Valor)
# Asignatura: Estructura de Datos 1 - UAGRM
# ---------------------------------------------------------------------
class Punto:
    """TDA Punto con coordenadas (x, y)."""
 
    def __init__(self, x, y):
        self.x = x
        self.y = y
 
    def __str__(self):
        return f"({self.x}, {self.y})"
 
 
class Circunferencia:
    """TDA Circunferencia definida por un centro (Punto) y un radio."""
 
    def __init__(self, centro, radio):
        # ERROR original: "self.centro = centro" guardaba la referencia
        # directa al Punto recibido. Se copia para que la circunferencia
        # tenga sus propias coordenadas, independientes del original.
        self.centro = copy(centro)
        self.radio = radio
 
    def __str__(self):
        return (f"Circunferencia con centro en {self.centro} "
                f"y radio {self.radio}")
 
 
def desafio_4():
    """Verifica que la circunferencia conserve su centro original."""
    mi_punto_original = Punto(1, 2)
    mi_circunferencia = Circunferencia(mi_punto_original, 5)
 
    print(f"Circunferencia inicial: {mi_circunferencia}")
 
    mi_punto_original.x = 10
    mi_punto_original.y = 20
 
    print("Circunferencia despues de modificar el punto original: "
          f"{mi_circunferencia}")
 