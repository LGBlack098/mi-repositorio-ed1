"""Mediciones reales de acciones MVC; sin audio, disco ni pantalla."""

from collections import deque
from dataclasses import dataclass
from functools import wraps
from time import perf_counter


@dataclass(frozen=True)
class Muestra:
    """Conserve latencia real y etiqueta de una acción del controlador."""

    accion: str
    instante: float
    segundos: float
    exito: bool


class Metricas:
    """Retenga las últimas 200 acciones; ventana de frecuencia de 10 s.

    deque almacena exclusivamente telemetría auxiliar. Las estructuras
    musicales continúan implementadas mediante sus nodos propios.
    """

    def __init__(self, reloj=perf_counter):
        """Reciba reloj monotónico inyectable para pruebas reproducibles."""
        self.reloj = reloj
        self.inicio = reloj()
        self.muestras = deque(maxlen=200)

    def resumen(self) -> dict:
        """Calcule acciones/s observadas y latencia de la última acción."""
        ahora = self.reloj()
        recientes = tuple(m for m in self.muestras if ahora - m.instante < 10)
        ventana = min(10, max(ahora - self.inicio, 0.001))
        ultima = self.muestras[-1] if self.muestras else None
        return {
            "acciones_s": len(recientes) / ventana,
            "ventana_s": ventana,
            "muestras": len(recientes),
            "ultima": ultima,
        }


def medir(metodo):
    """Mida una acción del controlador incluso si termina con error."""

    @wraps(metodo)
    def ejecutar(self, *args, **kwargs):
        """Cronometre el contrato del controlador sin incluir la vista."""
        inicio = self.metricas.reloj()
        exito = False
        try:
            resultado = metodo(self, *args, **kwargs)
            exito = True
            return resultado
        finally:
            final = self.metricas.reloj()
            self.metricas.muestras.append(
                Muestra(metodo.__name__, final, final - inicio, exito)
            )

    return ejecutar
