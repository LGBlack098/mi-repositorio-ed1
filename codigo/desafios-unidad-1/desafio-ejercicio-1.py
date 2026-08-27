"""Unidad 1 - Tipos de Datos Abstractos (TDA) y Gestion de Memoria.

Solucion de los desafios planteados en la unidad, respetando las
recomendaciones de la guia de estilo PEP 8. Cada funcion muestra
la solucion al problema indicado y explica brevemente el motivo
del error y la forma utilizada para corregirlo.
"""

from copy import copy


# ---------------------------------------------------------------------
# Desafio 1: El misterio de las referencias (Gestion de Memoria)
# ---------------------------------------------------------------------
# Al escribir "copy_data = original_data", no se genera una nueva lista.
# Ambas variables hacen referencia al mismo objeto en memoria, por lo
# que cualquier cambio realizado mediante una de ellas tambien afecta
# a la otra.
#
# Para evitar esto, se debe crear una copia independiente de la lista.
# En este caso se utiliza el metodo .copy(), que genera un nuevo objeto.


def desafio_1():
    """Crea una copia independiente de una lista y modifica la copia."""
    original_data = [10, 20, 30]

    # .copy() permite crear una nueva lista sin modificar la original.
    copy_data = original_data.copy()
    # copy_data = list(original_data)
    # copy_data = original_data[:]

    copy_data.append(40)

    print(f"Original: {original_data}")
    print(f"Copia: {copy_data}")