#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Punto de entrada principal para EVA - Versión Final Corregida
"""

import os
import sys
import ctypes
import traceback
import json
import ssl
import certifi

# Configurar certificados SSL para requests
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
ssl_context = ssl.create_default_context()
ssl_context.load_verify_locations(cafile=certifi.where())

import multiprocessing

# -----------------------------------------------------------------------------
# Configuración inicial - SISTEMA AUTO-ADAPTABLE
# -----------------------------------------------------------------------------

# 1. Inicializar sistema de rutas dinámicas
from core.dynamic_path_resolver import dynamic_path_resolver

BASE_DIR = dynamic_path_resolver.get_path('base')
os.chdir(BASE_DIR)  # Directorio de trabajo = directorio de la app

# 2. Configurar logging y manejo de excepciones
from core.initialization.bootstrap import setup_logging, setup_exception_handlers
log_file = dynamic_path_resolver.get_log_file('eva_debug.log')
logger = setup_logging(log_file)
setup_exception_handlers(logger)

logger.info("=" * 80)
logger.info(f"INICIO DE EVA - Directorio base: {BASE_DIR}")
logger.info("=" * 80)

# 3. Inicializar gestor de configuración unificado
from core.config_manager_unified import config_manager

# 4. Sistema de ubicación de recursos ROBUSTO
def encontrar_recurso(nombre, posibles_rutas):
    """Busca un recurso en múltiples ubicaciones posibles con mayor tolerancia"""
    # Rutas prioritarias
    rutas_prioritarias = [
        os.path.join(BASE_DIR, nombre),
        os.path.join(BASE_DIR, "_internal", nombre),
        os.path.join(BASE_DIR, "resources", nombre)
    ]
    
    # Si estamos en un ejecutable, agregar ruta de datos
    if getattr(sys, 'frozen', False):
        rutas_prioritarias.insert(0, os.path.join(BASE_DIR, "_internal", nombre))
    
    for ruta in rutas_prioritarias:
        if os.path.exists(ruta):
            logger.info(f"{nombre.upper()} encontrado en ubicación prioritaria: {ruta}")
            return ruta
    
    # Rutas alternativas
    for ruta in posibles_rutas:
        ruta_completa = os.path.join(BASE_DIR, ruta, nombre)
        if os.path.exists(ruta_completa):
            logger.info(f"{nombre.upper()} encontrado en ruta alternativa: {ruta_completa}")
            return ruta_completa
    
    # Búsqueda profunda como último recurso
    logger.warning(f"Búsqueda profunda para: {nombre}")
    for root, dirs, files in os.walk(BASE_DIR):
        if nombre in files:
            ruta_encontrada = os.path.join(root, nombre)
            logger.info(f"{nombre.upper()} encontrado en búsqueda profunda: {ruta_encontrada}")
            return ruta_encontrada
        elif nombre in dirs:
            ruta_encontrada = os.path.join(root, nombre)
            logger.info(f"{nombre.upper()} encontrado en búsqueda profunda: {ruta_encontrada}")
            return ruta_encontrada
    
    logger.error(f"¡RECURSO CRÍTICO FALTANTE! {nombre} no encontrado en ninguna ubicación")
    return None

# Ubicaciones posibles para cada recurso (ACTUALIZADAS)
RECURSOS = {
    "vosk": ["vosk", "_internal/vosk", "speech_recognition/vosk", "recursos/vosk"],
    "ffmpeg": ["ffmpeg/bin", "_internal/ffmpeg/bin", "bin/ffmpeg", "external/ffmpeg"],
    "resources": ["resources", "_internal/resources", "assets", "recursos"]
}

# Solo buscar voices si estamos en un EXE (para compatibilidad)
if getattr(sys, 'frozen', False):
    RECURSOS["voices"] = ["voices", "_internal/voices", "tts_voices", "recursos/voices", "audio/voices"]

# Encontrar todos los recursos
RUTAS_CRITICAS = {nombre: encontrar_recurso(nombre, rutas) 
                  for nombre, rutas in RECURSOS.items()}

# Verificación de recursos con fallbacks
missing_resources = []
for nombre, ruta in RUTAS_CRITICAS.items():
    if not ruta:
        logger.warning(f"RECURSO FALTANTE: {nombre}")
        missing_resources.append(nombre)

# Manejar recursos faltantes con degradación gradual
if missing_resources:
    if "vosk" in missing_resources:
        logger.warning("Vosk no disponible - reconocimiento de voz deshabilitado")
        os.environ["EVA_VOICE_DISABLED"] = "true"
    
    if "voices" in missing_resources:
        logger.warning("Voces TTS no disponibles - síntesis de voz limitada")
        os.environ["EVA_TTS_LIMITED"] = "true"
    
    if "ffmpeg" in missing_resources:
        logger.warning("FFmpeg no disponible - funciones de audio limitadas")
        os.environ["EVA_AUDIO_LIMITED"] = "true"
    
    # Solo salir si faltan recursos absolutamente críticos
    critical_missing = [r for r in missing_resources if r in ["resources"]]
    if critical_missing:
        logger.critical(f"RECURSOS CRÍTICOS FALTANTES: {critical_missing}")
        ctypes.windll.user32.MessageBoxW(
            0,
            f"Error crítico: Recursos esenciales no encontrados: {', '.join(critical_missing)}\n\nLa aplicación no puede continuar.",
            "EVA - Error de Recursos",
            0x10
        )
        sys.exit(1)
    else:
        logger.info(f"EVA iniciará con funcionalidad limitada debido a recursos faltantes: {missing_resources}")

# 4. Configuración del sistema
path_dirs = [
    RUTAS_CRITICAS.get('ffmpeg', ''),
    os.path.join(BASE_DIR, "_internal", "python-embed"),
    os.path.join(BASE_DIR, "_internal", "python-embed", "Scripts"),
    RUTAS_CRITICAS.get('vosk', ''),
    os.path.join(BASE_DIR, "_internal")
]

path_dirs = [d for d in path_dirs if d is not None and os.path.exists(d)]
os.environ['PATH'] = os.pathsep.join(path_dirs) + os.pathsep + os.environ['PATH']
logger.info(f"PATH configurado: {os.environ['PATH']}")

os.environ["EVA_VOICES_PATH"] = RUTAS_CRITICAS.get("voices", "") or ""
os.environ["EVA_RESOURCES_PATH"] = RUTAS_CRITICAS["resources"] or ""

logger.info(f"Ruta de voces: {os.environ['EVA_VOICES_PATH']}")
logger.info(f"Ruta de recursos: {os.environ['EVA_RESOURCES_PATH']}")

# Configuración DPI para Windows
if os.name == 'nt':
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        logger.info("Configuración DPI aplicada correctamente")
    except Exception as e:
        logger.error(f"Error configurando DPI: {str(e)}")

# Configurar variables de entorno para Qt - MEJORADO PARA STANDALONE
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_SCALE_FACTOR"] = "1.0"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCREEN_SCALE_FACTORS"] = "1.0"

# Variables adicionales para estabilidad fuera de PyCharm
os.environ["QT_QPA_PLATFORM"] = "windows"
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = ""
os.environ["QT_PLUGIN_PATH"] = ""
os.environ["QT_OPENGL"] = "software"  # Usar renderizado por software para mayor compatibilidad
os.environ["QT_QUICK_BACKEND"] = "software"
os.environ["QT_GRAPHICSSYSTEM"] = "raster"  # Sistema de gráficos más estable

# Configuración optimizada de threading y memoria
cpu_count = multiprocessing.cpu_count()
optimal_threads = min(4, max(1, cpu_count // 2))  # Usar máximo 4 hilos, mínimo 1

os.environ["OMP_NUM_THREADS"] = str(optimal_threads)
os.environ["OPENBLAS_NUM_THREADS"] = str(optimal_threads)
os.environ["MKL_NUM_THREADS"] = str(optimal_threads)
os.environ["NUMEXPR_NUM_THREADS"] = str(optimal_threads)
os.environ["VECLIB_MAXIMUM_THREADS"] = str(optimal_threads)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# CUDA optimizations removed - obsolete after Piper TTS migration
# Piper TTS uses CPU exclusively, Ollama manages GPU independently

# -----------------------------------------------------------------------------
# VERIFICACIÓN OLLAMA_EVA - INTEGRADO CON EVA
# -----------------------------------------------------------------------------

def verificar_ollama_eva():
    """Verifica si ollama_eva.exe está disponible"""
    try:
        ollama_eva_path = dynamic_path_resolver.get_path('ollama')
        models_dir = dynamic_path_resolver.get_ollama_models_dir()
        
        # Verificar que ollama_eva existe
        if not os.path.exists(ollama_eva_path):
            logger.error(f"ollama_eva.exe no encontrado en: {ollama_eva_path}")
            return False
        
        # Crear directorio de modelos si no existe
        # os.makedirs(models_dir, exist_ok=True)  # Comentado: Ollama usa sus paths originales
        
        # Configurar variables de entorno para ollama_eva
        os.environ["EVA_OLLAMA_MODELS_PATH"] = models_dir
        os.environ["EVA_NAME"] = "EVA"
        
        logger.info(f"✅ ollama_eva.exe encontrado: {ollama_eva_path}")
        logger.info(f"✅ Directorio de modelos: {models_dir}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verificando ollama_eva: {str(e)}")
        return False

# Verificar Ollama con fallback graceful
if not verificar_ollama_eva():
    logger.warning("ollama_eva.exe no encontrado, usando Ollama estándar del sistema")
    os.environ["EVA_OLLAMA_FALLBACK"] = "true"
    # Continuar con Ollama estándar - funcionalidad de IA puede estar limitada

# -----------------------------------------------------------------------------
# CARGA DE CONFIGURACIÓN SIN WIZARD - VERSIÓN DESARROLLO
# -----------------------------------------------------------------------------

# Rutas de configuración dinámicas
install_config_path = dynamic_path_resolver.get_config_file('install')
knowledge_path = dynamic_path_resolver.get_path('base', 'eva_knowledge_base.json')

# Función para cargar o crear archivos de configuración de forma segura con backup automático
def safe_load_json(file_path, default_content):
    """Carga un archivo JSON o crea uno con contenido predeterminado si está vacío o corrupto"""
    try:
        from utils.safe_json_manager import SafeJSONManager
        
        # Usar SafeJSONManager para protección automática contra corrupción
        manager = SafeJSONManager(file_path, default_content)
        data = manager.load_or_create()
        
        # Verificar si es el formato de configuración completa (como el que tienes)
        if "paths" in data:
            logger.warning("Formato de configuración completo detectado. Extrayendo datos esenciales.")
            # Extraer solo los campos esenciales que necesitamos
            essential_data = {
                "hardware_type": data.get("hardware_type", "cpu"),
                "user_name": data.get("user_name", "Usuario"),
                "user_avatar": "default_avatar.png"
            }
            # Guardar el formato simplificado usando SafeJSONManager
            manager.save(essential_data)
            return essential_data
        
        return data
        
    except Exception as e:
        logger.error(f"Error con SafeJSONManager para {file_path}: {str(e)}. Usando fallback.")
        # Fallback al método original si SafeJSONManager falla
        try:
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            logger.warning(f"No se pudo cargar fallback para {file_path}: {e}")
        
        # Crear archivo por defecto
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_content, f, ensure_ascii=False, indent=4)
        except IOError as e:
            logger.error(f"No se pudo crear archivo por defecto {file_path}: {e}")
        
        return default_content

# Crear/cargar configuración básica
default_install_config = {
    "hardware_type": "cpu",
    "user_name": "Usuario",
    "user_avatar": "default_avatar.png"
}

default_knowledge = {
    "general": {
        "saludos": ["Hola", "Buenos días", "¿Cómo estás?"],
        "despedidas": ["Adiós", "Hasta luego", "Nos vemos"]
    }
}

# Cargar los archivos de configuración de forma segura
install_config = safe_load_json(install_config_path, default_install_config)
knowledge_base = safe_load_json(knowledge_path, default_knowledge)

# -----------------------------------------------------------------------------
# INICIALIZACIÓN DE LA APLICACIÓN QT - CORRECCIÓN DPI
# -----------------------------------------------------------------------------

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

# SOLUCIÓN DEFINITIVA: Configuración Qt para eliminar errores de QPainter completamente
# Configurar política DPI ANTES de crear QApplication
try:
    if hasattr(QApplication, 'setHighDpiScaleFactorRoundingPolicy'):
        from PySide6.QtCore import Qt
        if hasattr(Qt, 'HighDpiScaleFactorRoundingPolicy'):
            QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
            logger.info("Política de escalado DPI configurada ANTES de crear QApplication")
except Exception as e:
    logger.warning(f"No se pudo configurar política DPI: {str(e)}")

# Configurar atributos Qt ANTES de crear la aplicación
QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, False)  # Desactivar completamente
QApplication.setAttribute(Qt.AA_UseDesktopOpenGL, False)  # Sin OpenGL de escritorio
QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)  # Forzar software rendering
QApplication.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings, True)  # Evitar widgets nativos

# Crear la aplicación con configuración completa
app = QApplication(sys.argv)

# Mostrar splash screen inmediatamente
from ui.splash_screen import create_splash_screen
splash = create_splash_screen()
splash.show_with_fade()
splash.update_progress(10, "Inicializando aplicación")

# -----------------------------------------------------------------------------
# CLASE PRINCIPAL DEL ASISTENTE
# -----------------------------------------------------------------------------

class EVAAssistant:
    def __init__(self, app, splash_screen=None):
        try:
            logger.info("Inicializando PySide6...")
            self.application = app
            self.application.setQuitOnLastWindowClosed(False)
            self.splash = splash_screen
            
            # Cargar configuración principal (unified ConfigManager)
            if self.splash:
                self.splash.update_progress(20, self.splash.messages.get("loading_config", "Cargando configuración"))
            config_manager.reload()
            self.config = config_manager._data  # Backward compat: mismo dict reference
            
            # Migración one-shot de configs antiguas
            config_manager.migrate_old_configs()
            
            # Initialize unified language system
            if self.splash:
                self.splash.update_progress(25, self.splash.messages.get("init_language", "Inicializando sistema de idiomas"))
            
            from core.unified_language_manager import unified_language_manager
            self.language_manager = unified_language_manager
            logger.info("Language manager initialized successfully")
            
            # Set language from config with validation
            config_lang = self.config.get("language", "es")
            if self.language_manager.is_valid_language(config_lang):
                self.language_manager.current_lang = config_lang
            
            final_language = self.language_manager.current_lang
            self.config["language"] = final_language
            logger.info(f"EVA initialized with language: {final_language}")
            
            # Usar configuración de instalación cargada de forma segura
            self.install_config = install_config
            
            # Sistema simplificado - detección automática únicamente
            from utils.hardware import get_ollama_system_info
            
            # Detectar hardware para información únicamente (no configuración)
            logger.info("🔍 Detectando capacidades del sistema...")
            system_info = get_ollama_system_info()
            
            if system_info["gpu_available"]:
                acceleration = system_info.get('ollama_acceleration', 'Aceleración por hardware no disponible')
                logger.info(f"✅ {acceleration}")
                logger.info("🎯 TTS: Piper (CPU optimizado)")
                os.environ["EVA_HARDWARE_MODE"] = "hybrid"  # GPU para Ollama, CPU para TTS
            else:
                logger.info("ℹ️ Sistema CPU - Ollama y Piper funcionarán correctamente")
                logger.info("🎯 TTS: Piper (CPU optimizado)")
                os.environ["EVA_HARDWARE_MODE"] = "cpu"
            
            logger.info(f"🚀 Sistema listo: {os.environ['EVA_HARDWARE_MODE']}")
            
            # Verificar licencia
            if self.splash:
                # (Verificacion de licencia eliminada - version libre)
                pass  # check_license() eliminado
            
            # Mini bar (creación diferida)
            self.mini_bar = None

            # Gestor de sesión
            if self.splash:
                self.splash.update_progress(35, self.splash.messages.get("setting_session", "Configurando sesión"))
            from core.session_manager import SessionManager
            self.session_manager = SessionManager(self.config)
            
            # Posponer la verificación de sesión hasta después de la inicialización
            self.session_expired = False
            logger.info("Verificación de sesión pospuesta hasta después de la inicialización")
            
            # Ventana de chat - Solo crear si NO es primera ejecución
            if self.splash:
                self.splash.update_progress(45, self.splash.messages.get("creating_ui", "Creando interfaz de usuario"))
            
            # Inicializar chat_window como None - se creará después del wizard si es necesario
            self.chat_window = None
            
            # Solo crear la ventana principal si NO es primera ejecución
            if not self._is_first_run():
                from ui.chat_window import ChatWindow
                self.chat_window = ChatWindow(
                    self.config, 
                    self.session_manager,
                    self.language_manager
                )
            
            # Procesador de comandos completo
            if self.splash:
                self.splash.update_progress(55, self.splash.messages.get("setting_processor", "Configurando procesador de comandos"))
            from commands.processor import CommandProcessor
            self.command_processor = CommandProcessor(
                self.config, 
                self.session_manager,
                self.language_manager
            )
            self.command_processor.eva = self
            
            # Solo configurar command_processor en chat_window si existe
            if self.chat_window:
                self.chat_window.command_processor = self.command_processor
                self.chat_window.controller.command_processor = self.command_processor
            
            # Configurar referencia EVA en ollama_integration para VRAM manager
            if hasattr(self.command_processor, 'ollama') and self.command_processor.ollama:
                self.command_processor.ollama.eva = self

            # OPTIMIZACIÓN: Carga paralela de gestores independientes
            if self.splash:
                self.splash.update_progress(58, self.splash.messages.get("setting_managers", "Configurando gestores en paralelo"))
            
            # Cargar gestores en paralelo para mayor velocidad
            self._load_managers_parallel()
            
            # OPTIMIZACIÓN: Carga paralela de sistemas de voz
            if self.splash:
                self.splash.update_progress(65, self.splash.messages.get("preparing_voice", "Iniciando sistemas de voz..."))

            # Carga de sistemas de voz en paralelo (descomentado tras instalar dependencias)
            # CARGA DIFERIDA DE VOZ: Solo si existe ventana
            if self.chat_window:
                self._load_voice_systems_parallel()
            if self.splash:
                self.splash.update_progress(85, self.splash.messages.get("setting_final", "Configurando componentes finales en paralelo"))
            
            # Cargar componentes finales en paralelo
            self._load_final_components_parallel()
            
            # Base de conocimiento simplificada (usando archivos JSON estándar)
            if self.splash:
                self.splash.update_progress(97, self.splash.messages.get("loading_knowledge", "Cargando base de conocimiento"))
            # Knowledge base now handled by unified language manager
            self.knowledge_base = knowledge_base  # From safe_load_json above
            

            
            # Sistema de manejo de errores simplificado
            if self.splash:
                self.splash.update_progress(99, self.splash.messages.get("setting_errors", "Configurando manejo de errores"))
            from utils.simple_error_handler import simple_error_handler
            simple_error_handler.eva = self
            self.error_handler = simple_error_handler
            
            # Gestor de recursos simplificado (no esencial)
            try:
                from core.simple_resource_manager import simple_resource_manager
                simple_resource_manager.eva = self
                simple_resource_manager.start()
                self.resource_manager = simple_resource_manager
            except Exception as e:
                logger.warning(f"SimpleResourceManager no disponible: {e}")
                self.resource_manager = None
            
            # Sistema de monitoreo automático de carpetas
            self._setup_folder_monitoring()
            
            # Conectar señal de terminación
            self.application.aboutToQuit.connect(self.cleanup)
            
            # Configurar limpieza de ollama_eva al cerrar
            if hasattr(self.command_processor, 'ollama') and self.command_processor.ollama:
                self.application.aboutToQuit.connect(self.command_processor.ollama.cleanup)
            

            
            # Finalización
            if self.splash:
                self.splash.update_progress(100, self.splash.messages.get("eva_ready", "¡EVA listo!"))
                # Verificar si es primera ejecución antes de mostrar la ventana principal
                from PySide6.QtCore import QTimer
                
                # Función para mostrar la interfaz principal
                def show_interface():
                    if self._is_first_run():
                        self._show_first_run_wizard()
                    else:
                        self._show_main_window()
                    
                    # Mostrar mensaje de sesión expirada si es necesario
                    if hasattr(self, 'session_expired') and self.session_expired:
                        pass  # show_timeout_message eliminado
                
                # Mostrar la interfaz
                show_interface()
                
                # Verificar sesión después de que la interfaz esté lista
                def check_session_after_init():
                    pass  # can_operate eliminado - siempre True
                    
                    
                
                # Verificar sesión después de 2 segundos
                QTimer.singleShot(2000, check_session_after_init)
            else:
                # Sin splash screen
                if self._is_first_run():
                    self._show_first_run_wizard()
                else:
                    # Solo mostrar si la ventana existe
                    if self.chat_window:
                        self.chat_window.show()
                    else:
                        self._show_main_window()
                
                # Mostrar mensaje de sesión expirada si es necesario
                if hasattr(self, 'session_expired') and self.session_expired:
                    pass  # show_timeout_message eliminado
            
            logger.info("Asistente EVA inicializado correctamente")
            
        except Exception as error:
            logger.error(f"ERROR CRÍTICO: {str(error)}")
            logger.error(traceback.format_exc())
            from utils.simple_error_handler import simple_error_handler
            simple_error_handler.handle_error(error, "Error en inicialización principal de EVAAssistant")
            sys.exit(1)

    def _load_managers_parallel(self):
        """Carga gestores independientes en paralelo (con fallback robusto)"""
        try:
            import concurrent.futures
            
            def load_calendar_manager():
                try:
                    from core.calendar_manager import CalendarManager
                    cm = CalendarManager(self.config, self.language_manager)
                    cm.eva = self
                    return cm
                except Exception as e:
                    logger.warning(f"CalendarManager no disponible: {e}")
                    return None
            
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            try:
                calendar_future = executor.submit(load_calendar_manager)
                try:
                    result = calendar_future.result(timeout=5)
                    if result:
                        self.calendar_manager = result
                        if (hasattr(self.command_processor, 'simple_cita_handler') and
                            hasattr(self.command_processor.simple_cita_handler, 'set_calendar_manager')):
                            self.command_processor.simple_cita_handler.set_calendar_manager(result)
                        logger.info("CalendarManager cargado")
                except concurrent.futures.TimeoutError:
                    logger.warning("Timeout cargando CalendarManager, ignorando")
            finally:
                # Cancel pending and shutdown without blocking main thread
                executor.shutdown(wait=False, cancel_futures=True)
        except Exception as e:
            logger.warning(f"Error en carga de gestores: {e}")
    
    def _load_managers_sequential(self):
        """Fallback: carga secuencial de gestores"""
        try:
            from core.calendar_manager import CalendarManager
            self.calendar_manager = CalendarManager(self.config, self.language_manager)
            self.calendar_manager.eva = self
            if (hasattr(self.command_processor, 'simple_cita_handler') and
                hasattr(self.command_processor.simple_cita_handler, 'set_calendar_manager')):
                self.command_processor.simple_cita_handler.set_calendar_manager(self.calendar_manager)
        except Exception as e:
            logger.warning(f"CalendarManager (secuencial) no disponible: {e}")
    
    def _load_voice_systems_parallel(self):
        """Carga sistemas de voz en paralelo (con try-except por componente)"""
        import concurrent.futures
        
        def load_voice_engine():
            try:
                from voice.recognition import VoiceEngine
                voice_config = self.config.copy()
                voice_config["language"] = self.language_manager.current_lang
                return VoiceEngine(voice_config, self.language_manager)
            except Exception as e:
                logger.error(f"Error cargando VoiceEngine: {e}")
                return None
        
        def load_speech_synthesizer():
            try:
                from voice.unified_piper_tts import UnifiedPiperTTS
                return UnifiedPiperTTS(self.config, language_manager=self.language_manager)
            except Exception as e:
                logger.error(f"Error cargando SpeechSynthesizer: {e}")
                return None
        
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        try:
            voice_future = executor.submit(load_voice_engine)
            speech_future = executor.submit(load_speech_synthesizer)
            
            voice_engine = voice_future.result(timeout=15)
            speech_synth = speech_future.result(timeout=15)
            
            if voice_engine:
                self.voice_engine = voice_engine
                self._setup_voice_polling()
                logger.info("VoiceEngine cargado")
            if speech_synth:
                self.speech_synthesizer = speech_synth
                self.speech = speech_synth
                self.speech_synthesizer.tts_started.connect(self.handle_tts_start)
                self.speech_synthesizer.tts_completed.connect(self.handle_tts_end)
                self.speech_active = False
                logger.info("SpeechSynthesizer cargado")
            
            self._voice_loaded = bool(voice_engine or speech_synth)
        except concurrent.futures.TimeoutError:
            logger.warning("Timeout cargando voz, fallback secuencial")
            self._load_voice_systems_sequential()
        except Exception as e:
            logger.error(f"Error cargando sistemas de voz: {e}")
            self._voice_loaded = False
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
    
    def _load_voice_systems_sequential(self):
        """Fallback: carga secuencial de sistemas de voz"""
        from voice.recognition import VoiceEngine
        from voice.unified_piper_tts import UnifiedPiperTTS
        
        voice_config = self.config.copy()
        voice_config["language"] = self.language_manager.current_lang
        self.voice_engine = VoiceEngine(voice_config, self.language_manager)
        self._setup_voice_polling()




        
        self.speech_synthesizer = UnifiedPiperTTS(self.config, language_manager=self.language_manager)
        self.speech = self.speech_synthesizer
        self.speech_synthesizer.tts_started.connect(self.handle_tts_start)
        self.speech_synthesizer.tts_completed.connect(self.handle_tts_end)
        self.speech_active = False
        
        # NOTA: No iniciar aqui - se inicia en _show_main_window()
        self._voice_loaded = True
    
    def _load_final_components_parallel(self):
        """Carga componentes finales en paralelo"""
        import concurrent.futures
        
        # INICIALIZAR TRAY ICON COMO NONE - SE CREARÁ DESPUÉS DE LA VENTANA PRINCIPAL
        self.tray_icon = None
        
        def load_hotkey_manager():
            from core.hotkey_manager import HotkeyManager
            hotkey_manager = HotkeyManager(self, self.config)
            hotkey_manager.start()
            return hotkey_manager
        
        def load_cache_and_managers():
            from utils.smart_cache import ollama_cache as unified_cache
            from core.update_manager import UpdateManager
            from core.backup_manager import BackupManager
            
            backup_manager = BackupManager(BASE_DIR)
            update_manager = UpdateManager(self.config, BASE_DIR)
            
            return unified_cache, backup_manager, update_manager
        
        # Cargar otros componentes en paralelo
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        try:
            hotkey_future = executor.submit(load_hotkey_manager)
            cache_future = executor.submit(load_cache_and_managers)
            
            try:
                # Obtener resultados
                self.hotkey_manager = hotkey_future.result(timeout=5)
                
                self.unified_cache, self.backup_manager, self.update_manager = cache_future.result(timeout=5)
                
                # Conectar señales del sistema de actualizaciones
                self.update_manager.update_available.connect(self.handle_update_available)
                self.update_manager.update_error.connect(self.handle_update_error)
                self.update_manager.check_completed.connect(self.handle_update_check_completed)
                self.update_manager.start_periodic_checks()
                
                logger.info("✅ Componentes finales cargados en paralelo exitosamente")
            except concurrent.futures.TimeoutError:
                logger.warning("⚠️ Timeout cargando componentes finales, usando carga secuencial")
                self._load_final_components_sequential()
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
    
    def _load_final_components_sequential(self):
        """Fallback: carga secuencial de componentes finales"""
        # Tray icon se creará después en _show_main_window()
        
        # Hotkey manager
        from core.hotkey_manager import HotkeyManager
        self.hotkey_manager = HotkeyManager(self, self.config)
        self.hotkey_manager.start()
        
        # Cache y managers
        from utils.smart_cache import ollama_cache as unified_cache
        from core.update_manager import UpdateManager
        from core.backup_manager import BackupManager
        
        self.unified_cache = unified_cache
        self.backup_manager = BackupManager(BASE_DIR)
        self.update_manager = UpdateManager(self.config, BASE_DIR)
        
        # Conectar señales
        self.update_manager.update_available.connect(self.handle_update_available)
        self.update_manager.update_error.connect(self.handle_update_error)
        self.update_manager.check_completed.connect(self.handle_update_check_completed)
        self.update_manager.start_periodic_checks()

    def _is_first_run(self):
        """
        Detecta si es la primera ejecución de EVA usando el sistema de configuración
        """
        try:
            from utils.first_run import is_first_run
            return is_first_run()
        except Exception as e:
            logger.error(f"Error detectando primera ejecución: {str(e)}")
            # En caso de error, asumir que NO es primera ejecución para evitar mostrar wizard innecesariamente
            return False

    def _show_first_run_wizard(self):
        """Muestra el wizard de primera ejecución"""
        try:
            logger.info("Primera ejecución detectada - mostrando wizard de configuración")
            
            # Ocultar splash screen primero
            if self.splash:
                self.splash.fade_out()
            
            # Importar el wizard de primera ejecución
            from first_run_wizard import run_first_run_wizard
            
            # Ejecutar el wizard
            wizard_completed = run_first_run_wizard()
            
            if wizard_completed:
                # Importar el gestor de configuración del wizard
                from utils.first_run import get_config as get_wizard_config
                
                # Obtener la configuración del wizard
                wizard_config = get_wizard_config()
                logger.info(f"Wizard completado con configuración: {wizard_config}")
                
                # Actualizar configuración con los valores del wizard
                self.config.update({
                    "hardware_type": wizard_config.get("hardware", "cpu"),
                    "default_model": wizard_config.get("model", "phi3:mini"),
                    "voice_type": wizard_config.get("voice", "piper-es"),
                    "language": wizard_config.get("language", "en"),
                    "first_run": False  # Marcar como no primera ejecución
                })
                
                # Actualizar el idioma si es necesario
                if hasattr(self, 'language_manager') and self.language_manager:
                    self.language_manager.current_lang = self.config["language"]
                
                # Guardar configuración actualizada
                self._save_config_after_wizard()
                
                # CRÍTICO: Marcar primera ejecución como completada
                from utils.first_run import mark_first_run_complete
                mark_first_run_complete()
                logger.info("✅ Primera ejecución marcada como completada")
                
                # Mostrar mensaje de bienvenida personalizado
                self._show_welcome_after_wizard()
            else:
                # Usuario canceló el wizard - usar configuración por defecto
                logger.info("Wizard cancelado - usando configuración por defecto")
                self.config["first_run"] = False
                self._save_config_after_wizard()
                
                # CRÍTICO: Marcar primera ejecución como completada incluso si se cancela
                from utils.first_run import mark_first_run_complete
                mark_first_run_complete()
                logger.info("✅ Primera ejecución marcada como completada (cancelado)")
            
            # Mostrar ventana principal después del wizard
            self._show_main_window()
            
        except Exception as e:
            logger.error(f"Error mostrando wizard de primera ejecución: {str(e)}")
            # Fallback: marcar como no primera ejecución y mostrar ventana principal
            self.config["first_run"] = False
            self._save_config_after_wizard()
            
            # CRÍTICO: Marcar primera ejecución como completada incluso en caso de error
            try:
                from utils.first_run import mark_first_run_complete
                mark_first_run_complete()
                logger.info("✅ Primera ejecución marcada como completada (error)")
            except Exception as mark_error:
                logger.error(f"Error marcando primera ejecución como completada: {str(mark_error)}")
            
            self._show_main_window()

    def _create_tray_icon(self):
        """Crear el icono de la bandeja del sistema"""
        try:
            if self.tray_icon is None and self.chat_window is not None:
                from ui.tray_icon import create_tray_icon
                self.tray_icon = create_tray_icon(self.application, self.chat_window, self.config, self.language_manager, eva=self)
                if self.tray_icon:
                    self.tray_icon.show()
                    logger.info("✅ Tray icon creado exitosamente")
                else:
                    logger.warning("⚠️ Tray icon no se pudo crear")
        except Exception as e:
            logger.error(f"Error creando tray icon: {str(e)}")
            self.tray_icon = None

    def _save_config_after_wizard(self):
        """Guarda la configuración después del wizard"""
        try:
            config_manager.save()
            logger.info("Configuración guardada después del wizard")
        except Exception as e:
            logger.error(f"Error guardando configuración después del wizard: {str(e)}")

    def _show_welcome_after_wizard(self):
        """Muestra mensaje de bienvenida personalizado después del wizard"""
        try:
            if hasattr(self, 'chat_window'):
                welcome_msg = self.language_manager.get_text(
                    "ui.wizard_welcome", 
                    "¡Bienvenido a EVA! 🎉\n\nTu asistente ha sido configurado correctamente y está listo para ayudarte.\n\n💡 Puedes cambiar estas configuraciones en cualquier momento desde el menú de configuración."
                )
                # Usar QTimer para asegurar que la ventana esté completamente cargada
                from PySide6.QtCore import QTimer
                QTimer.singleShot(1000, lambda: self.chat_window.add_message(welcome_msg, is_user=False))
        except Exception as e:
            logger.error(f"Error mostrando mensaje de bienvenida: {str(e)}")

    def _create_mini_bar(self):
        """Crea la barra mini (compacta) si no existe"""
        if self.mini_bar is not None:
            return
        try:
            from ui.mini_bar import MiniBar
            self.mini_bar = MiniBar(
                self.config,
                self.language_manager,
                chat_window=self.chat_window,
                command_processor=self.command_processor
            )
            logger.info("Mini bar creada")
        except Exception as e:
            logger.error(f"Error creando mini bar: {e}")
            self.mini_bar = None

    def _show_main_window(self):
        """Muestra la ventana principal y oculta el splash screen"""
        try:
            # Crear ventana principal si no existe (después del wizard)
            if self.chat_window is None:
                logger.info("Creando ventana principal después del wizard")
                from ui.chat_window import ChatWindow
                self.chat_window = ChatWindow(
                    self.config, 
                    self.session_manager,
                    self.language_manager
                )
                # Configurar command_processor
                if hasattr(self, 'command_processor'):
                    self.chat_window.command_processor = self.command_processor
                    self.chat_window.controller.command_processor = self.command_processor

            # Crear mini bar
            self._create_mini_bar()

            # Mostrar ventana principal
            if self.config.get("use_mini_mode", False) and self.mini_bar is not None:
                self.mini_bar.show()
                logger.info("Mostrando mini bar (modo compacto)")
            else:
                self.chat_window.show()

            # Crear tray icon ahora que la ventana principal existe
            self._create_tray_icon()

            # Ocultar splash screen con fade out
            if self.splash:
                self.splash.fade_out()

            logger.info("Transición de splash a ventana principal completada")

            # Auto-arrancar voz si estaba activa al cerrar
            if self.config.get("auto_listen", False):
                from PySide6.QtCore import QTimer
                QTimer.singleShot(500, self._auto_start_voice)

        except Exception as e:
            logger.error(f"Error en transición de splash: {str(e)}")
            # Fallback: crear y mostrar ventana directamente
            if self.chat_window is None:
                from ui.chat_window import ChatWindow
                self.chat_window = ChatWindow(
                    self.config, 
                    self.session_manager,
                    self.language_manager
                )
            self.chat_window.show()

            # Crear mini bar también en fallback
            self._create_mini_bar()

            # Crear tray icon también en el fallback
            self._create_tray_icon()

            if self.splash:
                self.splash.close()

    def _setup_folder_monitoring(self):
        """Configura el monitoreo automático de cambios de carpeta activa"""
        try:
            from PySide6.QtCore import QTimer
            from utils.file_utils import refresh_folder_cache

            # Variable para rastrear la última carpeta conocida
            self.last_known_folder = None

            # Contador para reducir logs
            self.folder_check_count = 0

            # Primer refresh inmediato (async) para calentar la caché.
            # Sin esto la primera lectura del timer siempre encuentra caché vacía.
            refresh_folder_cache(blocking=False)

            # Timer: cada 5s -> leer caché previa + lanzar refresh para el siguiente ciclo
            self.folder_monitor_timer = QTimer()
            self.folder_monitor_timer.timeout.connect(self._check_folder_changes)
            self.folder_monitor_timer.start(5000)

            logger.info("Sistema de monitoreo automático de carpetas iniciado (cada 5 segundos)")

        except Exception as e:
            logger.error(f"Error configurando monitoreo de carpetas: {str(e)}")

    def _check_folder_changes(self):
        """
        Arquitectura de dos fases:
          FASE 1 – Leer la caché que el ciclo ANTERIOR ya completó (instantáneo,
                   sin bloquear el hilo Qt).
          FASE 2 – Disparar el refresh para el SIGUIENTE ciclo (PowerShell async,
                   no bloquea nada; tarda ~400ms y termina mucho antes de los 5s).

        NUNCA llames a time.sleep() aquí: estamos en el hilo principal de Qt.
        """
        try:
            from utils.file_utils import get_working_folder, refresh_folder_cache
            import os

            # ── FASE 1: leer caché ya actualizada por el ciclo previo ──────────
            current_folder = get_working_folder()

            if current_folder and current_folder != self.last_known_folder:
                logger.info(f"🔄 Cambio de carpeta detectado: {self.last_known_folder} → {current_folder}")
                self.last_known_folder = current_folder
                if hasattr(self, 'command_processor') and self.command_processor:
                    self.command_processor.last_opened_folder = current_folder
                if hasattr(self, 'chat_window') and self.chat_window:
                    folder_name = os.path.basename(current_folder)
                    msg = self.language_manager.get_text("responses.working_folder_updated", 
                                                         default=f"📁 Working folder updated: {folder_name}",
                                                         folder=folder_name)
                    self.chat_window.add_message(msg, is_user=False)

            # ── FASE 2: lanzar refresh async para el SIGUIENTE ciclo ──────────
            # blocking=False → hilo daemon, regresa de inmediato, no bloquea Qt
            refresh_folder_cache(blocking=False)

        except Exception as e:
            logger.error(f"❌ Error en verificación de carpeta: {str(e)}")

    def _delayed_voice_initialization(self):
        """Inicializa los sistemas de voz DESPUÉS de mostrar la ventana principal"""
        try:
            logger.info("🔄 Iniciando carga diferida de sistemas de voz...")
            
            # Mostrar mensaje al usuario
            if hasattr(self, 'chat_window'):
                # Obtener idioma configurado
                current_lang = self.config.get('language', 'es')
                if current_lang == 'en':
                    voice_init_msg = "🔄 Initializing voice systems in background..."
                else:
                    voice_init_msg = "🔄 Inicializando sistemas de voz en segundo plano..."
                self.chat_window.add_message(voice_init_msg, is_user=False)
            
            # Cargar sistemas de voz de forma segura
            self._load_voice_systems_safe()
            
        except Exception as e:
            logger.error(f"❌ Error en inicialización diferida de voz: {str(e)}")
            if hasattr(self, 'chat_window'):
                # Obtener idioma configurado
                current_lang = self.config.get('language', 'es')
                if current_lang == 'en':
                    error_msg = f"❌ Error initializing voice systems: {str(e)}"
                else:
                    error_msg = f"❌ Error inicializando sistemas de voz: {str(e)}"
                self.chat_window.add_message(error_msg, is_user=False)

    def _load_voice_systems_safe(self):
        """Carga segura de sistemas de voz con manejo robusto de errores"""
        import threading
        
        def load_voice_thread():
            try:
                logger.info("🎤 Cargando motor de reconocimiento de voz...")
                
                # Cargar VoiceEngine con timeout
                voice_loaded = self._load_voice_engine_with_timeout()
                
                # Cargar Speech Synthesizer
                logger.info("🔊 Cargando sintetizador de voz...")
                speech_loaded = self._load_speech_synthesizer_safe()
                
                # Reportar resultados
                if voice_loaded and speech_loaded:
                    logger.info("✅ Sistemas de voz cargados exitosamente")
                    
                    # CRÍTICO: Iniciar el stream de captura del micrófono
                    try:
                        if hasattr(self, 'voice_engine') and self.voice_engine:
                            logger.info("🎤 Iniciando escucha del micrófono...")
#                             self.voice_engine.start()
#                             logger.info("✅ Motor de reconocimiento ACTIVO - escuchando micrófono")
                    except Exception as start_err:
                        logger.error(f"❌ Error iniciando motor de voz: {start_err}")
                    
                    if hasattr(self, 'chat_window'):
                        # Obtener idioma configurado
                        current_lang = self.config.get('language', 'es')
                        if current_lang == 'en':
                            voice_ready_msg = "✅ Voice systems activated correctly"
                        else:
                            voice_ready_msg = "✅ Sistemas de voz activados correctamente"
                        self.chat_window.add_message(voice_ready_msg, is_user=False)
                elif speech_loaded:
                    logger.warning("⚠️ Solo síntesis de voz disponible (reconocimiento deshabilitado)")
                    if hasattr(self, 'chat_window'):
                        # Obtener idioma configurado
                        current_lang = self.config.get('language', 'es')
                        if current_lang == 'en':
                            partial_msg = "⚠️ Only voice synthesis available"
                        else:
                            partial_msg = "⚠️ Solo síntesis de voz disponible"
                        self.chat_window.add_message(partial_msg, is_user=False)
                else:
                    logger.error("❌ No se pudieron cargar los sistemas de voz")
                    if hasattr(self, 'chat_window'):
                        # Obtener idioma configurado
                        current_lang = self.config.get('language', 'es')
                        if current_lang == 'en':
                            unavailable_msg = "❌ Voice systems not available"
                        else:
                            unavailable_msg = "❌ Sistemas de voz no disponibles"
                        self.chat_window.add_message(unavailable_msg, is_user=False)
                        
            except Exception as e:
                logger.error(f"❌ Error en hilo de carga de voz: {str(e)}")
                if hasattr(self, 'chat_window'):
                    self.chat_window.add_message(f"❌ Error cargando sistemas de voz: {str(e)}", is_user=False)
        
        # Ejecutar en hilo separado para no bloquear la UI
        voice_thread = threading.Thread(target=load_voice_thread, daemon=True, name="VoiceLoader")
        voice_thread.start()

    def _load_voice_engine_with_timeout(self):
        """Carga el motor de voz con timeout para evitar bloqueos"""
        import threading
        
        voice_loaded = [False]  # Lista para permitir modificación en el hilo
        
        def load_voice():
            try:
                from voice.recognition import VoiceEngine
                voice_config = self.config.copy()
                voice_config["language"] = self.language_manager.current_lang
                
                # Crear VoiceEngine (esto puede bloquearse en Model())
                self.voice_engine = VoiceEngine(voice_config, self.language_manager)
                
                self._setup_voice_polling()


                
                voice_loaded[0] = True
                logger.info("✅ Motor de reconocimiento cargado exitosamente")
                
            except Exception as e:
                logger.error(f"❌ Error cargando motor de voz: {str(e)}")
                voice_loaded[0] = False
        
        # Ejecutar con timeout
        voice_thread = threading.Thread(target=load_voice, daemon=True)
        voice_thread.start()
        voice_thread.join(timeout=10)  # Timeout de 10 segundos
        
        if voice_thread.is_alive():
            logger.error("❌ Timeout cargando motor de voz (>10s)")
            return False
        
        return voice_loaded[0]

    def _load_speech_synthesizer_safe(self):
        """Carga el sintetizador de voz de forma segura"""
        try:
            from voice.unified_piper_tts import UnifiedPiperTTS
            self.speech_synthesizer = UnifiedPiperTTS(self.config, language_manager=self.language_manager)
            self.speech = self.speech_synthesizer  # Compatibilidad
            
            # Configurar señales
            if hasattr(self.speech_synthesizer, 'tts_started'):
                self.speech_synthesizer.tts_started.connect(self.handle_tts_start)
            if hasattr(self.speech_synthesizer, 'tts_completed'):
                self.speech_synthesizer.tts_completed.connect(self.handle_tts_end)
            
            self.speech_active = False
            logger.info("✅ Sintetizador de voz cargado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando sintetizador: {str(e)}")
            return False

    def _delayed_voice_start(self):
        """Método legacy - redirige al nuevo sistema"""
        self._delayed_voice_initialization()



    def handle_update_available(self, update_info):
        """Maneja cuando hay una actualización disponible"""
        try:
            from ui.update_notification import UpdateNotificationDialog
            
            logger.info(f"Actualización disponible: v{update_info['version']}")
            
            # Crear y mostrar el diálogo de notificación
            dialog = UpdateNotificationDialog(update_info, self.chat_window)
            
            # Conectar señales del diálogo
            dialog.update_accepted.connect(self._handle_update_accepted)
            dialog.update_postponed.connect(self._handle_update_postponed)
            dialog.update_skipped.connect(self._handle_update_skipped)
            
            # Mostrar el diálogo
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Error mostrando notificación de actualización: {str(e)}")

    def _handle_update_accepted(self):
        """Maneja cuando el usuario acepta la actualización"""
        try:
            logger.info("Usuario aceptó la actualización - Abriendo Gumroad")
            
            # Crear backup antes de que el usuario descargue la actualización
            if hasattr(self, 'backup_manager'):
                current_version = self.update_manager.current_version
                backup_path = self.backup_manager.create_backup(current_version, "pre_update")
                
                if backup_path:
                    logger.info(f"Backup creado antes de actualización: {backup_path}")
                    
                    # Mostrar mensaje al usuario sobre el backup
                    if hasattr(self, 'chat_window'):
                        backup_msg = (f"✅ Backup de seguridad creado antes de la actualización.\n"
                                    f"📁 Ubicación: {backup_path}\n"
                                    f"💡 Recuerda cerrar EVA completamente antes de instalar la nueva versión.")
                        self.chat_window.add_message(backup_msg, is_user=False)
                else:
                    logger.warning("No se pudo crear backup antes de la actualización")
                    
        except Exception as e:
            logger.error(f"Error manejando aceptación de actualización: {str(e)}")

    def _handle_update_postponed(self, hours):
        """Maneja cuando el usuario pospone la actualización"""
        try:
            logger.info(f"Usuario pospuso actualización por {hours} horas")
            
            if hasattr(self, 'update_manager'):
                self.update_manager.remind_later(hours)
                
            # Mostrar mensaje de confirmación
            if hasattr(self, 'chat_window'):
                msg = f"⏰ Te recordaré sobre la actualización en {hours} horas."
                self.chat_window.add_message(msg, is_user=False)
                
        except Exception as e:
            logger.error(f"Error manejando posposición de actualización: {str(e)}")

    def _handle_update_skipped(self, version):
        """Maneja cuando el usuario omite una versión"""
        try:
            logger.info(f"Usuario omitió versión {version}")
            
            if hasattr(self, 'update_manager'):
                self.update_manager.skip_version(version)
                
            # Mostrar mensaje de confirmación
            if hasattr(self, 'chat_window'):
                msg = f"❌ Versión {version} omitida. No volverás a recibir notificaciones para esta versión."
                self.chat_window.add_message(msg, is_user=False)
                
        except Exception as e:
            logger.error(f"Error manejando omisión de actualización: {str(e)}")

    def handle_update_error(self, error_msg):
        """Maneja errores del sistema de actualizaciones"""
        try:
            logger.error(f"Error en sistema de actualizaciones: {error_msg}")
            
            # Solo mostrar errores críticos al usuario
            if "timeout" not in error_msg.lower() and "conexión" not in error_msg.lower():
                if hasattr(self, 'chat_window'):
                    msg = f"⚠️ Error verificando actualizaciones: {error_msg}"
                    self.chat_window.add_message(msg, is_user=False)
                    
        except Exception as e:
            logger.error(f"Error manejando error de actualización: {str(e)}")

    def handle_update_check_completed(self, update_found):
        """Maneja cuando se completa una verificación de actualizaciones"""
        try:
            if update_found:
                logger.info("Verificación de actualizaciones completada - Actualización encontrada")
            else:
                logger.info("Verificación de actualizaciones completada - Sin actualizaciones")
                
        except Exception as e:
            logger.error(f"Error manejando finalización de verificación: {str(e)}")

    def check_updates_manually(self):
        """Permite verificar actualizaciones manualmente (para comandos de voz)"""
        try:
            if hasattr(self, 'update_manager'):
                logger.info("Verificación manual de actualizaciones solicitada")
                self.update_manager.check_for_updates(silent=False)
                
                if hasattr(self, 'chat_window'):
                    msg = "🔍 Verificando actualizaciones..."
                    self.chat_window.add_message(msg, is_user=False)
            else:
                logger.warning("Sistema de actualizaciones no disponible")
                
        except Exception as e:
            logger.error(f"Error en verificación manual de actualizaciones: {str(e)}")

    def show_setup_wizard_manually(self):
        """Permite mostrar el wizard de configuración manualmente"""
        try:
            logger.info("Wizard de configuración solicitado manualmente")
            
            if hasattr(self, 'chat_window'):
                msg = "🔧 Abriendo wizard de configuración..."
                self.chat_window.add_message(msg, is_user=False)
            
            # Importar y crear el wizard cyberpunk completo
            from ui.first_run_dialog import NewFirstRunWizard
            wizard = NewFirstRunWizard(self.language_manager, parent=self.chat_window)
            
            # Configurar el wizard
            wizard.setWindowTitle("EVA - Reconfiguración")
            wizard.setModal(True)
            
            # Mostrar el wizard y esperar resultado
            result = wizard.exec()
            
            if result == wizard.Accepted:
                # Usuario completó el wizard - obtener configuración
                wizard_config = wizard.get_config()
                logger.info(f"Reconfiguración completada: {wizard_config}")
                
                # Actualizar configuración con los valores del wizard
                self.config.update({
                    "hardware_type": wizard_config.get("hardware", "cpu"),
                    "default_model": wizard_config.get("model", "phi3:mini"),
                    "voice_type": wizard_config.get("voice", "piper-es"),
                })
                
                # Guardar configuración actualizada
                self._save_config_after_wizard()
                
                # Mostrar mensaje de confirmación
                if hasattr(self, 'chat_window'):
                    success_msg = self.language_manager.get_text(
                        "ui.wizard_reconfigured", 
                        "✅ Configuración actualizada correctamente.\n\n💡 Los cambios se aplicarán en la próxima sesión de EVA."
                    )
                    self.chat_window.add_message(success_msg, is_user=False)
                    
            else:
                # Usuario canceló el wizard
                logger.info("Reconfiguración cancelada por el usuario")
                if hasattr(self, 'chat_window'):
                    cancel_msg = "❌ Configuración cancelada. Se mantiene la configuración actual."
                    self.chat_window.add_message(cancel_msg, is_user=False)
            
        except Exception as e:
            logger.error(f"Error mostrando wizard manual: {str(e)}")
            if hasattr(self, 'chat_window'):
                error_msg = f"❌ Error abriendo wizard de configuración: {str(e)}"
                self.chat_window.add_message(error_msg, is_user=False)

    def handle_tts_start(self):
        """Maneja el inicio de síntesis de voz - MANTIENE INDICADOR VISIBLE"""
        self.speech_active = True
        if hasattr(self, 'chat_window'):
            self.chat_window.update_voice_indicator(True)
            logger.debug("Indicador de voz activado - permanecerá visible mientras habla")
        
    def handle_tts_end(self):
        """Maneja el final de síntesis de voz - OCULTA INDICADOR Y PROGRAMA DESCARGA"""
        self.speech_active = False
        if hasattr(self, 'chat_window'):
            self.chat_window.update_voice_indicator(False)
            logger.debug("Indicador de voz desactivado - síntesis completada")
        


    def check_license(self):
        """Stub: siempre válido como PREMIUM (sistema de licencias eliminado)."""
        self.config["license_valid"] = True
        self.config["license_type"] = "PREMIUM"
        logger.info("Licencia: modo libre, siempre PREMIUM")

    def show_start_message(self, silent=True):
        try:
            if silent:
                user_name = self.chat_window.user_name
                welcome = self.language_manager.get_text("responses.welcome_message")
                self.chat_window.add_message(welcome.format(user=user_name), is_user=False)
        except Exception as error:
            logger.error(f"Error mostrando mensaje de inicio: {str(error)}")
    
    def show_timeout_message(self):
        """Stub: sin tiempo límite, no hace nada."""
        pass


    def _setup_voice_polling(self):
        """Configura el polling thread-safe para comandos de voz.
        Usa singleShot(0) para diferir el start hasta que el event loop este activo,
        evitando el problema de timers creados antes de app.exec()."""
        from PySide6.QtCore import QTimer
        if hasattr(self, '_voice_poll_timer') and self._voice_poll_timer:
            self._voice_poll_timer.stop()
        self._voice_poll_timer = QTimer()
        self._voice_poll_timer.timeout.connect(self._poll_voice_commands)
        # singleShot(0) garantiza que _start_poll_timer se llama en el primer
        # tick del event loop, aunque _setup_voice_polling se llame antes de exec()
        QTimer.singleShot(0, self._start_poll_timer)
        logger.info("✅ Voice polling timer registrado (arrancara con el event loop)")

    def _start_poll_timer(self):
        """Arranca el timer de polling - siempre se ejecuta dentro del event loop."""
        if hasattr(self, '_voice_poll_timer') and self._voice_poll_timer:
            self._voice_poll_timer.start(50)
            logger.info("✅ Voice polling timer ACTIVO (50ms)")

    def _poll_voice_commands(self):
        """Polling de comandos de voz - siempre corre en el main thread (Qt)."""
        try:
            if not hasattr(self, 'voice_engine') or not self.voice_engine:
                return
            if not hasattr(self.voice_engine, '_cmd_queue'):
                return
            while not self.voice_engine._cmd_queue.empty():
                text = self.voice_engine._cmd_queue.get_nowait()
                logger.info(f"[POLL] Comando recibido en main thread: {text}")
                self.handle_voice_command(text)
        except Exception as e:
            logger.error(f"Error en _poll_voice_commands: {e}")

    def handle_voice_command(self, text):
        """Maneja comando de voz - eco visual + procesa"""
        if self.chat_window is None:
            logger.warning(f'Comando de voz recibido pero chat_window no disponible: {text[:50]}...')
            return
        try:
            if not self.session_manager.can_operate():
                session_expired = self.language_manager.get_text("responses.session_expired")
                self.chat_window.add_message(session_expired, is_user=False)
                return

            # Eco visual: mostrar el texto reconocido en el chat ANTES de procesar
            # add_message ya es thread-safe (usa QTimer.singleShot si no es hilo principal)
            try:
                self.chat_window.add_message(text, is_user=True)
            except Exception as echo_err:
                logger.warning(f"Eco visual falló: {echo_err}")
                # Fallback directo
                try:
                    self.chat_window.chat_history.append(
                        f"<div style='margin-bottom: 10px;'><span style='color:#a7ffeb;'>Tu:</span> "
                        f"<span style='color:#e0f7fa;'>{text}</span></div>"
                    )
                except Exception:
                    pass

            # Tracking de actividad (legacy)
            if hasattr(self, 'intelligent_ollama_manager') and self.intelligent_ollama_manager:
                self.intelligent_ollama_manager.track_user_activity()
            if hasattr(self, 'vram_manager') and self.vram_manager:
                self.vram_manager.track_activity()

            from utils.command_utils import is_conversation_command
            if is_conversation_command(text):
                if hasattr(self, 'speech_synthesizer'):
                    logger.info("MODO CONVERSACION ACTIVADO - Usando Piper TTS para respuesta de Ollama")

            self.command_processor.process_command(text, self.chat_window)

        except Exception as error:
            logger.error(f"Error procesando comando de voz: {str(error)}", exc_info=True)
            

    def _auto_start_voice(self):
        """Arranca el motor de voz al inicio si auto_listen estaba activo.
        Nunca debe causar el cierre de la aplicación."""
        if not hasattr(self, 'voice_engine') or not self.voice_engine:
            self.config["auto_listen"] = False
            config_manager.save()
            self._sync_voice_ui()
            return
        try:
            logger.info("Auto-arrancando motor de voz (auto_listen=True)...")
            self.voice_engine.start()
            logger.info("Motor de reconocimiento ACTIVO")
        except Exception as e:
            logger.error(f"Error en auto-arranque de voz: {e}, desactivando auto_listen")
            self.config["auto_listen"] = False
            config_manager.save()
        self._sync_voice_ui()

    def _sync_voice_ui(self):
        if hasattr(self, 'chat_window') and self.chat_window:
            try:
                self.chat_window.sync_voice_button_state()
            except Exception as e:
                logger.error(f"Error sincronizando UI de voz: {e}")
        if hasattr(self, 'mini_bar') and self.mini_bar:
            try:
                self.mini_bar.sync_voice_state()
            except Exception as e:
                logger.error(f"Error sincronizando mini bar voice: {e}")

    def start_voice_engine(self):
        """Inicia el motor de voz de forma segura una vez que la ventana existe"""
        if hasattr(self, 'voice_engine') and self.voice_engine:
            logger.info("🎤 Iniciando escucha del micrófono...")
            self.voice_engine.start()
            logger.info("✅ Motor de reconocimiento ACTIVO")
    def cleanup(self):
        """Limpieza completa y ordenada de todos los recursos - Optimizada para Windows EXE"""
        import traceback as _tb
        import sys as _sys
        print(f"[DIAG_CLEANUP] cleanup() called from:\n{''.join(_tb.format_stack()[:-1])}", file=_sys.stderr, flush=True)
        if getattr(self, '_cleaning_up', False):
            return
        self._cleaning_up = True
        try:
            logger.info("🔄 Iniciando cierre rápido de EVA...")
            
            # Importar gestores de limpieza
            from core.thread_registry import get_thread_registry
            from core.windows_cleanup import get_cleanup_manager
            
            thread_registry = get_thread_registry()
            cleanup_manager = get_cleanup_manager()
            
            # 1. CANCELAR TIMERS Y OPERACIONES PENDIENTES INMEDIATAMENTE
            if hasattr(self, 'voice_engine') and self.voice_engine:
                self.voice_engine.should_stop = True  # Señal de parada inmediata
            
            # 2. DETENER COMPONENTES ESENCIALES
            components = [
                (getattr(self, 'update_manager', None), "UpdateManager"),
                (getattr(self, 'calendar_manager', None), "CalendarManager"),
            ]
            for component, name in components:
                if component:
                    try:
                        if hasattr(component, 'stop'):
                            component.stop()
                        elif hasattr(component, 'cleanup'):
                            component.cleanup()
                    except Exception as e:
                        logger.warning(f"Error deteniendo {name}: {str(e)}")
            
            logger.info("Gestores de VRAM: delegados a Ollama")
            
            # Cache ya detenido arriba con el sistema unificado
            
            # 4. LIMPIEZA RÁPIDA DE MEMORIA (SIN ESPERAS)

            
            # 5. DETENER MOTORES DE VOZ CON TIMEOUT MEJORADO
            if hasattr(self, 'voice_engine') and self.voice_engine:
                try:
                    self.voice_engine.stop()
                    # Timeout mejorado para hilos de voz
                    if hasattr(self.voice_engine, 'audio_thread') and self.voice_engine.audio_thread and self.voice_engine.audio_thread.is_alive():
                        self.voice_engine.audio_thread.join(timeout=2.0)
                        if self.voice_engine.audio_thread.is_alive():
                            logger.warning("⚠️ Audio thread no se cerró correctamente")
                    if hasattr(self.voice_engine, 'processing_thread') and self.voice_engine.processing_thread and self.voice_engine.processing_thread.is_alive():
                        self.voice_engine.processing_thread.join(timeout=2.0)
                        if self.voice_engine.processing_thread.is_alive():
                            logger.warning("⚠️ Processing thread no se cerró correctamente")
                except Exception as e:
                    logger.warning(f"Error deteniendo motor de voz: {str(e)}")
            logger.info("Motor de reconocimiento detenido")
                    
            if hasattr(self, 'speech_synthesizer') and self.speech_synthesizer:
                try:
                    self.speech_synthesizer.cleanup()
                    logger.info("Speech synthesizer resources released")
                except Exception as e:
                    logger.warning(f"Error limpiando speech synthesizer: {str(e)}")
            logger.info("Motor de voz detenido")
            
            # 6. DETENER MONITOREO DE CARPETAS
            if hasattr(self, 'folder_monitor_timer') and self.folder_monitor_timer:
                try:
                    self.folder_monitor_timer.stop()
                except Exception as e:
                    logger.warning(f"Error deteniendo monitor de carpetas: {str(e)}")
            logger.info("Monitoreo de carpetas detenido")
            
            # 6b. OCULTAR MINI BAR
            if hasattr(self, 'mini_bar') and self.mini_bar:
                try:
                    self.mini_bar.save_position()
                    self.mini_bar.hide()
                except Exception as e:
                    logger.warning(f"Error ocultando mini bar: {e}")

            # 7. DETENER HOTKEYS RÁPIDAMENTE
            if hasattr(self, 'hotkey_manager') and self.hotkey_manager:
                try:
                    self.hotkey_manager.stop()
                except Exception as e:
                    logger.warning(f"Error deteniendo hotkey manager: {str(e)}")
            logger.info("Gestor de hotkeys detenido")
            
            # 7. GUARDAR CONFIGURACIÓN RÁPIDAMENTE
            logger.info("Guardando configuración de ventana...")
            if hasattr(self, 'chat_window') and self.chat_window is not None:
                try:
                    self.chat_window.save_config()
                except Exception as e:
                    logger.warning(f"Error guardando configuración de ventana: {str(e)}")
            
            # 8. EJECUTAR LIMPIEZA DE HILOS REGISTRADOS
            logger.info("Ejecutando limpieza final de hilos...")
            thread_registry.shutdown_all(timeout=3.0, force_exit=getattr(sys, 'frozen', False))
            
            # 9. LIMPIEZA DE ARCHIVOS TEMPORALES Y RECURSOS WINDOWS
            logger.info("Ejecutando limpieza de archivos temporales...")
            cleanup_manager.full_cleanup()
            
            # 10. VERIFICACIÓN FINAL DE HILOS ACTIVOS
            import threading
            active_threads = [t for t in threading.enumerate() if t != threading.current_thread() and t.is_alive()]
            if active_threads:
                logger.warning(f"⚠️ Hilos aún activos: {[t.name for t in active_threads]}")
                
                # Para ejecutables, forzar cierre si hay hilos persistentes
                if getattr(sys, 'frozen', False) and len(active_threads) > 0:
                    logger.warning("🔥 Ejecutable detectado: forzando cierre de proceso...")
                    import os
                    os._exit(0)
            
            logger.info("✅ Limpieza completada")
            
        except Exception as e:
            logger.error(f"Error durante limpieza: {str(e)}")
            
            # Limpieza de emergencia para ejecutables
            if getattr(sys, 'frozen', False):
                try:
                    from core.windows_cleanup import get_cleanup_manager
                    get_cleanup_manager().emergency_cleanup()
                    import os
                    os._exit(1)
                except Exception:
                    import os
                    os._exit(1)
            
    def update_settings(self, config):
        self.config = config
        if hasattr(self, 'voice_engine'):
            self.voice_engine.update_config(config)
        if hasattr(self, 'speech_synthesizer'):
            self.speech_synthesizer.update_config(config)
        if hasattr(self, 'hotkey_manager'):
            self.hotkey_manager.update_config(config)
        logger.info("Configuración actualizada en tiempo real")

    def update_gpu_settings(self, config):
        # GPU settings method simplified - Ollama manages GPU automatically
        # Piper TTS always uses CPU, no manual GPU configuration needed
        logger.info("GPU configuration: Ollama auto-detection enabled, Piper TTS uses CPU")

    def run(self):
        try:
            # Heartbeat timer to confirm event loop is alive
            from PySide6.QtCore import QTimer

            self._heartbeat_count = 0

            def _heartbeat():
                self._heartbeat_count += 1
                logger.info(f"[HEARTBEAT] Qt event loop alive — tick #{self._heartbeat_count} ({self._heartbeat_count * 10}s)")

            self._heartbeat_timer = QTimer()
            self._heartbeat_timer.timeout.connect(_heartbeat)
            self._heartbeat_timer.start(10000)
            logger.info("[HEARTBEAT] Timer started (10s interval) — waiting for events...")

            # Log when the event loop finishes
            def _log_event_loop_stop():
                logger.warning(f"[EVENT_LOOP] app.exec() returned! Heartbeat ran {getattr(self, '_heartbeat_count', 0)} times.")
                import traceback as _tb
                _tb.print_stack()

            # Connect to aboutToQuit to log why we're quitting
            original_about_to_quit = self.application.aboutToQuit
            try:
                self.application.aboutToQuit.connect(_log_event_loop_stop)
            except Exception:
                pass

            import sys as _sys
            logger.info("Iniciando bucle principal de Qt...")
            print("[DIAG] BEFORE app.exec()", file=_sys.stderr, flush=True)
            QTimer.singleShot(2000, lambda: print("[DIAG] ALIVE at 2s", file=_sys.stderr, flush=True))
            QTimer.singleShot(4000, lambda: print("[DIAG] ALIVE at 4s", file=_sys.stderr, flush=True))
            QTimer.singleShot(6000, lambda: print("[DIAG] ALIVE at 6s", file=_sys.stderr, flush=True))
            QTimer.singleShot(10000, lambda: print("[DIAG] ALIVE at 10s", file=_sys.stderr, flush=True))
            exit_code = self.application.exec()
            print(f"[DIAG] AFTER app.exec(): returned {exit_code}", file=_sys.stderr, flush=True)
            logger.warning(f"[EVENT_LOOP] app.exec() returned with code {exit_code}")
            # Log stack trace of who called quit
            import traceback as _tb
            _tb.print_stack()
            sys.exit(exit_code)
        except Exception as error:
            logger.error(f"Error en ejecución principal: {str(error)}")
            logger.error(traceback.format_exc())
            self.cleanup()
            sys.exit(1)

# -----------------------------------------------------------------------------
# DETECCIÓN DE ALTO CONTRASTE (WINDOWS)
# -----------------------------------------------------------------------------

def _detect_high_contrast():
    """Detecta si Windows está en modo alto contraste y devuelve estilos QSS extra."""
    try:
        if os.name != 'nt':
            return ""
        import ctypes
        from ctypes import wintypes

        class HIGHCONTRASTW(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.UINT),
                        ("dwFlags", wintypes.DWORD),
                        ("lpszDefaultScheme", wintypes.LPWSTR)]

        SPI_GETHIGHCONTRAST = 0x0042
        HCF_HIGHCONTRASTON = 0x00000001

        hc = HIGHCONTRASTW()
        hc.cbSize = ctypes.sizeof(HIGHCONTRASTW)
        if ctypes.windll.user32.SystemParametersInfoW(SPI_GETHIGHCONTRAST,
                                                       ctypes.sizeof(HIGHCONTRASTW),
                                                       ctypes.byref(hc), 0):
            if hc.dwFlags & HCF_HIGHCONTRASTON:
                logger.info("Modo alto contraste ACTIVO en Windows")
                return """
                    /* HIGH CONTRAST OVERRIDES */
                    * { color: #ffffff !important; background-color: #000000 !important; }
                    QLineEdit, QTextEdit { border: 2px solid #ffffff !important;
                        background-color: #1a1a1a !important; color: #ffffff !important; }
                    QPushButton { border: 2px solid #ffffff !important;
                        background-color: #333333 !important; color: #ffffff !important; }
                    QPushButton:hover { background-color: #555555 !important; }
                    QPushButton:pressed { background-color: #777777 !important; }
                    QPushButton:checked { background-color: #0066cc !important; }
                    QComboBox { border: 2px solid #ffffff !important;
                        background-color: #1a1a1a !important; color: #ffffff !important; }
                    QTextBrowser { background-color: #000000 !important; color: #ffffff !important; }
                    QScrollBar::handle { background: #ffffff !important; }
                    QLabel { color: #ffffff !important; }
                    #titleBar, #statusBar { background-color: #000000 !important; }
                    #chatHistory { background-color: #0a0a0a !important; }
                    QGroupBox { border: 2px solid #ffffff !important; color: #ffffff !important; }
                    QCheckBox { color: #ffffff !important; }
                    QCheckBox::indicator { border: 2px solid #ffffff !important; }
                    QCheckBox::indicator:checked { background-color: #ffffff !important; }
                    QSlider::groove:horizontal { background: #333333 !important; }
                    QSlider::handle:horizontal { background: #ffffff !important; }
                    QTabBar::tab { border: 1px solid #ffffff !important; color: #ffffff !important; }
                    QTabBar::tab:selected { background-color: #333333 !important; }
                    QMenu { background-color: #000000 !important; border: 1px solid #ffffff !important; }
                    QMenu::item { color: #ffffff !important; }
                    QMenu::item:selected { background-color: #333333 !important; }
                    #miniBarContainer { background-color: #000000 !important;
                        border: 2px solid #ffffff !important; }
                    QToolTip { background-color: #000000 !important;
                        color: #ffffff !important; border: 1px solid #ffffff !important; }
                """
    except Exception as e:
        logger.debug(f"No se pudo detectar alto contraste: {e}")
    return ""


# -----------------------------------------------------------------------------
# PUNTO DE ENTRADA PRINCIPAL
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Inicializar COM antes de freeze_support (requerido para PyInstaller .exe)
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except ImportError:
        pass

    # Esencial para compatibilidad con PyInstaller en Windows
    multiprocessing.freeze_support()
    
    # REGISTRAR HANDLERS DE SISTEMA PARA EJECUTABLES
    import signal
    import atexit
    
    def signal_handler(signum, frame):
        """Handler para señales del sistema"""
        import sys as _sys
        print(f"[DIAG_SIGNAL] Signal {signum} received", file=_sys.stderr, flush=True)
        logger.info(f"📡 Señal del sistema recibida: {signum}")
        if 'assistant' in globals() and not getattr(assistant, '_cleaning_up', False):
            assistant.cleanup()
        # Si ya estábamos en cleanup o acabamos de hacerlo, salir directamente
        sys.exit(0)
    
    def emergency_exit():
        """Limpieza de emergencia al cerrar"""
        try:
            from core.thread_registry import get_thread_registry
            from core.windows_cleanup import get_cleanup_manager
            
            get_thread_registry().shutdown_all(timeout=1.0, force_exit=True)
            get_cleanup_manager().emergency_cleanup()
        except Exception:
            pass
        
        # Para ejecutables, forzar salida
        if getattr(sys, 'frozen', False):
            import os
            os._exit(0)
    
    # Registrar handlers
    atexit.register(emergency_exit)
    if sys.platform == 'win32':
        try:
            signal.signal(signal.SIGTERM, signal_handler)
            signal.signal(signal.SIGINT, signal_handler)
        except Exception as e:
            logger.warning(f"No se pudieron registrar signal handlers: {e}")
    
    # PROTECCIÓN CONTRA MÚLTIPLES INSTANCIAS
    import ctypes
    mutex_name = "Global\\EVA_Main_Application_Mutex"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()
    
    if last_error == 183:  # ERROR_ALREADY_EXISTS
        print("EVA ya se está ejecutando. Cerrando esta instancia...")
        ctypes.windll.user32.MessageBoxW(
            0,
            "EVA ya se está ejecutando.\n\nSolo se permite una instancia a la vez.",
            "EVA - Instancia duplicada",
            0x40  # MB_ICONINFORMATION
        )
        sys.exit(0)
    
    try:
        # Ocultar consola solo si es un ejecutable
        if sys.platform == 'win32' and getattr(sys, 'frozen', False):
            try:
                import ctypes
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
                logger.info("Consola ocultada")
            except Exception as e:
                logger.error(f"No se pudo ocultar consola: {str(e)}")

        logger.info("Iniciando EVA...")
        assistant = EVAAssistant(app, splash)
        logger.info("Asistente creado, iniciando ejecución...")
        
        # Cargar estilos DESPUÉS de crear la aplicación
        styles_path = dynamic_path_resolver.get_path('base', 'styles.qss')
        if os.path.exists(styles_path):
            try:
                with open(styles_path, "r", encoding='utf-8') as f:
                    base_styles = f.read()

                # Detectar modo de alto contraste en Windows y añadir overrides
                high_contrast_styles = _detect_high_contrast()
                if high_contrast_styles:
                    base_styles += "\n" + high_contrast_styles
                    logger.info("Modo alto contraste detectado - estilos adaptados")

                app.setStyleSheet(base_styles)
                logger.info("Estilos cargados correctamente")
            except Exception as e:
                logger.error(f"Error cargando estilos: {str(e)}")
        else:
            logger.error(f"Archivo de estilos no encontrado: {styles_path}")
            
        assistant.run()
        logger.info("Ejecución completada")

    except Exception as error:
        logger.error(f"ERROR NO MANEJADO: {str(error)}")
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        # Limpiar cualquier proceso hijo pendiente
        for process in multiprocessing.active_children():
            logger.warning(f"Terminando proceso hijo pendiente: {process.name}")
            process.terminate()
            process.join()