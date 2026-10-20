"""Compare primitivas reales en datos aislados, sin editar la biblioteca."""

from statistics import median
from time import perf_counter_ns

from models.estructuras.lista_doble import ListaDoblementeEnlazada


def comparar() -> tuple:
    """Mida inserción final y búsqueda ausente para tres tamaños.

    Use cinco lotes de 100 repeticiones por operación. La construcción
    inicial queda fuera del cronómetro; la inserción incluye crear nodo.
    Devuelve ns/op medianos. No certifica complejidad por medición sola.
    """
    resultados = []
    for cantidad in (100, 1000, 5000):
        insertar, buscar = [], []
        for _ in range(5):
            lista = ListaDoblementeEnlazada()
            busqueda = ListaDoblementeEnlazada()
            for i in range(cantidad):
                lista.agregar_final(i)
                busqueda.agregar_final(i)
            inicio = perf_counter_ns()
            for i in range(100):
                lista.agregar_final(i)
            insertar.append((perf_counter_ns() - inicio) / 100)
            inicio = perf_counter_ns()
            for _ in range(100):
                busqueda.buscar(lambda x: x == -1)
            buscar.append((perf_counter_ns() - inicio) / 100)
        resultados.append((cantidad, median(insertar), median(buscar)))
    return tuple(resultados)
