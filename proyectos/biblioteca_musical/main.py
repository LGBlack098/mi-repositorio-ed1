"""Entrada local: python main.py [--web] [--port 8550] [--sin-demo]."""

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path

import flet as ft

from controllers.controlador_biblioteca import ControladorBiblioteca
from demo import crear_demo
from generar_demo import generar
from services.persistencia import cargar, codificar
from views.vista_sonoteca import VistaSonoteca

RECURSOS = Path(__file__).resolve().parent
BASE = (
    Path(os.environ["SONOTECA_DATA_DIR"])
    if os.getenv("SONOTECA_DATA_DIR")
    else Path(os.environ["FLET_APP_STORAGE_DATA"])
    if os.getenv("FLET_APP_STORAGE_DATA")
    else (
        Path(sys.executable).resolve().parent / "SonotecaDatos"
        if getattr(sys, "frozen", False)
        else RECURSOS
    )
)


def construir_controlador(ruta: Path, demo: bool = False):
    """Cargue guardado si existe; ante error no sobrescriba el archivo.

    Devuelve controlador y aviso de inicio. Un JSON inválido deja una
    sesión vacía; el usuario conserva el archivo para recuperarlo.
    """
    controlador = ControladorBiblioteca()
    if ruta.exists():
        try:
            controlador.importar(codificar(cargar(ruta)))
            return controlador, "Biblioteca guardada recuperada."
        except (OSError, ValueError) as error:
            return controlador, f"No se cargó el guardado: {error}"
    return (crear_demo() if demo else controlador), (
        "Demostración: títulos ficticios y audio sintético de 6 s."
        if demo
        else ""
    )


def main(pagina: ft.Page) -> None:
    """Componga modelo, controlador y vista para cada sesión nueva."""
    controlador, aviso = construir_controlador(BASE / "data/musica.json")
    vista = VistaSonoteca(controlador, BASE)
    vista.montar(pagina)
    vista._avisar(aviso)


def ejecutar() -> None:
    """Configure destino local, datos y assets antes de iniciar Flet."""
    if getattr(sys, "frozen", False):
        BASE.mkdir(parents=True, exist_ok=True)
        registro = (BASE / "sonoteca.log").open("a", encoding="utf-8")
        # Un EXE sin consola no tiene stdout/stderr. El servidor web y
        # sus formatters sí los consultan; proporcionar un archivo real.
        if sys.stdout is None:
            sys.stdout = registro
        if sys.stderr is None:
            sys.stderr = registro
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--web", action="store_true")
    parser.add_argument("--sin-abrir", action="store_true")
    parser.add_argument("--port", type=int, default=8550)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--movil", action="store_true")
    parser.add_argument("--sin-demo", action="store_true")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument(
        "--datos", type=Path, default=BASE / "data/musica.json"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if BASE != RECURSOS:
        (BASE / "assets/audio").mkdir(parents=True, exist_ok=True)
        for nombre in ("sonoteca.ico", "sonoteca.png"):
            shutil.copyfile(
                RECURSOS / "assets" / nombre, BASE / "assets" / nombre
            )
        destino = BASE / "assets/audio/demo.wav"
        if not destino.exists():
            shutil.copyfile(RECURSOS / "assets/audio/demo.wav", destino)
    if args.sin_abrir:
        os.environ["FLET_FORCE_WEB_SERVER"] = "true"
    if not (BASE / "assets/audio/demo.wav").exists():
        generar(BASE / "assets/audio/demo.wav")

    def inicio(pagina: ft.Page) -> None:
        """Cree una sesión MVC por conexión usando la ruta elegida."""
        if args.movil:
            pagina.window.width = 430
            pagina.window.height = 720
        controlador, aviso = construir_controlador(
            args.datos, args.demo and not args.sin_demo
        )
        vista = VistaSonoteca(controlador, BASE, args.datos)
        vista.montar(pagina)
        vista._avisar(aviso)

    ft.run(
        inicio,
        assets_dir=str(BASE / "assets"),
        host=args.host,
        port=args.port,
        view=(
            None
            if args.sin_abrir
            else ft.AppView.WEB_BROWSER
            if args.web
            else ft.AppView.FLET_APP
        ),
    )


if __name__ == "__main__":
    try:
        ejecutar()
    except Exception:
        logging.exception("No se pudo iniciar Sonoteca")
        raise
