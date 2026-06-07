import json
import logging
import os
import sys

# Agregar el directorio padre al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger("EVA")

# Ruta única para toda la configuración
CONFIG_FILE = os.path.join("config", "paths.json")

# Configuración por defecto consolidada
DEFAULT_CONFIG = {
    "window_position": [100, 100],
    "window_size": [500, 400],
    "font_size": 14,
    "language": "es",
    "volume_threshold": 0.3,
    "inactivity_timeout": 30,
    # GPU configs removed - obsolete after Piper TTS migration
    "colors": {
        "listening": [100, 255, 150, 220],
        "responding": [200, 100, 255, 220],
        "idle": [100, 200, 255, 180],
        "stealth": [80, 80, 80, 100],
        "alert": [255, 50, 50, 220],
        "conversation": [255, 150, 50, 220],
    },
    "ollama": {
        "model": "qwen3:4b",
        "base_url": "http://localhost:11434",
        "timeout": 30,
    },
    "tts": {
        "fast_voice": "pyttsx3",
        "natural_voice": "coqui",
        # Legacy coqui_model removed - using Piper TTS
        "use_coqui": True,
        "cuda": True,
        "volume": 0.8,
        "voice_id": "Helena",
        "voice_model": "tts_models/es/mai/tacotron2-DDC",
        "enhanced_mode": True,  # NEW: Enable Coqui Enhanced features
        # Legacy MeloTTS configuration removed - using Piper TTS
        "melo_config": {
            "enabled": True,
            "speaker_id": 0,  # Spanish speaker
            "speed": 1.0,     # Speech speed (0.5-2.0)
            "pitch": 0.0,     # Pitch adjustment (-1.0 to 1.0)
            "energy": 1.0,    # Energy/volume (0.5-1.5)
            "emotion": "neutral",  # neutral, happy, sad, angry, surprised
            "sample_rate": 44100,  # High quality audio
            "optimize_memory": True,  # Memory optimization
            "streaming": False,  # Real-time streaming
            "noise_scale": 0.667,  # Voice naturalness
            "noise_scale_w": 0.8,  # Voice variation
            "length_scale": 1.0,   # Duration control
        }
    },
    "frases_transicion": ["Procesando...", "Un momento..."],
    "respuestas_error": ["No entendí el comando", "Intenta de nuevo"],
    "comandos_especiales": {},
    "variants": {},
    "license_key": "",
    "auto_start": False,
    "minimize_start": True,
    "auto_listen": True,
    "sensitivity": 0.5,
    "first_run": True,
    "confirm": ["apaga", "reinicia", "cierra sesión"],
    "updates": {
        "check_automatically": True,
        "check_interval_hours": 6,
        "notify_critical_only": False,
        "create_backups": True,
        "skipped_versions": [],
        "last_check": None,
        "remind_later_until": None
    },
    "gumroad": {
        "product_url": "https://gumroad.com/l/eva-assistant",
        "api_key": ""
    },
    "plugins": {
        "tavily_api_key": "",
        "tavily_search_depth": "basic",
        "tavily_max_results": 3
    },
    "memory": {
        "auto_unload_min": 15,           # Tiempo de inactividad para descarga automática
        "enable_auto_detect": True,      # Detección automática de apps
        "emergency_threshold_mb": 500,   # Umbral para descarga de emergencia
        "monitoring_interval": 30,       # Intervalo de monitoreo en segundos
        "vram_warning_threshold": 85     # % de VRAM para mostrar advertencia
    },
    "high_perf_apps": [
        "javaw.exe",           # Minecraft
        "davinci.exe",         # DaVinci Resolve
        "blender.exe",         # Blender
        "Unity.exe",           # Unity Editor
        "UnrealEditor.exe",    # Unreal Engine
        "obs64.exe",           # OBS Studio
        "chrome.exe",          # Chrome (puede usar GPU)
        "firefox.exe",         # Firefox
        "steam.exe",           # Steam
        "steamwebhelper.exe",  # Steam Web Helper
        "GameOverlayUI.exe",   # Steam Overlay
        "Discord.exe",         # Discord
        "Photoshop.exe",       # Adobe Photoshop
        "AfterFX.exe",         # After Effects
        "PremierePro.exe"      # Premiere Pro
    ],
    "tts_management": {
        "enabled": True,
        "preload_delay_seconds": 600,      # 10 minutes default
        "unload_delay_seconds": 900,       # 15 minutes default
        "cpu_idle_threshold": 10,          # 10% CPU threshold
        "ram_idle_threshold_mb": 50,       # 50MB RAM threshold
        "monitoring_interval_seconds": 30, # 30 seconds monitoring interval
    },
    "paths": {
        "programs": {},
        "folders": {},
        "websites": {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "twitch": "https://www.twitch.tv",
        },
        "hotkeys": [
            {"key": "ctrl+alt+e", "action_type": "basic", "target": "activar"},
            {"key": "ctrl+alt+c", "action_type": "basic", "target": "mostrar_chat"},
            {"key": "ctrl+alt+h", "action_type": "basic", "target": "ocultar_chat"},
            {"key": "ctrl+alt+q", "action_type": "basic", "target": "salir"},
            {"key": "ctrl+alt+v", "action_type": "vram", "target": "liberar_vram"},
            {"key": "ctrl+alt+p", "action_type": "vram", "target": "modo_rendimiento"},
        ],
    },
    "general_settings": "General Settings",
    "voice_settings": "Voice Settings",
    "hardware_settings": "Hardware Settings",
    "settings": "Settings",
    # 🧠 CONFIGURACIÓN VAD (Voice Activity Detection)
    "vad": {
        "enabled": True,                    # Activar filtro inteligente por defecto
        "mode": 2,                         # 0=Muy Conservador, 1=Conservador, 2=Equilibrado, 3=Sensible
        "description": {
            "0": "Muy Conservador - Solo voz muy clara (oficinas muy ruidosas)",
            "1": "Conservador - Voz normal, ignora susurros (oficinas ruidosas)", 
            "2": "Equilibrado - Recomendado para la mayoría de usuarios",
            "3": "Sensible - Detecta susurros (ambientes silenciosos)"
        }
    },
}


def load_configuration():
    """Carga toda la configuración usando SafeJSONManager con backup automático"""
    logger.info(f"Intentando cargar configuración desde: {CONFIG_FILE}")

    try:
        try:
            from utils.safe_json_manager import SafeJSONManager
        except ImportError:
            SafeJSONManager = None
        
        # Usar SafeJSONManager para protección automática contra corrupción
        manager = SafeJSONManager(CONFIG_FILE, DEFAULT_CONFIG)
        config = manager.load_or_create()
        
        logger.info("Configuración cargada exitosamente")

        # Validación y fusión con valores por defecto
        config = _merge_with_defaults(config, DEFAULT_CONFIG)
        
        # Validaciones específicas
        config = _validate_config_values(config)
        
        # Expansión de variables de entorno en rutas
        config = _expand_environment_variables(config)

        return config
    
    except Exception as e:
        logger.error(f"Error cargando configuración con SafeJSONManager: {str(e)}. Usando fallback.")
        # Fallback al método original
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            if os.path.exists(CONFIG_FILE) and os.path.getsize(CONFIG_FILE) > 0:
                with open(CONFIG_FILE, "r", encoding="utf-8") as file:
                    config = json.load(file)
                    return _validate_config_values(_merge_with_defaults(config, DEFAULT_CONFIG))
        except Exception:
            pass
        
        return DEFAULT_CONFIG.copy()


def _merge_with_defaults(config, defaults):
    """Fusiona configuración cargada con valores por defecto recursivamente"""
    for key, value in defaults.items():
        if key not in config:
            config[key] = value
        elif isinstance(value, dict) and isinstance(config.get(key), dict):
            config[key] = _merge_with_defaults(config[key], value)
    return config


def _validate_config_values(config):
    """Valida y corrige valores de configuración usando el sistema robusto"""
    try:
        # Usar el nuevo sistema de validación robusto
        from config.config_validator import validate_full_config
        return validate_full_config(config)
    except ImportError:
        logger.warning("Sistema de validación robusto no disponible, usando validación básica")
        return _validate_config_values_basic(config)

def _validate_config_values_basic(config):
    """Validación básica como fallback (mantener compatibilidad)"""
    # Validar idioma
    if not isinstance(config.get("language", ""), str) or config["language"] not in ["es", "en"]:
        config["language"] = "es"
        logger.warning("Idioma inválido, usando 'es' por defecto")

    # Validar tamaño de fuente
    font_size = config.get("font_size", 12)
    if not isinstance(font_size, int) or font_size < 8 or font_size > 72:
        config["font_size"] = 12
        logger.warning("Tamaño de fuente inválido, usando 12 por defecto")

    # Validar sensibilidad
    sensitivity = config.get("sensitivity", 0.5)
    if not isinstance(sensitivity, (int, float)) or sensitivity < 0 or sensitivity > 1:
        config["sensitivity"] = 0.5
        logger.warning("Sensibilidad inválida, usando 0.5 por defecto")

    # Validar volumen
    if "tts" in config and "volume" in config["tts"]:
        volume = config["tts"]["volume"]
        if not isinstance(volume, (int, float)) or volume < 0 or volume > 1:
            config["tts"]["volume"] = 0.8
            logger.warning("Volumen TTS inválido, usando 0.8 por defecto")

    return config


def _expand_environment_variables(config):
    """Expande variables de entorno en rutas de configuración"""
    if "paths" in config:
        for category, paths in config["paths"].items():
            if isinstance(paths, dict):
                for key, path in paths.items():
                    if isinstance(path, str):
                        config["paths"][category][key] = os.path.expandvars(os.path.expanduser(path))
            elif isinstance(paths, str):
                config["paths"][category] = os.path.expandvars(os.path.expanduser(paths))
    return config


def save_configuration(config):
    """Guarda toda la configuración usando SafeJSONManager con backup automático"""
    try:
        try:
            from utils.safe_json_manager import SafeJSONManager
        except ImportError:
            SafeJSONManager = None
        
        config_to_save = config.copy()

        if "hardware_info" in config_to_save:
            del config_to_save["hardware_info"]

        # Usar SafeJSONManager para guardado seguro con backup automático
        manager = SafeJSONManager(CONFIG_FILE, DEFAULT_CONFIG)
        manager.save(config_to_save)

        logger.info(f"Configuración guardada en: {CONFIG_FILE}")
        
    except Exception as e:
        logger.error(f"Error guardando configuración con SafeJSONManager: {str(e)}. Usando fallback.")
        # Fallback al método original
        try:
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as file:
                json.dump(config_to_save, file, indent=2, ensure_ascii=False)
            logger.info(f"Configuración guardada (fallback) en: {CONFIG_FILE}")
        except Exception as fallback_error:
            logger.error(f"Error en fallback de guardado: {str(fallback_error)}")
