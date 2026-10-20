"""JSON versionado y validación transaccional antes de reconstruir nodos."""

import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from models.cancion import Cancion
from models.playlist import Entrada
from models.sesion import Estado, FotoPlaylist

LIMITE_JSON = 5 * 1024 * 1024


def entero(valor: object, nombre: str) -> int:
    """Exija entero positivo exacto; ValueError rechaza bool y texto."""
    if type(valor) is not int or valor <= 0:
        raise ValueError(f"{nombre} debe ser un entero positivo.")
    return valor


def decodificar(texto: str) -> Estado:
    """Valide esquema, unicidad, referencias y cursores; O(n + p + e).

    JSON inválido o incompatible produce ValueError sin mutar el modelo.
    Los sets/dict son índices temporales de validación, no estructuras
    académicas. El disco no guarda nodos ni punteros.
    """
    if len(texto.encode("utf-8")) > LIMITE_JSON:
        raise ValueError("El JSON supera el límite de 5 MB.")
    try:
        datos = json.loads(texto)
        if type(datos) is not dict or type(datos.get("version")) is not int:
            raise ValueError("Falta la versión del documento.")
        if datos["version"] != 1:
            raise ValueError("Versión JSON no compatible.")
        if type(datos["canciones"]) is not list:
            raise ValueError("El catálogo JSON debe ser una secuencia.")
        if type(datos["playlists"]) is not list:
            raise ValueError("Las playlists deben ser una secuencia.")
        canciones = tuple(Cancion(**c) for c in datos["canciones"])
        ids = {c.identificador for c in canciones}
        if len(ids) != len(canciones):
            raise ValueError("Hay IDs de canción repetidos.")
        playlists = []
        ids_playlist: set[int] = set()
        ids_entrada: set[int] = set()
        for p in datos["playlists"]:
            identificador = entero(p["identificador"], "ID playlist")
            if identificador in ids_playlist:
                raise ValueError("Hay IDs de playlist repetidos.")
            ids_playlist.add(identificador)
            nombre = p["nombre"]
            if not isinstance(nombre, str) or not nombre.strip():
                raise ValueError("Nombre de playlist inválido.")
            if type(p["entradas"]) is not list:
                raise ValueError("Las entradas deben ser una secuencia.")
            entradas = []
            locales: set[int] = set()
            for e in p["entradas"]:
                eid = entero(e["identificador"], "ID entrada")
                cid = entero(e["cancion_id"], "ID canción")
                if eid in ids_entrada or cid not in ids:
                    raise ValueError("Entrada duplicada o canción ausente.")
                ids_entrada.add(eid)
                locales.add(eid)
                entradas.append(Entrada(eid, cid))
            actual = p["actual_id"]
            if entradas:
                entero(actual, "Cursor actual")
                if actual not in locales:
                    raise ValueError("El cursor no pertenece a la playlist.")
            elif actual is not None:
                raise ValueError("Una playlist vacía no tiene cursor.")
            playlists.append(
                FotoPlaylist(
                    identificador, nombre.strip(), tuple(entradas), actual
                )
            )
        marcas = tuple(
            entero(datos[campo], campo)
            for campo in (
                "siguiente_cancion",
                "siguiente_playlist",
                "siguiente_entrada",
            )
        )
        for marca, usados in zip(marcas, (ids, ids_playlist, ids_entrada)):
            if marca <= max(usados, default=0):
                raise ValueError(
                    "El contador de IDs reutilizaría identidades."
                )
        return Estado(canciones, tuple(playlists), *marcas)
    except (
        KeyError,
        TypeError,
        json.JSONDecodeError,
        RecursionError,
    ) as error:
        raise ValueError("JSON inválido: revisa campos y tipos.") from error


def codificar(estado: Estado) -> str:
    """Convierta instantánea a JSON legible UTF-8; O(n + p + e)."""
    datos = asdict(estado)
    datos["version"] = 1
    return json.dumps(datos, ensure_ascii=False, indent=2)


def guardar(ruta: Path, estado: Estado) -> None:
    """Escriba de forma atómica; un fallo no trunca el archivo anterior.

    El temporal se crea en el mismo directorio para que os.replace
    reemplace en el mismo volumen. OSError se comunica al usuario.
    """
    texto = codificar(estado)
    decodificar(texto)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=ruta.parent,
            suffix=".tmp",
            delete=False,
        ) as archivo:
            temporal = Path(archivo.name)
            archivo.write(texto)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, ruta)
    finally:
        if temporal and temporal.exists():
            temporal.unlink()


def cargar(ruta: Path) -> Estado:
    """Lea hasta 5 MB y valide; OSError o ValueError si falla."""
    with ruta.open("rb") as archivo:
        contenido = archivo.read(LIMITE_JSON + 1)
    if len(contenido) > LIMITE_JSON:
        raise ValueError("El JSON supera el límite de 5 MB.")
    try:
        return decodificar(contenido.decode("utf-8-sig"))
    except UnicodeDecodeError as error:
        raise ValueError("El JSON debe estar codificado en UTF-8.") from error
