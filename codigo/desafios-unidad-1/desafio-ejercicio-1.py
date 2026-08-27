"""Unidad 1 - Tipos de Datos Abstractos (TDA) y Gestion de Memoria.
 
Solucion a los desafios propuestos, siguiendo la guia de estilo PEP 8.
Cada funcion "desafio_n" corrige el error conceptual senalado en el
enunciado original y agrega un comentario breve explicando la causa
del error.
"""
 
from copy import copy
 
 
# ---------------------------------------------------------------------
# Desafio 1: El misterio de las referencias (Gestion de Memoria)
# ---------------------------------------------------------------------
# Causa del error: "copy_data = original_data" no crea una lista nueva,
# solo una segunda variable que apunta a la MISMA lista en el heap. Por
# eso, al modificar "copy_data" tambien cambia "original_data".
# Solucion: crear una copia independiente con .copy(), list() o [:].
 
def desafio_1():
    """Duplica una lista de forma independiente (copia por valor)."""
    original_data = [10, 20, 30]
 
    # Cualquiera de estas tres formas crea una lista nueva en el heap:
    copy_data = original_data.copy()
    # copy_data = list(original_data)
    # copy_data = original_data[:]
 
    copy_data.append(40)
 
    print(f"Original: {original_data}")
    print(f"Copia: {copy_data}")
 
 