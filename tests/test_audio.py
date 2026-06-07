import sounddevice as sd
import numpy as np
import time

def callback(indata, frames, time_info, status):
    if status:
        print(f"Status: {status}")
    rms = np.sqrt(np.mean(indata.astype(np.float64)**2))
    # Solo mostrar si hay algo de sonido
    if rms > 10:
        print(f"RMS: {rms:.1f}")

stream = sd.InputStream(samplerate=16000, blocksize=1024, channels=1, dtype='int16', callback=callback)
stream.start()
print("Escuchando durante 10 segundos...")
time.sleep(10)
stream.stop()
stream.close()
print("Prueba completada sin errores.")