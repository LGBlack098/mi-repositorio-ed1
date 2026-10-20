"""Diagramas del estado real a partir de instantáneas públicas."""

import flet as ft


def cadena(titulo, etiquetas, flecha="→", circular=False, cursor=None):
    """Dibuje nodos ordenados y enlaces; resalte el cursor si existe."""
    controles = []
    for indice, texto in enumerate(etiquetas):
        if indice:
            controles.append(
                ft.Icon(
                    ft.Icons.SWAP_HORIZ
                    if flecha == "⇄"
                    else ft.Icons.ARROW_FORWARD,
                    size=24,
                    color="#70E0B1",
                )
            )
        controles.append(
            ft.Container(
                ft.Text(texto),
                padding=14,
                border_radius=10,
                bgcolor="#225B68" if cursor == indice else "#293549",
            )
        )
    if not controles:
        controles.append(ft.Text("Vacía · extremos = None"))
    leyenda = (
        "↻ El último vuelve al primero." if circular and etiquetas else ""
    )
    return ft.Container(
        ft.Column(
            [
                ft.Text(titulo, size=18, weight=ft.FontWeight.BOLD),
                ft.Row(controles, scroll=ft.ScrollMode.AUTO),
                ft.Text(leyenda, color="#70E0B1"),
            ]
        ),
        padding=18,
        bgcolor="#1A2332",
        border_radius=14,
    )


def pila(titulo: str, etiquetas: tuple[str, ...]) -> ft.Container:
    """Dibuje bloques verticales con el tope arriba, sin alterar orden."""
    return ft.Container(
        ft.Column(
            [
                ft.Text(titulo, size=18, weight=ft.FontWeight.BOLD),
                ft.Text("TOPE (arriba)", color="#70E0B1"),
                *(
                    ft.Container(
                        ft.Text(texto),
                        bgcolor="#293549",
                        padding=10,
                        border_radius=8,
                    )
                    for texto in etiquetas
                ),
                *([] if etiquetas else [ft.Text("Vacía · tope = None")]),
            ]
        ),
        padding=18,
        bgcolor="#1A2332",
        border_radius=14,
        col={"xs": 12, "md": 6},
    )


def visualizar(datos: dict, playlist_id, solo_colas=False) -> list:
    """Dibuje extremos, orden, topes y cursor después de cada operación.

    Los diagramas leen la misma instantánea que las tarjetas. No existe
    un catálogo de dibujo separado ni acceso directo a nodos.
    """
    estado = datos["estado"]
    nombres = {c.identificador: c.titulo for c in estado.canciones}
    playlists = {p.identificador: p.nombre for p in estado.playlists}
    controles = []
    if not solo_colas:
        controles.extend(
            [
                ft.Text("Estructuras en vivo", size=26),
                ft.Text(datos["evento"], color="#70E0B1"),
                ft.Text(
                    f"{len(estado.canciones)} canciones · "
                    f"{len(estado.playlists)} playlists · "
                    f"{sum(len(p.entradas) for p in estado.playlists)} "
                    "apariciones"
                ),
                cadena(
                    "Catálogo doble · cabeza izquierda / cola derecha",
                    tuple(
                        f"#{c.identificador} {c.titulo}"
                        for c in estado.canciones
                    ),
                    "⇄",
                ),
            ]
        )
        for playlist in estado.playlists:
            if (
                playlist_id is not None
                and playlist.identificador != playlist_id
            ):
                continue
            cursor = next(
                (
                    i
                    for i, e in enumerate(playlist.entradas)
                    if e.identificador == playlist.actual_id
                ),
                None,
            )
            controles.append(
                cadena(
                    f"Playlist circular: {playlist.nombre} · actual resaltado",
                    tuple(
                        f"Entrada {e.identificador}\n{nombres[e.cancion_id]}"
                        for e in playlist.entradas
                    ),
                    "⇄",
                    True,
                    cursor,
                )
            )
        controles.extend(
            [
                ft.ResponsiveRow(
                    [
                        pila("DESHACER · LIFO", datos["deshacer"]),
                        pila("REHACER · LIFO", datos["rehacer"]),
                    ]
                ),
                ft.Text(
                    "Apilar/desapilar O(1). Restaurar la edición reconstruye "
                    "instantáneas O(canciones + entradas + playlists)."
                ),
            ]
        )
    controles.extend(
        [
            cadena(
                "FIFO · frente izquierda / final derecha · "
                "insertar/retirar O(1)",
                tuple(nombres[c] for c in datos["fifo"]),
            ),
            cadena(
                "Prioridad · mayor primero, empate FIFO · insertar O(q)",
                tuple(
                    f"P{s.prioridad}: {nombres[s.dato]}"
                    for s in datos["prioridad"]
                ),
            ),
            cadena(
                "Cola circular · frente izquierda · máximo 8 turnos",
                tuple(playlists[p] for p in datos["turnos"]),
                circular=True,
            ),
        ]
    )
    return controles
