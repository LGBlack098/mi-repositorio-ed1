"""Demostración del núcleo sin Flet: ejecute python demo.py."""

from controllers.controlador_biblioteca import ControladorBiblioteca


def crear_demo() -> ControladorBiblioteca:
    """Construya un catálogo de tres canciones ficticias en memoria."""
    controlador = ControladorBiblioteca()
    controlador.agregar(
        "Camino al sur", "Grupo Horizonte", "6", "audio/demo.wav"
    )
    controlador.agregar(
        "Luz de octubre", "Ana del Valle", "6", "audio/demo.wav"
    )
    controlador.agregar("Camino al sur", "Trío del Río", "6", "audio/demo.wav")
    controlador.crear_playlist("Para estudiar")
    controlador.crear_playlist("Favoritas")
    controlador.agregar_entrada(1, 1)
    controlador.agregar_entrada(1, 2)
    controlador.agregar_entrada(2, 3)
    # La demostración inicial no representa cambios hechos por el usuario.
    from models.estructuras.lineales import Pila

    controlador.sesion.deshacer = Pila()
    controlador.sesion.rehacer = Pila()
    return controlador


def main() -> None:
    """Muestre agregar, buscar y eliminar sin tocar nodos desde la vista."""
    controlador = crear_demo()
    for cancion in controlador.listar():
        print(
            f"{cancion.identificador}. {cancion.titulo} - "
            f"{cancion.artista} ({cancion.duracion_formateada()})"
        )
    coincidencias = controlador.listar("CAMINO")
    print(f"Coincidencias por título: {len(coincidencias)}")
    eliminada = controlador.eliminar(coincidencias[0].identificador)
    print(f"Eliminada por ID: {eliminada.identificador}")
    print(f"Canciones restantes: {len(controlador.listar())}")


if __name__ == "__main__":
    main()
