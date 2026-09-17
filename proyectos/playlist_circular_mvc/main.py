"""Punto de entrada de la aplicación Playlist Circular MVC."""

from controllers.controlador_playlist import ControladorPlaylist
from views.vista_playlist import VistaPlaylist


def main() -> None:
    """Construye las capas MVC e inicia la interfaz gráfica."""
    controlador = ControladorPlaylist()
    aplicacion = VistaPlaylist(controlador)
    aplicacion.mainloop()


if __name__ == "__main__":
    main()
