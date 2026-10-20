"""Genere el catálogo de funciones desde docstrings reales, sin importar UI."""

import ast
from pathlib import Path


def generar_documentacion(base: Path) -> Path:
    """Escriba API.md con cada módulo, clase y función de la aplicación.

    Leer AST evita ejecutar módulos o abrir servicios. El orden de cada
    archivo se conserva y las descripciones salen del código vigente.
    """
    lineas = [
        "# Catálogo de funciones y clases",
        "",
        "Generado con `python documentar.py`. Las explicaciones proceden",
        "de las docstrings del código. Para costos globales, consultar",
        "[GUIA_DEFENSA.md](GUIA_DEFENSA.md).",
        "",
    ]
    rutas = sorted(
        ruta
        for ruta in base.rglob("*.py")
        if not any(
            parte in ruta.parts
            for parte in (".venv", "tests", "build", "dist", "__pycache__")
        )
    )

    def agregar(nodos, prefijo="") -> None:
        """Visite definiciones y copie su contrato sin inferir funciones."""
        for nodo in nodos:
            if isinstance(
                nodo, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                nombre = f"{prefijo}{nodo.name}"
                lineas.extend(
                    [
                        f"### `{nombre}`",
                        "",
                        ast.get_docstring(nodo) or "Sin documentación.",
                        "",
                    ]
                )
                if isinstance(nodo, ast.ClassDef):
                    agregar(nodo.body, f"{nombre}.")

    for ruta in rutas:
        relativo = ruta.relative_to(base).as_posix()
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        lineas.extend(
            [
                f"## [{relativo}](../{relativo})",
                "",
                ast.get_docstring(arbol) or "",
                "",
            ]
        )
        agregar(arbol.body)
    destino = base / "docs/API.md"
    destino.write_text("\n".join(lineas), encoding="utf-8")
    return destino


if __name__ == "__main__":
    print(generar_documentacion(Path(__file__).resolve().parent))
