# Playlist circular con lista enlazada y MVC

Aplicación breve de escritorio desarrollada en Python. Administra canciones
mediante una **lista enlazada circular simple** implementada desde cero y
separa sus responsabilidades con el patrón **Modelo-Vista-Controlador (MVC)**.

## ¿Por qué una lista circular?

En una playlist, después de la última canción se puede volver a la primera. En
esta implementación, el enlace `siguiente` del nodo final apunta a la cabeza:

```text
 cabeza                         cola
    ↓                             ↓
[Canción 1] → [Canción 2] → [Canción 3]
    ↑_____________________________|
```

La lista conserva referencias a `cabeza`, `cola` y `actual`. Cada canción
recibe un identificador único, por lo que dos canciones con el mismo título y
artista pueden seleccionarse y eliminarse correctamente.

## Funcionalidades

- Agregar canciones al final.
- Seleccionar una canción de la tabla.
- Avanzar circularmente a la canción siguiente.
- Eliminar una canción por su ID.
- Buscar por título o artista sin distinguir mayúsculas.
- Mostrar el número de canciones y la reproducción actual.

## Arquitectura

```text
playlist_circular_mvc/
├── controllers/
│   └── controlador_playlist.py
├── models/
│   ├── cancion.py
│   └── lista_circular.py
├── views/
│   └── vista_playlist.py
├── tests/
│   └── test_lista_circular.py
├── main.py
└── README.md
```

- **Modelo:** contiene la canción, los nodos y la lista circular.
- **Vista:** presenta la interfaz Tkinter y no modifica nodos directamente.
- **Controlador:** valida entradas y traduce acciones de la vista al modelo.

## Complejidad

| Operación | Complejidad | Justificación |
|---|---:|---|
| Agregar al final | O(1) | Se conserva una referencia a la cola. |
| Obtener actual | O(1) | Se conserva una referencia al nodo actual. |
| Avanzar | O(1) | Solo se sigue el enlace `siguiente`. |
| Buscar | O(n) | Puede ser necesario recorrer todos los nodos. |
| Seleccionar por ID | O(n) | El ID se localiza mediante recorrido. |
| Eliminar por ID | O(n) | Se busca el nodo y su anterior. |
| Listar | O(n) | Se visita cada nodo exactamente una vez. |

Los recorridos usan el tamaño de la lista como límite. Esto evita un ciclo
infinito, ya que en una lista circular nunca se encuentra un enlace `None`.

## Ejecución

Se requiere Python 3.10 o superior. Tkinter forma parte de la instalación
estándar de Python.

```bash
cd proyectos/playlist_circular_mvc
python main.py
```

## Pruebas

Desde la misma carpeta:

```bash
python -m unittest discover -s tests -v
```

Las pruebas cubren lista vacía, inserción, recorrido circular, búsqueda,
eliminación de la cabeza o del único elemento, títulos repetidos y validación
de entradas.

## Casos borde contemplados

- Playlist vacía.
- Campos de texto vacíos o compuestos solo por espacios.
- Canciones repetidas.
- Eliminación de la canción actual.
- Eliminación del único nodo.
- Regreso de la última canción a la primera.

## Guion breve para la exposición

1. **Problema:** una playlist debe continuar desde la última canción hacia la
   primera sin detenerse.
2. **Estructura elegida:** lista enlazada circular simple; cada nodo contiene
   una canción y una referencia al siguiente nodo.
3. **Eficiencia:** agregar al final y avanzar cuestan O(1) gracias a las
   referencias `cola` y `actual`; buscar y eliminar cuestan O(n).
4. **MVC:** el modelo implementa la estructura, el controlador valida las
   acciones y la vista solo presenta los datos con Tkinter.
5. **Demostración:** agregar dos canciones con el mismo título, seleccionar una
   por su ID, avanzar hasta volver al inicio y eliminar solo la seleccionada.
