"""
Enhanced Voice Assistant V.2.0 - Voice Recognition using sounddevice
Replaces pyaudio with sounddevice for better Python 3.14 compatibility
"""

import json
import logging
import math
import os
import sys
import queue
import threading
import time
import wave
from datetime import datetime

import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal

from vosk import KaldiRecognizer, Model

SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
SILENCE_FRAMES_TO_CUT = 10
MIN_SPEECH_BYTES = 6400
RMS_SPEECH_BASE = 30
RMS_SPEECH_RANGE = 170

from core.audio_lock import audio_lock

logger = logging.getLogger("EVA")


class SimpleVAD:
    """VAD basado en energia RMS - sin dependencias externas"""

    _diag_counter = 0

    def __init__(self, mode=2):
        """
        mode: 0=Muy Conservador, 1=Conservador, 2=Equilibrado, 3=Sensible
        """
        self.mode = mode
        # Umbrales RMS ajustados para cada modo (0-32767 para int16)
        # Reducidos para capturar voz normal con microfonos tipicos
        self._thresholds = {
            0: 500,
            1: 150,
            2: 80,
            3: 40
        }
        self._silence_counter = 0
        self._speech_counter = 0
        self._required_speech_frames = 2

    def is_speech(self, audio_bytes, sample_rate=16000):
        """
        Determina si el buffer de audio contiene voz basandose en energia RMS.
        """
        try:
            samples = np.frombuffer(audio_bytes, dtype=np.int16)

            if len(samples) == 0:
                return False

            # Calcular energia RMS
            rms = np.sqrt(np.mean(samples.astype(np.float64) ** 2))

            threshold = self._thresholds.get(self.mode, 80)

            if sample_rate != 16000:
                scale_factor = 16000.0 / sample_rate
                threshold = threshold * math.sqrt(scale_factor)

            is_speech = rms > threshold

            # Diagnostico: mostrar nivel de audio periodico
            SimpleVAD._diag_counter += 1
            if SimpleVAD._diag_counter % 50 == 0:
                peak = np.max(np.abs(samples))
                logger.info(
                    f"Audio diagnostic: RMS={rms:.1f} threshold={threshold:.1f} peak={peak} speech={is_speech}"
                )

            if is_speech:
                self._speech_counter += 1
                self._silence_counter = 0
                logger.debug(f"VAD: voz detectada (RMS={rms:.1f} > {threshold:.1f})")
            else:
                self._silence_counter += 1
                if self._speech_counter > 0:
                    self._speech_counter = max(0, self._speech_counter - 1)

            return is_speech

        except Exception as e:
            logger.error(f"SimpleVAD error: {e}")
            return True


class VoiceEngine(QObject):
    command_recognized = Signal(str)
    listening_state = Signal(bool)
    tts_started = Signal()
    tts_completed = Signal()
    recording_state = Signal(bool)  # NUEVO: señal para estado de grabación PTT

    def __init__(self, config, language_manager=None, parent=None):
        super().__init__(parent)
        self._cmd_queue = queue.Queue()  # Cola thread-safe para comandos de voz
        self.audio_thread = None
        self.config = config
        self.language_manager = language_manager
        self.is_listening = False
        self._stream = None
        self._input_device = None
        self._audio_lock = threading.Lock()

        # NUEVO: Soporte para grabación puntual (PTT)
        self._is_recording = False
        self._record_buffer = bytearray()
        self._record_stream = None
        self._record_stop_event = threading.Event()

        # SISTEMA INTELIGENTE CON VAD
        self.audio_data = bytearray()

        # CONFIGURACION VAD
        vad_config = self.config.get("vad", {})
        self.vad_enabled = vad_config.get("enabled", True)
        self.vad_mode = vad_config.get("mode", 2)
        self.vad = None
        self._init_vad()

        # FIXED: Ensure language is always a valid string
        raw_lang = self.config.get("language", "es")
        if isinstance(raw_lang, str) and raw_lang in ["es", "en"]:
            self.current_lang = raw_lang
        else:
            self.current_lang = "es"
            logger.warning(f"Invalid language detected: {raw_lang}, using Spanish as fallback")
        self.model_path = self.get_model_path()

        # EAGER LOADING: Cargar modelo inmediatamente para mejor UX
        self.model = None
        self.recognizer = None
        self.model_loaded = False

        # SOLUCION: No cargar modelo en __init__ para evitar freeze en splash
        logger.info(f"Modelo Vosk {self.current_lang.upper()} preparado para carga diferida")

        # NUEVO: Control para pausar procesamiento de comandos durante dictado
        self.pause_command_processing = False

    def _init_vad(self):
        """Inicializar Voice Activity Detection (sin dependencia webrtcvad)"""
        try:
            if self.vad_enabled:
                self.vad = SimpleVAD(mode=self.vad_mode)
                vad_mode_names = {0: "Muy Conservador", 1: "Conservador", 2: "Equilibrado", 3: "Sensible"}
                logger.info(
                    f"VAD inicializado (SimpleVAD) - Modo: {self.vad_mode} ({vad_mode_names.get(self.vad_mode, 'Desconocido')})"
                )
            else:
                self.vad = None
                logger.info("VAD deshabilitado por configuracion")
        except Exception as e:
            logger.error(f"Error inicializando VAD: {str(e)}")
            self.vad = None
            self.vad_enabled = False

    def get_model_path(self):
        """Obtiene la ruta del modelo Vosk segun el idioma actual CON VERIFICACION"""
        is_frozen = getattr(sys, 'frozen', False)

        possible_paths = []

        if is_frozen:
            base_dir = os.path.dirname(sys.executable)
            possible_paths.extend([
                os.path.join(base_dir, "models", "vosk"),
                os.path.join(base_dir, "_internal", "models", "vosk"),
                os.path.join(base_dir, "..", "models", "vosk"),
                os.path.join(base_dir, "..", "_internal", "models", "vosk")
            ])

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)

        possible_paths.extend([
            os.path.join(project_root, "models", "vosk"),
            os.path.join(project_root, "_internal", "models", "vosk"),
            os.path.join(project_root, "..", "models", "vosk"),
            os.path.join(project_root, "..", "_internal", "models", "vosk")
        ])

        local_appdata = os.environ.get('LOCALAPPDATA', '')
        if local_appdata:
            possible_paths.append(os.path.join(local_appdata, 'EVA', 'models', 'vosk'))

        model_names = {
            "es": "vosk-model-small-es-0.42",
            "en": "vosk-model-small-en-us-0.15"
        }

        for base_path in possible_paths:
            if not base_path or not os.path.exists(base_path):
                continue

            model_name = model_names.get(self.current_lang, model_names["es"])
            model_path = os.path.join(base_path, model_name)

            if os.path.exists(model_path):
                logger.info(f"Modelo {self.current_lang.upper()} encontrado en: {model_path}")
                return model_path

            for item in os.listdir(base_path):
                if "vosk-model" in item:
                    item_path = os.path.join(base_path, item)
                    if os.path.isdir(item_path):
                        logger.warning(f"Usando modelo alternativo encontrado en: {item_path}")
                        return item_path

        try:
            from core.dynamic_path_resolver import dynamic_path_resolver
            target_path = dynamic_path_resolver.get_vosk_model_path(self.current_lang)
            if os.path.exists(target_path):
                logger.info(f"Modelo encontrado a traves de dynamic_path_resolver: {target_path}")
                return target_path
        except Exception as e:
            logger.warning(f"Error usando dynamic_path_resolver: {str(e)}")

        fallback_path = os.path.join("models", "vosk", model_names.get(self.current_lang, model_names["es"]))
        logger.error(f"No se pudo encontrar ningun modelo Vosk. Ultima ruta intentada: {fallback_path}")
        return fallback_path

    def _ensure_model_loaded(self):
        """Verifica que el modelo este cargado"""
        if not self.model_loaded:
            logger.warning("Modelo no estaba cargado, cargando de emergencia...")
            return self.load_model_optimized()
        return True

    def load_model_optimized(self):
        """Carga optimizada del modelo de reconocimiento de voz"""
        import time
        start_time = time.time()

        try:
            if not os.path.exists(self.model_path):
                logger.error(f"Modelo Vosk no encontrado en: {self.model_path}")
                self.model_loaded = False
                return False

            logger.info(f"Cargando modelo desde: {self.model_path}")

            if getattr(sys, 'frozen', False):
                logger.info("Detectado entorno compilado, usando carga especial para ejecutables")
                return self._load_model_for_executable()
            else:
                logger.info("Entorno de desarrollo, usando carga estandar")
                return self._load_model_standard()

        except Exception as e:
            load_time = time.time() - start_time
            logger.error(f"Error cargando modelo Vosk despues de {load_time:.2f}s: {str(e)}")
            self.model_loaded = False
            return False

    def _load_model_standard(self):
        """Carga estandar para entorno de desarrollo"""
        import time
        start_time = time.time()

        try:
            if not os.path.exists(self.model_path):
                logger.error(f"La ruta del modelo no existe: {self.model_path}")
                return False

            if not os.access(self.model_path, os.R_OK):
                logger.error(f"No se tienen permisos de lectura en: {self.model_path}")
                return False

            required_files = [
                os.path.join(self.model_path, 'am', 'final.mdl'),
                os.path.join(self.model_path, 'conf', 'model.conf'),
                os.path.join(self.model_path, 'graph', 'HCLr.fst')
            ]

            for req_file in required_files:
                if not os.path.exists(req_file):
                    logger.error(f"Archivo de modelo requerido no encontrado: {req_file}")
                    return False

            logger.info(f"Intentando cargar modelo desde: {self.model_path}")

            try:
                self.model = Model(self.model_path)
                self.recognizer = KaldiRecognizer(self.model, 16000)

                if not self.recognizer.AcceptWaveform(b'\x00' * 320):
                    self.model_loaded = True
                    load_time = time.time() - start_time
                    logger.info(f"Modelo Vosk {self.current_lang.upper()} cargado exitosamente en {load_time:.2f}s")
                    return True
                else:
                    logger.error("El modelo se cargo pero no responde correctamente")
                    return False

            except Exception as e:
                logger.error(f"Error al cargar el modelo Vosk: {str(e)}")
                return False

        except Exception as e:
            load_time = time.time() - start_time
            logger.error(f"Error en carga estandar despues de {load_time:.2f}s: {str(e)}")
            import traceback
            logger.error(f"Traceback completo: {traceback.format_exc()}")
            return False

    def _load_model_for_executable(self):
        """Carga especial para entornos compilados con PyInstaller"""
        import time

        logger.info("Iniciando carga especial para ejecutable...")

        load_result = {'success': False, 'error': None}

        def load_with_safety():
            try:
                start_time = time.time()
                abs_model_path = os.path.abspath(self.model_path)
                logger.info(f"Ruta absoluta del modelo: {abs_model_path}")

                logger.info("Instanciando Model() de Vosk...")
                self.model = Model(abs_model_path)

                logger.info("Creando KaldiRecognizer...")
                self.recognizer = KaldiRecognizer(self.model, 16000)

                load_time = time.time() - start_time
                logger.info(f"Modelo cargado exitosamente en {load_time:.2f}s")

                load_result['success'] = True
                self.model_loaded = True

            except Exception as e:
                load_result['error'] = str(e)
                load_result['success'] = False
                logger.error(f"Error en hilo de carga: {str(e)}")

        load_thread = threading.Thread(target=load_with_safety, daemon=True, name="VoskModelLoader")
        load_thread.start()

        timeout_seconds = 15
        load_thread.join(timeout=timeout_seconds)

        if load_thread.is_alive():
            logger.error(f"TIMEOUT: Carga de modelo excedió {timeout_seconds}s - Abortando")
            self.model_loaded = False
            return False

        if load_result['success']:
            logger.info("Carga especial para ejecutable completada exitosamente")
            return True
        else:
            error_msg = load_result.get('error', 'Error desconocido')
            logger.error(f"Carga especial falló: {error_msg}")
            self.model_loaded = False
            return False

    def load_model(self):
        """Metodo legacy - redirige al optimizado"""
        return self.load_model_optimized()

    def unload_model(self):
        """Libera recursos del modelo Vosk"""
        try:
            if self.model_loaded:
                self.model = None
                self.recognizer = None
                self.model_loaded = False
                logger.warning("Modelo Vosk liberado (operacion de emergencia)")
        except Exception as e:
            logger.error(f"Error liberando modelo Vosk: {str(e)}")

    def get_model_info(self):
        """Obtiene informacion del estado del modelo"""
        return {
            "loaded": self.model_loaded,
            "language": self.current_lang,
            "model_path": self.model_path,
            "model_exists": os.path.exists(self.model_path) if self.model_path else False,
            "memory_usage": "~50-100MB" if self.model_loaded else "0MB"
        }

    def update_config(self, config):
        """Actualiza la configuracion del motor de voz"""
        self.config = config
        new_lang = self.config.get("language", "es")

        if new_lang != self.current_lang:
            logger.info(f"Cambiando idioma de reconocimiento de {self.current_lang} a {new_lang}")
            self.current_lang = new_lang
            self.model_path = self.get_model_path()

            if self.model_loaded:
                self.unload_model()

            self.load_model()
            logger.info(f"Modelo Vosk cambiado a {new_lang.upper()}")

            if self.language_manager:
                self.language_manager.current_lang = new_lang

    def update_vad_config(self, vad_enabled=None, vad_mode=None):
        """Actualizar configuracion VAD dinamicamente"""
        try:
            config_changed = False

            if vad_enabled is not None and vad_enabled != self.vad_enabled:
                self.vad_enabled = vad_enabled
                config_changed = True

            if vad_mode is not None and vad_mode != self.vad_mode:
                self.vad_mode = vad_mode
                config_changed = True

            if config_changed:
                self._init_vad()
                logger.info(f"Configuracion VAD actualizada - Habilitado: {self.vad_enabled}, Modo: {self.vad_mode}")

        except Exception as e:
            logger.error(f"Error actualizando configuracion VAD: {str(e)}")

    def get_vad_status(self):
        """Obtener estado actual de VAD"""
        return {
            "enabled": self.vad_enabled,
            "mode": self.vad_mode,
            "mode_name": {0: "Muy Conservador", 1: "Conservador", 2: "Equilibrado", 3: "Sensible"}.get(self.vad_mode, "Desconocido"),
            "initialized": self.vad is not None
        }

    def start(self):
        """Inicia el motor de reconocimiento de voz"""
        if self.is_listening:
            return

        # Intentar adquirir AudioLock (evita conflicto con dictado)
        if not audio_lock.acquire("voice_engine"):
            logger.warning("AudioLock en uso por dictado - no se puede iniciar VoiceEngine")
            return

        if not self.model_loaded:
            logger.info("Cargando modelo Vosk de forma diferida...")
            if not self.load_model_optimized():
                logger.error("No se pudo cargar el modelo, reconocimiento no disponible")
                audio_lock.release("voice_engine")
                return

        # Encontrar dispositivo de entrada disponible
        self._input_device = self._find_input_device()

        self.is_listening = True
        self.stop_listening = threading.Event()
        self.audio_thread = threading.Thread(target=self.listen_loop, daemon=True, name="VoiceListen")
        self.audio_thread.start()
        logger.info("Motor de reconocimiento de voz iniciado")

    def _find_input_device(self):
        """Encuentra el dispositivo de entrada real, ignorando cables virtuales y usando el default solo si es físico"""
        import time as _time

        # Palabras clave de dispositivos VIRTUALES que hay que evitar como primera opción
        VIRTUAL_KEYWORDS = [
            'vb-audio', 'virtual cable', 'virtual mic', 'audiorelay',
            'cable output', 'cable input', 'cable in', 'vb audio',
            'voicemeeter', 'blackhole', 'soundflower', 'vac ',
            'virtual audio', 'vb_audio', 'vbaudio'
        ]

        def is_virtual(name: str) -> bool:
            n = name.lower()
            return any(kw in n for kw in VIRTUAL_KEYWORDS)

        def try_open(device_idx, label="") -> bool:
            """Intenta abrir el dispositivo brevemente. True si funciona."""
            try:
                s = sd.InputStream(
                    samplerate=SAMPLE_RATE, blocksize=CHUNK_SIZE, channels=1,
                    dtype='int16', device=device_idx, latency='low'
                )
                s.start()
                _time.sleep(0.15)
                s.stop()
                s.close()
                logger.info(f"  ✅ [{device_idx}] {label} - OK")
                return True
            except Exception as e:
                logger.warning(f"  ❌ [{device_idx}] {label} - falló: {e}")
                return False

        try:
            devices = sd.query_devices()
            apis = sd.query_hostapis()

            def api_name(dev):
                hapi = dev.get('hostapi', -1)
                if 0 <= hapi < len(apis):
                    return apis[hapi].get('name', '')
                return ''

            # Obtener el default de Windows
            try:
                win_default = sd.default.device[0]
            except Exception:
                win_default = None

            logger.info(f"Total dispositivos de audio encontrados: {len(devices)}")
            for i, dev in enumerate(devices):
                ch_in = dev.get('max_input_channels', 0)
                ch_out = dev.get('max_output_channels', 0)
                api = api_name(dev)
                name = dev.get('name', '?')
                tag = "(DEFAULT) " if i == win_default else ""
                virt = " [VIRTUAL]" if is_virtual(name) else ""
                if ch_in > 0:
                    logger.info(f"  [{i}] {tag}{name} (entrada:{ch_in}) api={api}{virt}")
                else:
                    logger.info(f"  [{i}] {name} (solo salida:{ch_out}) api={api}")

            # --- Candidatos de entrada ordenados por preferencia ---
            # Prioridad: MME > DirectSound > WASAPI (todos funcionales con Blocking API)
            # Excluir WDM-KS (no soporta Blocking API)
            GOOD_APIS = ['mme', 'windows directsound', 'windows wasapi']

            physical = []   # micros físicos reales
            virtual_devs = []  # virtuales (fallback de último recurso)

            for i, dev in enumerate(devices):
                if dev.get('max_input_channels', 0) == 0:
                    continue
                a = api_name(dev).lower()
                if not any(good in a for good in GOOD_APIS):
                    continue  # saltar WDM-KS y otros problemáticos
                name = dev.get('name', '')
                if is_virtual(name):
                    virtual_devs.append(i)
                else:
                    physical.append(i)

            logger.info(f"Micrófonos físicos candidatos: {physical}")
            logger.info(f"Dispositivos virtuales candidatos: {virtual_devs}")
            logger.info(f"Default Windows: [{win_default}] {'(virtual)' if win_default is not None and is_virtual(devices[win_default].get('name','')) else '(físico)'}")

            # 1. Si el default de Windows es un micro físico → usarlo directamente
            if win_default is not None and win_default in physical:
                name = devices[win_default].get('name', '?')
                logger.info(f"Default Windows es físico → probando [{win_default}] '{name}'")
                if try_open(win_default, name):
                    return win_default

            # 2. Primer micro físico disponible (el que Windows llame "Asignador" suele ser el real)
            for idx in physical:
                name = devices[idx].get('name', '?')
                logger.info(f"Probando micro físico [{idx}] '{name}'...")
                if try_open(idx, name):
                    return idx

            # 3. Último recurso: default de Windows aunque sea virtual
            if win_default is not None and win_default < len(devices):
                if devices[win_default].get('max_input_channels', 0) > 0:
                    name = devices[win_default].get('name', '?')
                    logger.warning(f"Sin micro físico disponible, usando default virtual [{win_default}] '{name}'")
                    if try_open(win_default, name):
                        return win_default

            # 4. Cualquier virtual funcional
            for idx in virtual_devs:
                name = devices[idx].get('name', '?')
                if try_open(idx, name):
                    logger.warning(f"Usando dispositivo virtual como fallback [{idx}] '{name}'")
                    return idx

            logger.error("No se encontró ningún dispositivo de entrada utilizable")
            return None

        except Exception as e:
            logger.error(f"Error buscando dispositivo de entrada: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def test_microphone(self, duration=3, output_file="debug/mic_test.wav") -> dict:
        """
        Registra audio del micrófono durante 'duration' segundos y guarda en WAV.
        Útil para diagnóstico de problemas de captura de audio.

        Args:
            duration: Duración de la grabación en segundos (default: 3)
            output_file: Ruta del archivo WAV de salida

        Returns:
            dict con información del test:
                - success: bool
                - device: str (nombre del dispositivo usado)
                - max_rms: float (RMS máximo detectado)
                - avg_rms: float (RMS promedio)
                - samples_count: int
                - has_audio: bool (si se detectó audio significativo)
                - error: str or None
        """
        import os
        os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else ".", exist_ok=True)

        result = {
            "success": False,
            "device": None,
            "max_rms": 0.0,
            "avg_rms": 0.0,
            "samples_count": 0,
            "has_audio": False,
            "error": None
        }

        try:
            device = self._input_device if self._input_device is not None else sd.default.device[0]
            device_info = sd.query_devices(device)
            device_name = device_info.get('name', f'Dispositivo {device}')
            result["device"] = device_name

            logger.info(f"🔍 Test de micrófono iniciado: [{device}] '{device_name}' ({duration}s)")

            audio_frames = []

            def callback(indata, frames, time_info, status):
                if status:
                    logger.debug(f"  Test mic status: {status}")
                audio_frames.append(indata.copy())

            stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                blocksize=CHUNK_SIZE,
                channels=1,
                dtype='int16',
                device=device,
                callback=callback
            )

            stream.start()
            import time as _time
            _time.sleep(duration)
            stream.stop()
            stream.close()

            if not audio_frames:
                result["error"] = "No se recibieron datos de audio"
                logger.warning(f"🔍 Test micrófono: SIN datos recibidos de '{device_name}'")
                return result

            all_audio = np.concatenate(audio_frames, axis=0)
            result["samples_count"] = len(all_audio)

            # Calcular RMS por frame
            frame_size = 1024
            rms_values = []
            for i in range(0, len(all_audio) - frame_size + 1, frame_size):
                frame = all_audio[i:i + frame_size]
                rms = np.sqrt(np.mean(frame.astype(np.float64) ** 2))
                rms_values.append(rms)

            if rms_values:
                result["max_rms"] = float(np.max(rms_values))
                result["avg_rms"] = float(np.mean(rms_values))

            # Umbral para considerar que hay audio real (no solo ruido de fondo)
            # En silencio total típico: RMS < 5-10
            # Voz normal: RMS > 500-2000
            audio_threshold = 20  # Cualquier valor por encima indica que el micrófono funciona
            result["has_audio"] = result["avg_rms"] > audio_threshold

            if result["has_audio"]:
                logger.info(f"🔍 Test micrófono OK: '{device_name}' "
                           f"avg_rms={result['avg_rms']:.1f}, max_rms={result['max_rms']:.1f}, "
                           f"frames={len(audio_frames)}")
            else:
                logger.warning(f"🔍 Test micrófono: audio muy bajo en '{device_name}' "
                              f"avg_rms={result['avg_rms']:.1f} (¿micrófono silenciado?)")

            # Guardar WAV
            import wave as _wave
            with _wave.open(output_file, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes((all_audio * 32767 / np.max(np.abs(all_audio))).astype(np.int16).tobytes())
            logger.info(f"🔍 Audio guardado en: {output_file}")

            result["success"] = True

        except sd.PortAudioError as e:
            result["error"] = f"Error de PortAudio: {str(e)}"
            logger.error(f"🔍 Error de PortAudio en test de micrófono: {e}")
        except Exception as e:
            result["error"] = f"Error: {str(e)}"
            logger.error(f"🔍 Error en test de micrófono: {e}")
            import traceback
            logger.error(traceback.format_exc())

        return result

    def diagnose_audio_system(self) -> dict:
        """
        Diagnóstico completo del sistema de audio.
        Útil para troubleshooting cuando el micrófono no captura audio.

        Returns:
            dict con información de diagnóstico
        """
        result = {
            "devices": [],
            "default_input": None,
            "selected_input": None,
            "has_valid_input": False,
            "issues": []
        }

        try:

            # Listar todos los dispositivos
            devices = sd.query_devices()
            default_input = sd.default.device[0] if hasattr(sd.default, 'device') and sd.default.device else None

            result["default_input"] = default_input
            result["selected_input"] = self._input_device

            for i, dev in enumerate(devices):
                dev_info = {
                    "index": i,
                    "name": dev.get('name', '?'),
                    "max_input_ch": dev.get('max_input_channels', 0),
                    "max_output_ch": dev.get('max_output_channels', 0),
                    "is_input": dev.get('max_input_channels', 0) > 0,
                    "hostapi": dev.get('hostapi', -1),
                    "is_default": i == default_input
                }
                result["devices"].append(dev_info)

                if dev_info["is_input"]:
                    logger.info(f"  🎤 [{i}] {dev_info['name']} "
                               f"(entradas:{dev_info['max_input_ch']}) "
                               f"{'[DEFAULT] ' if dev_info['is_default'] else ''}"
                               f"api:{dev_info['hostapi']}")

            # Verificar privacidad del micrófono (Windows)
            try:
                # Intentar verificar si el micrófono está accesible
                # Esto es una verificación básica - si el stream se puede abrir, está OK
                test_device = self._input_device if self._input_device is not None else default_input
                if test_device is not None and test_device < len(devices):
                    test_info = sd.query_devices(test_device)
                    if test_info.get('max_input_channels', 0) > 0:
                        result["has_valid_input"] = True
                    else:
                        result["issues"].append("El dispositivo seleccionado no tiene canales de entrada")
            except Exception as e:
                result["issues"].append(f"Error verificando acceso al micrófono: {e}")

            if not result["has_valid_input"] and result["devices"]:
                input_devs = [d for d in result["devices"] if d["is_input"]]
                if input_devs:
                    result["issues"].append(
                        f"Hay {len(input_devs)} dispositivo(s) de entrada pero ninguno seleccionado correctamente"
                    )
                else:
                    result["issues"].append("No se encontraron dispositivos de entrada de audio")

            logger.info(f"🔍 Diagnóstico de audio: {len(result['devices'])} dispositivos, "
                       f"default={result['default_input']}, selected={result['selected_input']}, "
                       f"valid={result['has_valid_input']}")
            if result["issues"]:
                for issue in result["issues"]:
                    logger.warning(f"  ⚠️ Issue: {issue}")

        except Exception as e:
            logger.error(f"Error en diagnóstico de audio: {e}")
            result["issues"].append(str(e))

        return result

    def stop(self):
        """Detiene el motor de reconocimiento"""
        self.is_listening = False
        if hasattr(self, 'stop_listening') and self.stop_listening:
            self.stop_listening.set()

        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception as e:
                logger.warning(f"Error cerrando stream sounddevice: {str(e)}")
            self._stream = None

        audio_lock.release("voice_engine")
        logger.info("Motor de voz detenido")

    def _get_input_device(self):
        # Obtiene el dispositivo de entrada actual o encuentra uno valido
        try:
            if self._input_device is not None:
                device_info = sd.query_devices(self._input_device)
                if device_info.get('max_input_channels', 0) > 0:
                    return self._input_device
        except Exception:
            pass
        try:
            return sd.default.device[0]
        except Exception:
            pass
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev.get('max_input_channels', 0) > 0:
                return i
        return None

    def _record_callback(self, indata, frames, time_info, status):
        if self._record_stop_event.is_set():
            raise sd.CallbackStop()
        if status:
            logger.debug(f"Record status: {status}")
        self._record_buffer.extend(indata.tobytes())

    def start_recording(self):
        if self._is_recording:
            return
        device = self._get_input_device()
        if device is None:
            logger.error("No se encontro dispositivo de entrada para grabacion")
            return
        self._is_recording = True
        self._record_buffer = bytearray()
        self._record_stop_event.clear()
        self.recording_state.emit(True)
        try:
            self._record_stream = sd.InputStream(
                samplerate=SAMPLE_RATE, blocksize=CHUNK_SIZE, channels=1,
                dtype='int16', device=device, callback=self._record_callback
            )
            self._record_stream.start()
            logger.info("Grabacion PTT iniciada")
        except Exception as e:
            logger.error(f"Error iniciando grabacion PTT: {str(e)}")
            self._is_recording = False
            self.recording_state.emit(False)

    def stop_recording(self):
        if not self._is_recording:
            return
        self._is_recording = False
        self._record_stop_event.set()
        if self._record_stream is not None:
            try:
                self._record_stream.stop()
                self._record_stream.close()
            except Exception as e:
                logger.warning(f"Error cerrando stream de grabacion: {str(e)}")
            self._record_stream = None
        self.recording_state.emit(False)
        if len(self._record_buffer) >= 8000:
            audio_bytes = bytes(self._record_buffer)
            self._process_recorded_audio(audio_bytes)
        else:
            logger.warning("Audio grabado demasiado corto, ignorando")
        self._record_buffer = bytearray()

    def _process_recorded_audio(self, audio_bytes):
        try:
            if not self.model_loaded or not self.recognizer:
                if not self.load_model_optimized():
                    logger.error("No se pudo cargar el modelo para procesar audio")
                    return
            if self.recognizer.AcceptWaveform(audio_bytes):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "").strip()
                if text:
                    logger.info(f"PTT reconocido: {text}")
                    self._cmd_queue.put(text)
                else:
                    logger.info("No se reconocio texto del audio")
            else:
                logger.info("No se detecto habla en la grabacion")
        except Exception as e:
            logger.error(f"Error procesando audio grabado: {str(e)}")

    def _stream_callback(self, indata, frames, time_info, status):
        """Callback de sounddevice - VAD manual con acumulacion y corte por silencio"""
        if status:
            logger.debug(f"SoundDevice status: {status}")

        if self.stop_listening is not None and self.stop_listening.is_set():
            raise sd.CallbackStop()

        try:
            rms = float(np.sqrt(np.mean(indata.astype(np.float64) ** 2)))
            peak = int(np.max(np.abs(indata)))

            SimpleVAD._diag_counter += 1
            if SimpleVAD._diag_counter <= 3 or SimpleVAD._diag_counter % 20 == 0:
                logger.info(f"Audio recibido: RMS={rms:.1f} peak={peak:.0f} frames={frames} len={len(indata)}")

            audio_bytes = indata.tobytes()

            # VAD por RMS - umbral leido de config (slider de sensibilidad)
            # sensitivity 0.0=max sensible -> RMS bajo; 1.0=min sensible -> RMS alto
            # Rango util: RMS 30 (muy sensible) a 200 (poco sensible). Default 80.
            sensitivity = self.config.get("sensitivity", 0.5)
            RMS_SPEECH  = int(RMS_SPEECH_BASE + sensitivity * RMS_SPEECH_RANGE)  # 0.5 -> 115, 0.0 -> 30, 1.0 -> 200

            if rms > RMS_SPEECH:
                self._vad_speech_frames  = getattr(self, '_vad_speech_frames',  0) + 1
                self._vad_silence_frames = 0
                self.audio_data.extend(audio_bytes)
            else:
                self._vad_silence_frames = getattr(self, '_vad_silence_frames', 0) + 1
                if len(self.audio_data) > 0:
                    self.audio_data.extend(audio_bytes)  # seguir grabando cola de silencio
                if self._vad_silence_frames >= SILENCE_FRAMES_TO_CUT:
                    if len(self.audio_data) >= MIN_SPEECH_BYTES:
                        logger.info(f"Segmento listo: {len(self.audio_data)} bytes")
                        self.process_audio_direct(bytes(self.audio_data))
                    elif len(self.audio_data) > 0:
                        logger.debug(f"Segmento descartado (muy corto): {len(self.audio_data)} bytes")
                    self.audio_data = bytearray()
                    self._vad_speech_frames  = 0
                    self._vad_silence_frames = 0

        except Exception as e:
            logger.error(f"Error en callback de audio: {str(e)}")

    def listen_loop(self):
        """Bucle de escucha usando sounddevice"""
        try:
            logger.info("Escuchando... (sounddevice)")
            self.listening_state.emit(True)

            # Iniciar stream de captura con sounddevice
            stream_kwargs = {
                'samplerate': 16000,
                'blocksize': 1024,
                'channels': 1,
                'dtype': 'int16',
                'callback': self._stream_callback,
                'finished_callback': lambda: logger.debug("Stream finished")
            }

            # NUEVO: Manejo robusto de fallback de dispositivo
            devices_to_try = []
            if self._input_device is not None:
                devices_to_try.append(self._input_device)
            # Agregar default como fallback
            try:
                default_dev = sd.default.device[0]
                if default_dev not in devices_to_try:
                    devices_to_try.append(default_dev)
            except Exception:
                pass
            # Agregar None (default automático de sounddevice) como último fallback
            devices_to_try.append(None)

            stream_opened = False
            used_device = None

            for dev in devices_to_try:
                try:
                    kwargs = stream_kwargs.copy()
                    if dev is not None:
                        kwargs['device'] = dev
                    self._stream = sd.InputStream(**kwargs)
                    self._stream.start()
                    stream_opened = True
                    used_device = dev
                    logger.info(
                        f"Escuchando en dispositivo: {dev if dev is not None else 'default (auto)'}"
                    )
                    break
                except sd.PortAudioError as e:
                    logger.warning(f"Dispositivo {dev if dev is not None else 'default'} falló: {e}")
                    if self._stream is not None:
                        try:
                            self._stream.close()
                        except Exception:
                            pass
                        self._stream = None
                    continue
                except Exception as e:
                    logger.warning(f"Error abriendo dispositivo {dev}: {e}")
                    continue

            if not stream_opened:
                logger.error("No se pudo abrir NINGÚN dispositivo de captura de audio")
                self.is_listening = False
                self.listening_state.emit(False)
                return

            logger.info(f"🔊 Stream de audio activo en dispositivo: {used_device}")

            # Esperar mientras se escucha
            while self.is_listening and (self.stop_listening is None or not self.stop_listening.is_set()):
                time.sleep(0.1)

        except sd.PortAudioError as e:
            logger.error(f"Error de PortAudio/sounddevice: {str(e)}")
            logger.error("No se pudo abrir el microfono. Verifica que esta conectado y no en uso por otra aplicacion.")
            self.is_listening = False
            self.listening_state.emit(False)
        except Exception as e:
            logger.error(f"Error en el bucle de escucha: {str(e)}")
            self.is_listening = False
        finally:
            self.listening_state.emit(False)
            if self._stream is not None:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception:
                    pass
                self._stream = None

    def process_audio_direct(self, audio_bytes):
        """Procesamiento con VAD"""
        try:
            if not self.model_loaded or not self.recognizer:
                return

            if self.vad_enabled and self.vad:
                try:
                    frame_size = 640  # 20ms a 16kHz
                    is_speech_detected = False
                    for i in range(0, len(audio_bytes) - frame_size + 1, frame_size):
                        frame = audio_bytes[i:i + frame_size]
                        if self.vad.is_speech(frame, 16000):
                            is_speech_detected = True
                            break

                    if not is_speech_detected:
                        return  # Ignorar ruido

                except Exception as vad_error:
                    logger.warning(f"VAD error, procesando sin filtro: {str(vad_error)}")

            if self.recognizer.AcceptWaveform(audio_bytes):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "").strip()

                if text:
                    logger.info(f"Comando reconocido: {text}")

                    if self.pause_command_processing:
                        logger.info(f"Dictado pausado - texto ignorado: {text}")
                        return

                    self._cmd_queue.put(text)  # thread-safe: main thread lo emite via QTimer

        except Exception as e:
            logger.error(f"Error procesando audio: {str(e)}")

    def poll_commands(self):
        """Llamado desde QTimer en main thread - emite signals de forma thread-safe"""
        try:
            while not self._cmd_queue.empty():
                text = self._cmd_queue.get_nowait()
                self.command_recognized.emit(text)
        except Exception:
            pass

    def _schedule_auto_unload(self):
        """Programa la descarga automatica del modelo despues de inactividad"""
        try:
            from PySide6.QtCore import QTimer

            self._cancel_auto_unload_timer()

            self.auto_unload_timer = QTimer()
            self.auto_unload_timer.setSingleShot(True)
            self.auto_unload_timer.timeout.connect(self._auto_unload_model)
            self.auto_unload_timer.start(self.auto_unload_delay * 1000)

            logger.debug(f"Timer de descarga automatica programado para {self.auto_unload_delay}s")
        except Exception as e:
            logger.error(f"Error programando descarga automatica: {str(e)}")

    def _cancel_auto_unload_timer(self):
        """Cancela el timer de descarga automatica"""
        if hasattr(self, 'auto_unload_timer') and self.auto_unload_timer and self.auto_unload_timer.isActive():
            self.auto_unload_timer.stop()
            self.auto_unload_timer = None

    def _auto_unload_model(self):
        """Descarga automatica del modelo por inactividad"""
        try:
            current_time = time.time()
            idle_time = current_time - self.last_used_time

            if idle_time >= self.auto_unload_delay:
                logger.info(f"Descargando modelo automaticamente despues de {idle_time:.0f}s de inactividad")
                self.unload_model()
            else:
                remaining_time = self.auto_unload_delay - idle_time
                self.auto_unload_timer.start(int(remaining_time * 1000))

        except Exception as e:
            logger.error(f"Error en descarga automatica: {str(e)}")

    def reset_audio(self):
        """Reinicia los buffers de audio"""
        self.audio_data = bytearray()
        if hasattr(self, 'audio_buffer'):
            self.audio_buffer.clear()
        if hasattr(self, 'speech_frames'):
            self.speech_frames = 0
        if hasattr(self, 'silence_frames'):
            self.silence_frames = 0

    def _is_critical_command(self, text):
        """Identifica comandos criticos"""
        critical_patterns = [
            "abre data", "abrir data", "open data",
            "abre", "abrir", "open"
        ]
        text_lower = text.lower().strip()
        return any(pattern in text_lower for pattern in critical_patterns)

    def _execute_critical_command_direct(self, text):
        """Ejecuta comandos criticos directamente"""
        try:
            text_lower = text.lower().strip()

            if "data" in text_lower and ("abre" in text_lower or "abrir" in text_lower or "open" in text_lower):
                import subprocess
                try:
                    os.startfile("D:/")
                except Exception:
                    try:
                        subprocess.run(["explorer", "D:/"], check=False)
                    except Exception:
                        pass
                return

            logger.info(f"Comando reconocido: {text}")
            self._cmd_queue.put(text)  # thread-safe: main thread lo emite via QTimer

        except Exception:
            self._cmd_queue.put(text)  # thread-safe: main thread lo emite via QTimer

    def save_audio_debug(self, data, prefix="audio"):
        """Guarda el audio para depuracion"""
        try:
            os.makedirs("debug", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"debug/{prefix}_{timestamp}.wav"

            with wave.open(filename, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(data)

            logger.info(f"Audio guardado para depuracion: {filename}")
        except Exception as e:
            logger.error(f"Error guardando audio: {str(e)}")