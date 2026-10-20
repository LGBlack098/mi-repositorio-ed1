"""Política musical de avance, independiente de Flet y del audio."""

from dataclasses import dataclass

from models.cancion import Cancion


@dataclass(frozen=True)
class PasoMusical:
    """Entregue pista y posición del contexto, o None al terminar."""

    cancion: Cancion | None
    contexto_id: int | None


def navegar(sesion, origen, actual_id, playlist_id, direccion, repetir):
    """Seleccione siguiente/anterior sin tocar el dispositivo de audio.

    Prioridad y FIFO interrumpen temporalmente el contexto. Las playlists
    mueven su cursor enlazado; el catálogo se recorre en O(n). Devolver
    None significa fin sin repetición. No registra una edición.
    """
    if type(direccion) is not int or direccion not in (-1, 1):
        raise ValueError("La dirección debe ser +1 o -1.")
    if direccion == 1:
        for modo in ("prioridad", "fifo"):
            if len(getattr(sesion, modo)):
                return PasoMusical(sesion.consumir(modo), actual_id)
    if origen in ("fifo", "prioridad", "turnos"):
        if direccion != 1:
            raise ValueError("Las solicitudes no tienen pista anterior.")
        return PasoMusical(sesion.consumir(origen), actual_id)
    if origen == "playlist":
        playlist = sesion.playlist(playlist_id)
        entradas = tuple(playlist.entradas)
        actual = playlist.entradas.actual()
        if not entradas or actual is None:
            return PasoMusical(None, actual_id)
        extremo = entradas[-1] if direccion == 1 else entradas[0]
        if actual == extremo and not repetir:
            cancion = (
                None
                if direccion == 1
                else sesion.biblioteca.obtener(actual.cancion_id)
            )
        else:
            cancion = sesion.mover(playlist_id, direccion)
        return PasoMusical(
            cancion, cancion.identificador if cancion else actual_id
        )
    pistas = tuple(c for c in sesion.biblioteca.listar() if c.archivo)
    if not pistas:
        raise ValueError("Añade música para escuchar.")
    indice = next(
        (i for i, c in enumerate(pistas) if c.identificador == actual_id), -1
    )
    nuevo = indice + direccion
    if nuevo >= len(pistas) and not repetir:
        return PasoMusical(None, actual_id)
    nuevo = nuevo % len(pistas) if repetir else max(0, nuevo)
    cancion = pistas[nuevo]
    return PasoMusical(cancion, cancion.identificador)
