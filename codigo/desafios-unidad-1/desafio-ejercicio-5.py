# ---------------------------------------------------------------------
# Desafio 5: TDA Automovil y Garaje (Gestion de Objetos en Colecciones)
# Asignatura: Estructura de Datos 1 - UAGRM
# ---------------------------------------------------------------------
class Automovil:
    """TDA Automovil con marca, modelo y color."""
 
    def __init__(self, marca, modelo, color):
        self.marca = marca
        self.modelo = modelo
        self.color = color
 
    def __str__(self):
        return f"{self.color} {self.marca} {self.modelo}"
 
 
class Garaje:
    """TDA Garaje que almacena una coleccion de automoviles."""
 
    def __init__(self):
        self.automoviles = []
 
    def agregar_automovil(self, auto):
        """Agrega un automovil a la coleccion del garaje."""
        self.automoviles.append(auto)
 
    def mostrar_automoviles(self):
        """Imprime todos los automoviles almacenados en el garaje."""
        print("Automoviles en el garaje:")
        for i, auto in enumerate(self.automoviles):
            print(f"  {i + 1}. {auto}")
 
 
def desafio_5():
    """Agrega dos autos distintos, cada uno con su propia instancia."""
    mi_garaje = Garaje()
 
    auto_1 = Automovil("Toyota", "Corolla", "Rojo")
    mi_garaje.agregar_automovil(auto_1)
 
    # ERROR original: se reutilizaba "auto_temporal" y solo se
    # modificaban sus atributos, por lo que el garaje terminaba con
    # el MISMO objeto repetido dos veces. La solucion es crear una
    # instancia nueva para cada automovil.
    auto_2 = Automovil("Honda", "Civic", "Azul")
    mi_garaje.agregar_automovil(auto_2)
 
    mi_garaje.mostrar_automoviles()
 
 