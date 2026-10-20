"""Adaptador asíncrono de flet-audio; el modelo no conoce el dispositivo."""

import asyncio
import logging
from collections.abc import Callable

import flet_audio as fa

from services.archivos_audio import ArchivosAudio
from services.rutas_multimedia import fuente_multimedia


class Reproductor:
    """Controle fuente, pausa, posición y volumen con errores visibles."""

    def __init__(
        self,
        archivos: ArchivosAudio,
        notificar: Callable[[str], None],
        terminado: Callable,
    ) -> None:
        """Cree servicio sin autoplay y conserve callbacks de la vista."""
        self.archivos = archivos
        self.notificar = notificar
        self.terminado = terminado
        self._listo = asyncio.Event()
        self.audio = fa.Audio(
            src="audio/demo.wav",
            volume=1.0,
            release_mode=fa.ReleaseMode.STOP,
            on_state_change=self._estado,
            on_position_change=self._posicion,
            on_loaded=self._cargado,
            on_duration_change=self._duracion,
        )
        self.actual_id: int | None = None
        self.archivo_actual = ""
        self.pausado = False
        self.posicion = 0
        self.duracion = 0
        self._candado = asyncio.Lock()
        self._activo = False

    async def reproducir(self, identificador: int, archivo: str) -> None:
        """Compruebe archivo y reproduzca desde cero; límite de 12 s.

        No bloquea el bucle de interfaz. Errores del códec o del servicio
        se propagan para que la vista los muestre y detenga el avance.
        """
        relativa = self.archivos.comprobar(archivo)
        fuente = fuente_multimedia(self.archivos.assets, relativa)
        logging.info("Preparando audio: %s", fuente)
        async with self._candado:
            self._activo = False
            if self.actual_id is not None:
                await asyncio.wait_for(self.audio.pause(), 12)
            if self.audio.src != fuente:
                self._listo.clear()
                self.duracion = 0
            self.audio.src = fuente
            # Enviar fuente antes de play: auto-update llega al finalizar
            # el manejador, demasiado tarde para cargar esta pista.
            self.audio.update()
            self.actual_id = identificador
            self.archivo_actual = relativa
            self.posicion = 0
            self.pausado = False
            try:
                await asyncio.wait_for(self._listo.wait(), 12)
                await asyncio.wait_for(self.audio.play(), 12)
            except Exception:
                self.actual_id = None
                raise
            self._activo = True
            logging.info("Comando play confirmado")
            self.notificar("Reproduciendo")

    async def pausar_reanudar(self) -> None:
        """Alterne pausa y reproducción; ValueError si no hay audio."""
        if self.actual_id is None:
            raise ValueError("Selecciona una canción con audio.")
        if self.pausado:
            await asyncio.wait_for(self.audio.resume(), 12)
        else:
            await asyncio.wait_for(self.audio.pause(), 12)
        self.pausado = not self.pausado
        self.notificar("En pausa" if self.pausado else "Reproduciendo")

    async def detener(self) -> None:
        """Pause, vuelva a cero y borre selección sin generar avance."""
        self._activo = False
        if self.actual_id is not None:
            await asyncio.wait_for(self.audio.pause(), 12)
            await asyncio.wait_for(self.audio.seek(0), 12)
        self.actual_id = None
        self.pausado = False
        self.posicion = 0
        self.notificar("Detenido")

    def volumen(self, valor: float) -> None:
        """Fije amplitud entre 0 y 1; ValueError fuera del rango."""
        if not 0 <= valor <= 1:
            raise ValueError("El volumen debe estar entre 0 y 1.")
        self.audio.volume = valor
        self.audio.update()

    async def buscar_posicion(self, segundos: float) -> None:
        """Salte a segundos dentro de la pista; ValueError sin selección."""
        if self.actual_id is None:
            raise ValueError("Primero reproduce una canción.")
        if not 0 <= segundos <= self.duracion:
            raise ValueError("La posición está fuera de la pista.")
        await asyncio.wait_for(self.audio.seek(round(segundos * 1000)), 12)
        self.posicion = int(segundos)
        self.notificar("En pausa" if self.pausado else "Reproduciendo")

    def _duracion(self, evento) -> None:
        """Capture duración del dispositivo para progreso y búsqueda."""
        valor = evento.duration
        self.duracion = (
            valor.in_seconds
            if hasattr(valor, "in_seconds")
            else int(valor) // 1000
        )

    async def _estado(self, evento) -> None:
        """Avise fin real de pista una sola vez, ignorando release."""
        logging.info("Estado del cliente: %s", evento.state)
        if evento.state == fa.AudioState.COMPLETED and self._activo:
            self._activo = False
            self.actual_id = None
            self.pausado = False
            self.notificar("Pista finalizada")
            await self.terminado()

    def _posicion(self, evento) -> None:
        """Actualice segundos transcurridos desde el evento del motor."""
        posicion = evento.position
        self.posicion = (
            posicion.in_seconds
            if hasattr(posicion, "in_seconds")
            else int(posicion) // 1000
        )
        if self.actual_id is not None and self._activo:
            self.notificar("En pausa" if self.pausado else "Reproduciendo")

    def _cargado(self, _evento) -> None:
        """Habilite play solo después de que el cliente cargue la fuente."""
        logging.info("Audio cargado en cliente")
        self._listo.set()
