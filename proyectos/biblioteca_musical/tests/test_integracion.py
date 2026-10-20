"""Verifique fichas, mediciones, navegación móvil y recorrido circular."""

import json
import tempfile
import unittest
from base64 import b64decode
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from mutagen.id3 import APIC
from mutagen.wave import WAVE

from controllers.controlador_biblioteca import ControladorBiblioteca
from demo import crear_demo
from generar_demo import generar
from models.cancion import Cancion
from models.estructuras.lineales import Cola, ColaCircular, Pila
from models.estructuras.lista_circular import ListaCircular
from models.estructuras.lista_doble import ListaDoblementeEnlazada
from models.metricas import Metricas, Muestra
from services.experimento import comparar
from services.ficha_audio import leer_ficha
from views.recorrido_circular import RecorridoCircular
from views.vista_sonoteca import VistaSonoteca


class TestMediciones(unittest.TestCase):
    """Compruebe medidas sin umbrales de rendimiento dependientes del PC."""

    def test_ventana_con_reloj_controlado(self):
        """Expire muestras tras diez segundos y excluya tiempo de UI."""
        instante = [0.0]
        metricas = Metricas(lambda: instante[0])
        metricas.muestras.append(Muestra("agregar", 1, 0.002, True))
        instante[0] = 2
        self.assertEqual(metricas.resumen()["acciones_s"], 0.5)
        instante[0] = 12
        self.assertEqual(metricas.resumen()["acciones_s"], 0)
        self.assertEqual(metricas.resumen()["ultima"].segundos, 0.002)

    def test_mide_exitos_y_fallos_sin_perder_excepcion(self):
        """Registre ambas salidas y conserve las reglas de validación."""
        c = ControladorBiblioteca()
        c.agregar("Tema", "Artista", "60")
        with self.assertRaises(ValueError):
            c.agregar("Tema", "Artista", "no entero")
        self.assertEqual(len(c.metricas.muestras), 2)
        self.assertTrue(c.metricas.muestras[0].exito)
        self.assertFalse(c.metricas.muestras[1].exito)

    def test_memoria_circular_acotada_y_vacio(self):
        """Estime nodos una vez y termine incluso con enlaces circulares."""
        for estructura, insertar in (
            (ListaDoblementeEnlazada(), "agregar_final"),
            (ListaCircular(), "agregar"),
            (Cola(), "encolar"),
            (ColaCircular(), "encolar"),
            (Pila(), "apilar"),
        ):
            self.assertEqual(estructura.memoria_nodos(), 0)
            getattr(estructura, insertar)(1)
            uno = estructura.memoria_nodos()
            getattr(estructura, insertar)(2)
            self.assertGreater(estructura.memoria_nodos(), uno)
            self.assertEqual(
                tuple(estructura), (2, 1) if insertar == "apilar" else (1, 2)
            )

    def test_experimento_real_aislado(self):
        """Entregue tiempos positivos para tres tamaños sin editar música."""
        resultados = comparar()
        self.assertEqual(tuple(r[0] for r in resultados), (100, 1000, 5000))
        self.assertTrue(all(a > 0 and b > 0 for _, a, b in resultados))


class TestFicha(unittest.TestCase):
    """Verifique compatibilidad del guardado y carátulas de archivos."""

    def test_ficha_con_portada_real_incrustada(self):
        """Extraiga PNG ID3 y conserve intacto el original tras leer."""
        with tempfile.TemporaryDirectory() as temporal:
            ruta = Path(temporal) / "assets/audio/prueba.wav"
            generar(ruta)
            imagen = b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwC"
                "AAAAC0lEQVR42mP8/x8AAwMCAO+aGYQAAAAASUVORK5CYII="
            )
            audio = WAVE(ruta)
            audio.add_tags()
            audio.tags.add(APIC(mime="image/png", type=3, data=imagen))
            audio.save()
            original = ruta.read_bytes()
            ficha = leer_ficha(ruta, "Mi tema.wav")
            self.assertEqual(ficha["tamano_bytes"], len(original))
            self.assertEqual(ficha["formato"], "WAVE")
            self.assertEqual(ficha["nombre_archivo"], "Mi tema.wav")
            self.assertEqual(
                (ruta.parent.parent / ficha["portada"]).read_bytes(), imagen
            )
            self.assertEqual(ruta.read_bytes(), original)

    def test_metadatos_y_compatibilidad_json_antiguo(self):
        """Lea canciones antiguas sin nuevos campos y conserve las nuevas."""
        c = crear_demo()
        antiguo = json.loads(c.exportar())
        for cancion in antiguo["canciones"]:
            for campo in (
                "nombre_archivo",
                "tamano_bytes",
                "formato",
                "portada",
            ):
                cancion.pop(campo)
        c.importar(json.dumps(antiguo))
        self.assertEqual(c.listar()[0].tamano_bytes, 0)
        c.asociar_audio(
            1,
            "audio/demo.wav",
            tamano_bytes=200,
            formato="WAVE",
            nombre_archivo="Prueba.wav",
        )
        otra = ControladorBiblioteca()
        otra.importar(c.exportar())
        self.assertEqual(otra.listar()[0].tamano_bytes, 200)
        c.historial()
        self.assertEqual(c.listar()[0].tamano_bytes, 0)

    def test_rechaza_rutas_de_portada_y_tamanos_invalidos(self):
        """Impida escapar del directorio servido mediante metadatos JSON."""
        for datos in (
            {"portada": "../secreto.png"},
            {"tamano_bytes": True},
            {"tamano_bytes": -1},
        ):
            with self.assertRaises(ValueError):
                Cancion(1, "T", "A", 1, **datos)

    def test_cambiar_audio_limpia_ficha_anterior(self):
        """No atribuya peso o carátula del archivo previo al reemplazo."""
        c = crear_demo()
        c.asociar_audio(1, "audio/demo.wav", tamano_bytes=200)
        c.asociar_audio(1, "audio/nuevo.mp3")
        self.assertEqual(c.listar()[0].tamano_bytes, 0)


class TestPantallas(unittest.TestCase):
    """Construya controles reales sin dispositivo de audio ni ventana."""

    def montar(self, ancho):
        """Componga la página con el ancho pedido y recoja sus controles."""
        vista = VistaSonoteca(crear_demo())
        pagina = SimpleNamespace(width=ancho, update=Mock(), add=Mock())
        vista.montar(pagina)
        return vista, pagina

    def test_navegacion_inferior_y_busqueda_en_telefono(self):
        """Conserve búsqueda, tres destinos y objetivos táctiles."""
        vista, pagina = self.montar(390)
        self.assertIsNotNone(pagina.navigation_bar)
        self.assertEqual(len(pagina.navigation_bar.destinations), 3)
        self.assertTrue(vista._filtro.visible)
        self.assertFalse(vista._lateral.visible)
        self.assertFalse(vista._tabs.visible)
        self.assertEqual(vista._play.width, 48)
        vista._cambiar_destino(
            SimpleNamespace(control=SimpleNamespace(selected_index=2))
        )
        self.assertEqual(vista.seccion, "Siguientes")

    def test_escritorio_y_panel_tecnico_secundario(self):
        """Monte el reproductor y luego sus medidas y diagrama separado."""
        vista, pagina = self.montar(1366)
        self.assertIsNone(pagina.navigation_bar)
        self.assertTrue(vista._lateral.visible)
        self.assertEqual(vista.seccion, "Biblioteca")
        pagina.update.reset_mock()
        vista.seccion = "Tecnica"
        vista.actualizar()
        pagina.update.assert_called_once()
        self.assertIn("acciones/s", vista._medida.value)
        self.assertTrue(vista._memoria.controls)

    def test_anillo_reutiliza_marcador_y_cierra_cursor(self):
        """Siga el estado real, sin duplicar nodos ni cambiar canciones."""
        c = crear_demo()
        anillo = RecorridoCircular()
        foto = c.estado_vista()["estado"].playlists[0]
        anillo.actualizar(foto)
        marcador = anillo.marcador
        for _ in range(len(foto.entradas)):
            c.mover(1, 1)
            anillo.actualizar(c.estado_vista()["estado"].playlists[0])
        self.assertIs(anillo.marcador, marcador)
        self.assertEqual(anillo.indice, 0)
