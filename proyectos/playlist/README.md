# Sonoteca

Reproductor de música local en Python y Flet, con biblioteca, playlists,
cola de reproducción y una interfaz adaptable a escritorio y teléfono.

El título de la ventana es **Sonoteca**. La ventana, el ejecutable Windows
y la cabecera comparten el icono rosa y azul del cliente Flet original.

## Funcionalidades

- Importar varios archivos WAV, MP3, OGG, FLAC o M4A.
- Leer título, artista y duración desde el archivo.
- Consultar una ficha con ID, nombre original, formato, peso y duración.
- Mostrar la portada incrustada JPEG/PNG; usar arte local cuando falta.
- Buscar canciones y crear playlists con apariciones independientes.
- Reproducir, pausar, cambiar de pista, buscar posición y ajustar volumen.
- Iniciar con volumen al 100 % y acceder a la ficha desde la canción del dock.
- Repetición opcional y avance automático al terminar la pista real.
- Añadir solicitudes normales, reproducir después y alternar playlists.
- Guardar cambios automáticamente y restaurar respaldos.
- Ver por separado las solicitudes inmediatas y las canciones en cola,
  con acceso directo desde la barra de reproducción.

No requiere cuentas ni descarga música. Los archivos se copian a un
almacenamiento propio sin modificar sus originales.

## Iniciar

Requiere Python 3.10 o superior. Verificado con Python 3.12 en Windows.
Desde esta carpeta:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe main.py
```

El primer inicio queda vacío. Los siguientes inicios recuperan la biblioteca
local guardada. `--datos ruta.json` permite elegir otro guardado y
`--port 8551` cambia el puerto. `--movil` revisa una disposición estrecha
en Windows; no emula Android.

## Uso

1. Pulsa **Añadir música**, selecciona archivos y elige una canción.
2. Controla reproducción y posición desde la barra inferior.
3. Crea una playlist y añade canciones desde el menú **…** de cada pista.
4. En ese menú, **Información del archivo** muestra la ficha y portada.
5. **Añadir a la cola** conserva llegada; **Reproducir después** se
   atiende antes de las solicitudes normales.
6. En **Cola → Alternar playlists**, añade listas no vacías e inicia turnos.
7. El botón **Cola** de la barra abre los próximos temas. En escritorio
   amplio alterna el panel derecho; en teléfono abre la página de cola.
8. **Opciones de música** reúne volumen, repetición, historial y respaldos.
   También puedes deshacer con `Ctrl+Z` y rehacer con `Ctrl+Y`.

En teléfono hay navegación inferior: Mi música, Playlists y Cola. Búsqueda,
repetición y volumen siguen disponibles en la disposición compacta.

## Arquitectura

| Carpeta | Responsabilidad |
| --- | --- |
| `models/` | Entidades, reglas musicales, navegación y estructuras propias. |
| `models/estructuras/` | Nodos y operaciones de listas, pilas y colas. |
| `controllers/` | Entradas, coordinación del modelo y medición de acciones. |
| `services/` | Metadatos, archivos, audio, persistencia y experimento aislado. |
| `views/` | Interfaz Flet, fichas, diagramas y animación. |

El modelo y el controlador no importan Flet. La vista solicita la política
musical al controlador, sin modificar enlaces privados.

## Estructuras de datos

| Estructura manual | Uso | Costo de primitivas |
| --- | --- | --- |
| Lista doble | Catálogo y colección de playlists. | Añadir al final O(1); buscar por ID O(n). |
| Lista doble circular | Apariciones y cursor de cada playlist. | Mover cursor O(1); localizar aparición O(e). |
| Pila LIFO / dos pilas | Deshacer y rehacer ediciones. | Apilar/desapilar O(1); restaurar estado tiene costo adicional. |
| Cola FIFO | Solicitudes normales. | Encolar/desencolar O(1). |
| Cola de prioridad estable | Solicitudes destacadas. | Insertar O(q); retirar O(1). |
| Cola circular acotada | Turnos entre playlists. | Encolar/desencolar O(1); validar duplicados requiere recorrido. |

Los nodos contienen los datos y sus enlaces. Tuplas y colecciones auxiliares
se usan para instantáneas, validación, controles, JSON y telemetría; no
sustituyen las estructuras musicales.

Mover un cursor es O(1), pero resolver playlist y canción requiere búsquedas.
La acción completa no se anuncia como O(1). La navegación del catálogo
recorre una instantánea temporal en O(n).

## Datos y archivos

- El guardado contiene catálogo, playlists, cursores e identidades; los
  audios e imágenes permanecen en `assets/audio/` y `assets/portadas/`.
- Para trasladar una biblioteca se necesitan el JSON y sus assets.
- Los metadatos nuevos son opcionales: se leen guardados anteriores. Las
  fichas antiguas se completan al abrirlas si el archivo sigue disponible.
- El historial conserva hasta 50 ediciones. Las solicitudes de sesión no
  se guardan ni se recuperan al deshacer una baja.
- El guardado es atómico y detecta cambios de otro proceso antes de
  sobrescribir. No sustituye una base de datos multiusuario.
- Una baja no elimina el archivo físico, para permitir recuperación.

Límites: JSON de hasta 5 MiB, audio de hasta 50 MiB por archivo y portadas
JPEG/PNG incrustadas de hasta 3 MiB. La compatibilidad de códecs depende del
cliente. Los errores se comunican sin borrar la biblioteca.

## Leer y explicar el código

- `main.py`: inicia la aplicación y recupera el guardado.
- `views/vista_sonoteca.py`: presenta las canciones y recibe las acciones.
- `views/vista_reproductor.py`: biblioteca, playlists y controles de audio.
- `views/vista_biblioteca.py`: diálogos y acciones compartidas de guardado.
- `controllers/controlador_biblioteca.py`: coordina las operaciones.
- `models/cancion.py`: representa título, artista, duración e identidad.
- `models/biblioteca.py`: agrega, busca y elimina canciones.
- `models/estructuras/`: implementa los nodos, listas, pilas y colas.
- `services/`: importación de archivos, metadatos, persistencia y audio.

Al importar una canción, la vista recibe el archivo; los servicios lo
copian y leen sus metadatos; el controlador solicita añadirlo al modelo;
la lista enlaza un nodo nuevo y la vista muestra el estado actualizado.

Las funciones incluyen docstrings con propósito, entradas, resultados o
errores relevantes. Se siguen PEP 8 para estilo y PEP 257 para documentación.
Ruff comprueba el formato y las reglas configuradas; D401 se revisa
manualmente porque analiza gramática inglesa y el código se documenta
en español.

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

La aplicación no incluye demos, generadores de documentación ni módulos
de visualización educativa. Las pruebas de desarrollo se conservan aparte
de esta carpeta; la verificación pública revisa sintaxis, importaciones,
estilo y formato. Esas comprobaciones no sustituyen una prueba de audio
en cada dispositivo.

## Web y distribución

Servidor web local:

```powershell
.\iniciar_web.ps1
# Abrir http://127.0.0.1:8000
```

`Dockerfile` prepara un servidor dinámico Python con volumen `/data`.
`SONOTECA_DATA_DIR` configura almacenamiento persistente. Un servidor público
necesita su propia configuración de acceso y HTTPS; la app está concebida
para una biblioteca personal local.

Windows:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\empaquetar.ps1
```

La salida es `dist/Sonoteca/Sonoteca.exe`. Debe conservarse toda la carpeta,
incluido `_internal`. Los datos quedan en `SonotecaDatos/` junto al ejecutable.
El script respalda los datos existentes antes de reconstruir.

Android:

```powershell
.\construir_movil.ps1
```

El script prepara fuentes sin datos personales y solicita un APK arm64 a
Flet. La compilación requiere las herramientas Android/Flutter y acceso a
sus dependencias. Generar el APK no acredita funcionamiento en un teléfono
físico. iOS requiere un entorno de compilación y verificación propio.

## Dependencias y referencias

- [Flet](https://flet.dev/), [Flet Audio](https://flet.dev/docs/services/audio/).
- [Mutagen](https://mutagen.readthedocs.io/).
- [PEP 8](https://peps.python.org/pep-0008/),
  [PEP 257](https://peps.python.org/pep-0257/).
- [Documentación de Python](https://docs.python.org/3/).
