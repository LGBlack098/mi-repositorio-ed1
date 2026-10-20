"""Genere audio sintético propio para probar sin descargar canciones."""

import math
import struct
import wave
from pathlib import Path


def generar(destino: Path) -> None:
    """Escriba seis segundos de notas suaves en PCM WAV mono a 16 kHz.

    Las muestras usan amplitud baja y envolvente para evitar clics.
    El archivo es una señal de prueba original, no música de terceros.
    """
    destino.parent.mkdir(parents=True, exist_ok=True)
    frecuencia = 16000
    with wave.open(str(destino), "wb") as archivo:
        archivo.setnchannels(1)
        archivo.setsampwidth(2)
        archivo.setframerate(frecuencia)
        for nota in (261.63, 329.63, 392.0, 523.25, 392.0, 329.63):
            muestras = bytearray()
            for i in range(frecuencia):
                t = i / frecuencia
                envolvente = min(t * 20, (1 - t) * 20, 1)
                valor = int(
                    4000 * envolvente * math.sin(2 * math.pi * nota * t)
                )
                muestras.extend(struct.pack("<h", valor))
            archivo.writeframes(muestras)


if __name__ == "__main__":
    generar(Path(__file__).parent / "assets/audio/demo.wav")
