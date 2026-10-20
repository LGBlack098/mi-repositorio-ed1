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

El primer inicio queda vacío. Para probar títulos ficticios y una señal
sintética propia de seis segundos, usa `--demo` con un archivo de datos nuevo:

```powershell
.\.venv\Scripts\python.exe main.py --demo --datos data/demo.json
```

Si existe un guardado válido, se recupera antes de crear datos de ejemplo.
`--datos ruta.json` selecciona otro guardado; `--port 8551` cambia el puerto.
`--movil` permite revisar la disposición estrecha en Windows. Esa ventana
no emula Android ni sus permisos.

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
| `tests/` | Casos de dominio, enlaces, audio, datos y disposición. |

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

## Instrumentación interna

La instrumentación mide acciones del controlador con un reloj monotónico:
latencia, éxito/error y acciones/s observadas en una ventana de diez segundos.
El audio, el render y el guardado posterior quedan fuera de esa medición.

La memoria se estima con el tamaño superficial de cada nodo y su diccionario
de atributos. No incluye sus datos, buffers ni archivos; no representa RAM
total. Un experimento aislado compara inserción final y búsqueda ausente
con 100, 1000 y 5000 nodos. Los tiempos son locales y no prueban por sí solos
la complejidad asintótica.

La interfaz principal muestra únicamente funciones musicales. Los módulos
de diagramas, recorrido circular y comparación permanecen disponibles en
el código y sus pruebas; no hay un panel académico en la aplicación.

## Pruebas y estilo

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
```

La suite contiene 72 pruebas: enlaces, cursor, vacíos, prioridades, historial,
JSON, importación, metadatos, portadas, mediciones y disposición móvil.
El servicio de audio se simula en pruebas unitarias. No se afirma cobertura
del 100% ni compatibilidad con todos los dispositivos.

Las regresiones de interfaz comprueban la selección de una aparición entre
canciones repetidas, el refresco sin construir dos veces la vista, la cola
compacta, los atajos y el volumen inicial completo.

Se siguen PEP 8, anotaciones de tipo y docstrings según PEP 257. D401 se
revisa manualmente porque su análisis gramatical inglés no se adapta a las
docstrings en español.

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
- [unittest](https://docs.python.org/3/library/unittest.html),
  [perf_counter](https://docs.python.org/3/library/time.html#time.perf_counter).
