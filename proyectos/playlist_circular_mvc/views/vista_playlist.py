"""Interfaz Tkinter para administrar la playlist circular."""

import tkinter as tk
from tkinter import messagebox, ttk

from controllers.controlador_playlist import (
    ControladorPlaylist,
    ErrorDeValidacion,
)
from models.cancion import Cancion


class VistaPlaylist(tk.Tk):
    """Ventana principal; solo contiene lógica de presentación."""

    def __init__(self, controlador: ControladorPlaylist) -> None:
        super().__init__()
        self._controlador = controlador

        self.title("Playlist Circular · MVC")
        self.geometry("760x500")
        self.minsize(680, 440)

        self._titulo = tk.StringVar()
        self._artista = tk.StringVar()
        self._filtro = tk.StringVar()
        self._reproduccion = tk.StringVar(value="Ninguna canción seleccionada")
        self._estado = tk.StringVar(value="Playlist vacía")

        self._crear_interfaz()
        self._filtro.trace_add("write", self._al_cambiar_filtro)
        self._actualizar_vista()

    def _crear_interfaz(self) -> None:
        contenedor = ttk.Frame(self, padding=16)
        contenedor.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            contenedor,
            text="Playlist circular",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor=tk.W)
        ttk.Label(
            contenedor,
            text="La última canción vuelve a enlazar con la primera.",
        ).pack(anchor=tk.W, pady=(0, 12))

        formulario = ttk.Frame(contenedor)
        formulario.pack(fill=tk.X, pady=(0, 10))
        formulario.columnconfigure(1, weight=1)
        formulario.columnconfigure(3, weight=1)

        ttk.Label(formulario, text="Título:").grid(row=0, column=0, padx=(0, 5))
        self._entrada_titulo = ttk.Entry(formulario, textvariable=self._titulo)
        self._entrada_titulo.grid(row=0, column=1, sticky=tk.EW, padx=(0, 12))

        ttk.Label(formulario, text="Artista:").grid(row=0, column=2, padx=(0, 5))
        ttk.Entry(formulario, textvariable=self._artista).grid(
            row=0, column=3, sticky=tk.EW, padx=(0, 12)
        )
        ttk.Button(formulario, text="Agregar", command=self._agregar).grid(
            row=0, column=4
        )

        buscador = ttk.Frame(contenedor)
        buscador.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(buscador, text="Buscar:").pack(side=tk.LEFT)
        ttk.Entry(buscador, textvariable=self._filtro).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0)
        )

        tabla_frame = ttk.Frame(contenedor)
        tabla_frame.pack(fill=tk.BOTH, expand=True)

        self._tabla = ttk.Treeview(
            tabla_frame,
            columns=("id", "titulo", "artista"),
            show="headings",
            selectmode="browse",
        )
        self._tabla.heading("id", text="ID")
        self._tabla.heading("titulo", text="Título")
        self._tabla.heading("artista", text="Artista")
        self._tabla.column("id", width=55, anchor=tk.CENTER, stretch=False)
        self._tabla.column("titulo", width=280)
        self._tabla.column("artista", width=250)

        barra = ttk.Scrollbar(
            tabla_frame, orient=tk.VERTICAL, command=self._tabla.yview
        )
        self._tabla.configure(yscrollcommand=barra.set)
        self._tabla.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        barra.pack(side=tk.RIGHT, fill=tk.Y)
        self._tabla.bind("<Double-1>", lambda _evento: self._seleccionar())

        controles = ttk.Frame(contenedor)
        controles.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(
            controles, text="▶ Seleccionar", command=self._seleccionar
        ).pack(side=tk.LEFT)
        ttk.Button(
            controles, text="⏭ Siguiente", command=self._siguiente
        ).pack(side=tk.LEFT, padx=6)
        ttk.Button(
            controles, text="Eliminar", command=self._eliminar
        ).pack(side=tk.LEFT)
        ttk.Label(controles, textvariable=self._estado).pack(side=tk.RIGHT)

        ttk.Separator(contenedor).pack(fill=tk.X, pady=10)
        ttk.Label(contenedor, text="Reproduciendo:").pack(anchor=tk.W)
        ttk.Label(
            contenedor,
            textvariable=self._reproduccion,
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor=tk.W)

        self.bind("<Return>", lambda _evento: self._agregar())
        self.bind("<Delete>", lambda _evento: self._eliminar())

    def _agregar(self) -> None:
        try:
            cancion = self._controlador.agregar_cancion(
                self._titulo.get(), self._artista.get()
            )
        except ErrorDeValidacion as error:
            messagebox.showwarning("Datos incompletos", str(error), parent=self)
            return

        self._titulo.set("")
        self._artista.set("")
        self._filtro.set("")
        self._actualizar_vista()
        self._seleccionar_fila(cancion.identificador)
        self._entrada_titulo.focus_set()

    def _seleccionar(self) -> None:
        identificador = self._obtener_id_seleccionado()
        if identificador is None:
            messagebox.showinfo(
                "Selecciona una canción",
                "Debes seleccionar una canción de la tabla.",
                parent=self,
            )
            return

        try:
            self._controlador.seleccionar_cancion(identificador)
        except ErrorDeValidacion as error:
            messagebox.showwarning("Atención", str(error), parent=self)
        self._actualizar_reproduccion()

    def _siguiente(self) -> None:
        try:
            cancion = self._controlador.reproducir_siguiente()
        except ErrorDeValidacion as error:
            messagebox.showinfo("Playlist", str(error), parent=self)
            return

        self._filtro.set("")
        self._actualizar_vista()
        self._seleccionar_fila(cancion.identificador)

    def _eliminar(self) -> None:
        identificador = self._obtener_id_seleccionado()
        if identificador is None:
            messagebox.showinfo(
                "Selecciona una canción",
                "Debes seleccionar la canción que deseas eliminar.",
                parent=self,
            )
            return

        try:
            self._controlador.eliminar_cancion(identificador)
        except ErrorDeValidacion as error:
            messagebox.showwarning("Atención", str(error), parent=self)
            return

        self._actualizar_vista()

    def _al_cambiar_filtro(self, *_args: object) -> None:
        self._actualizar_tabla()

    def _actualizar_vista(self) -> None:
        self._actualizar_tabla()
        self._actualizar_reproduccion()
        cantidad = self._controlador.cantidad()
        palabra = "canción" if cantidad == 1 else "canciones"
        self._estado.set(f"{cantidad} {palabra}")

    def _actualizar_tabla(self) -> None:
        self._tabla.delete(*self._tabla.get_children())
        canciones = self._controlador.obtener_canciones(self._filtro.get())
        for cancion in canciones:
            self._tabla.insert(
                "",
                tk.END,
                iid=str(cancion.identificador),
                values=(cancion.identificador, cancion.titulo, cancion.artista),
            )

    def _actualizar_reproduccion(self) -> None:
        actual = self._controlador.obtener_actual()
        if actual is None:
            self._reproduccion.set("Ninguna canción seleccionada")
        else:
            self._reproduccion.set(self._describir(actual))

    def _obtener_id_seleccionado(self) -> int | None:
        seleccion = self._tabla.selection()
        return int(seleccion[0]) if seleccion else None

    def _seleccionar_fila(self, identificador: int) -> None:
        fila = str(identificador)
        if self._tabla.exists(fila):
            self._tabla.selection_set(fila)
            self._tabla.focus(fila)
            self._tabla.see(fila)

    @staticmethod
    def _describir(cancion: Cancion) -> str:
        return f"{cancion.titulo} — {cancion.artista}"
