"""Reglas del catálogo musical sobre una lista doble propia."""

from models.cancion import Cancion
from models.estructuras.lista_doble import ListaDoblementeEnlazada


class Biblioteca:
    """Administre canciones con ID único durante la sesión."""

    def __init__(self) -> None:
        """Cree el catálogo vacío y comience la numeración en uno."""
        self._canciones: ListaDoblementeEnlazada[Cancion] = (
            ListaDoblementeEnlazada()
        )
        self._siguiente_id = 1

    def agregar(
        self,
        titulo: str,
        artista: str,
        duracion_segundos: int,
        archivo: str = "",
        **metadatos,
    ) -> Cancion:
        """Agregue una canción validada y devuélvala; enlaces O(1).

        Limpia espacios exteriores. ValueError indica datos inválidos;
        en ese caso el catálogo y el contador no cambian.
        """
        if not isinstance(titulo, str) or not isinstance(artista, str):
            raise ValueError("Título y artista deben ser textos.")
        cancion = Cancion(
            self._siguiente_id,
            titulo.strip(),
            artista.strip(),
            duracion_segundos,
            archivo,
            **metadatos,
        )
        self._canciones.agregar_final(cancion)
        self._siguiente_id += 1
        return cancion

    def listar(self, filtro: str = "") -> tuple[Cancion, ...]:
        """Devuelva una instantánea filtrada por título o artista; O(n).

        casefold permite coincidencias sin distinguir mayúsculas.
        Un filtro vacío devuelve todo. La tupla sirve de salida para
        la vista; no almacena los nodos ni sustituye la lista doble.
        """
        consulta = filtro.strip().casefold()
        return tuple(
            cancion
            for cancion in self._canciones
            if consulta in cancion.titulo.casefold()
            or consulta in cancion.artista.casefold()
        )

    def eliminar(self, identificador: int) -> Cancion:
        """Elimine por ID y devuelva la canción; búsqueda O(n).

        ValueError indica un ID ausente. Los IDs no se reutilizan.
        """
        cancion = self._canciones.eliminar(
            lambda dato: dato.identificador == identificador
        )
        if cancion is None:
            raise ValueError("No existe una canción con ese identificador.")
        return cancion

    def cantidad(self) -> int:
        """Devuelva la cantidad de canciones en O(1)."""
        return len(self._canciones)

    def memoria_nodos(self) -> int:
        """Consulte memoria aproximada del catálogo sin exponer nodos."""
        return self._canciones.memoria_nodos()

    def obtener(self, identificador: int) -> Cancion:
        """Busque por ID; O(n), ValueError si no existe."""
        cancion = self._canciones.buscar(
            lambda dato: dato.identificador == identificador
        )
        if cancion is None:
            raise ValueError("La canción ya no existe.")
        return cancion

    def restaurar(
        self, canciones: tuple[Cancion, ...], siguiente_id: int
    ) -> None:
        """Reconstruya nodos desde datos validados en O(n).

        Se usa para carga e historial. El llamador valida unicidad e ID.
        """
        nueva: ListaDoblementeEnlazada[Cancion] = ListaDoblementeEnlazada()
        for cancion in canciones:
            nueva.agregar_final(cancion)
        self._canciones = nueva
        self._siguiente_id = siguiente_id

    @property
    def siguiente_id(self) -> int:
        """Consulte la marca de IDs sin exponer nodos; O(1)."""
        return self._siguiente_id
