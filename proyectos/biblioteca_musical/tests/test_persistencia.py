"""Pruebas de JSON, carga atómica y archivos musicales propios."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from controllers.controlador_biblioteca import ControladorBiblioteca
from demo import crear_demo
from main import construir_controlador
from services.archivos_audio import ArchivosAudio
from services.persistencia import cargar, decodificar, guardar


class TestPersistencia(unittest.TestCase):
    """Compruebe que un archivo inválido no modifica la sesión vigente."""

    def setUp(self) -> None:
        """Prepare una sesión de ejemplo con títulos repetidos y cursores."""
        self.c = crear_demo()
        self.c.seleccionar(1, 2)

    def test_ida_y_vuelta(self) -> None:
        """Reconstruya identidades, orden, archivos, marcas y cursores."""
        self.c.solicitar(1)
        self.c.crear_playlist("Nueva")
        original = self.c.estado_vista()["estado"]
        nueva = ControladorBiblioteca()
        nueva.importar(self.c.exportar())
        self.assertEqual(nueva.estado_vista()["estado"], original)
        self.assertEqual(nueva.estado_vista()["fifo"], ())
        self.assertEqual(nueva.estado_vista()["deshacer"], ())
        self.assertEqual(nueva.mover(1, 1).identificador, 1)

    def test_json_invalido_no_mutacion(self) -> None:
        """Rechace documentos corruptos o incompatibles de forma atómica."""
        original = self.c.estado_vista()["estado"]
        for texto in ("{}", "{", "[]", "null", '{"version": 99}', "[]" * 20):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    self.c.importar(texto)
                self.assertEqual(self.c.estado_vista()["estado"], original)

    def test_validar_ids_referencias_y_tipos(self) -> None:
        """Rechace IDs duplicados, referencias rotas y contadores inválidos."""
        base = self.c.exportar()
        mutaciones = (
            lambda d: d["canciones"].append(d["canciones"][0]),
            lambda d: d["playlists"][0]["entradas"][0].update(cancion_id=999),
            lambda d: d["playlists"][0].update(actual_id=999),
            lambda d: d["playlists"][0].update(actual_id=True),
            lambda d: d.update(siguiente_cancion=1),
            lambda d: d["canciones"][0].update(duracion_segundos=True),
            lambda d: d["canciones"][0].update(archivo="../secreto.wav"),
            lambda d: d["canciones"][0].update(archivo="audio/../secreto.wav"),
            lambda d: d["playlists"][1].update(identificador=1),
            lambda d: d["playlists"][1]["entradas"][0].update(identificador=1),
            lambda d: d["playlists"][0].update(nombre=" "),
            lambda d: d.update(version=True),
            lambda d: d.update(siguiente_entrada="4"),
        )
        for indice, mutar in enumerate(mutaciones):
            with self.subTest(indice=indice):
                datos = json.loads(base)
                mutar(datos)
                with self.assertRaises(ValueError):
                    decodificar(json.dumps(datos))

    def test_guardado_atomico(self) -> None:
        """Un fallo de reemplazo no trunque el guardado anterior."""
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "biblioteca.json"
            estado = self.c.estado_vista()["estado"]
            guardar(ruta, estado)
            self.assertEqual(cargar(ruta), estado)
            anterior = ruta.read_bytes()
            with patch(
                "services.persistencia.os.replace", side_effect=OSError
            ):
                with self.assertRaises(OSError):
                    guardar(ruta, estado)
            self.assertEqual(ruta.read_bytes(), anterior)
            self.assertEqual(tuple(Path(directorio).glob("*.tmp")), ())

    def test_arranque_corrupto_conserva_archivo(self) -> None:
        """Inicie vacío y avise sin reemplazar un guardado corrupto."""
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "biblioteca.json"
            ruta.write_text("corrupto", encoding="utf-8")
            controlador, aviso = construir_controlador(ruta)
            self.assertEqual(controlador.listar(), ())
            self.assertIn("No se cargó", aviso)
            self.assertEqual(ruta.read_text(), "corrupto")

    def test_limite_y_utf8(self) -> None:
        """Rechace JSON demasiado grande o codificación ilegible."""
        with self.assertRaises(ValueError):
            decodificar(" " * (5 * 1024 * 1024 + 1))
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "biblioteca.json"
            ruta.write_bytes(b"\xff\xff")
            with self.assertRaises(ValueError):
                cargar(ruta)


class TestArchivos(unittest.TestCase):
    """Compruebe copias propias y rechazo de rutas fuera de assets."""

    def test_importar_y_conservar_original(self) -> None:
        """Copie bytes y ruta con nombres distintos sin tocar el original."""
        with tempfile.TemporaryDirectory() as directorio:
            base = Path(directorio)
            original = base / "original.wav"
            original.write_bytes(b"onda de prueba")
            archivos = ArchivosAudio(base / "assets")
            a = archivos.importar("prueba.wav", origen=str(original))
            b = archivos.importar("prueba.wav", contenido=b"otros datos")
            self.assertNotEqual(a, b)
            self.assertEqual(original.read_bytes(), b"onda de prueba")
            self.assertEqual(archivos.comprobar(a), a)
            for ruta in ("", "../original.wav", "audio/ausente.wav"):
                with self.assertRaises(ValueError):
                    archivos.comprobar(ruta)
            for nombre, datos in (("mal.exe", b"x"), ("vacio.wav", b"")):
                with self.assertRaises(ValueError):
                    archivos.importar(nombre, contenido=datos)
