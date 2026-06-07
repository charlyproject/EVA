"""
Sistema de validación robusto para configuraciones de EVA
Previene valores inválidos que pueden causar fallos del sistema
"""

import re
import logging
from typing import Any, Dict, List, Union
from urllib.parse import urlparse

logger = logging.getLogger("EVA")

class ConfigValidator:
    """Validador robusto para todas las configuraciones de EVA"""
    
    @staticmethod
    def validate_rgba_color(color: List[int], name: str) -> List[int]:
        """Valida color RGBA [R, G, B, A] con valores 0-255"""
        if not isinstance(color, list) or len(color) != 4:
            logger.warning(f"Color {name} inválido: debe ser lista de 4 valores")
            return [100, 200, 255, 180]  # Color por defecto
        
        validated = []
        for i, value in enumerate(color):
            if not isinstance(value, int) or value < 0 or value > 255:
                logger.warning(f"Color {name}[{i}] inválido: {value}, usando 180")
                validated.append(180)
            else:
                validated.append(value)
        
        return validated
    
    @staticmethod
    def validate_url(url: str, name: str) -> str:
        """Valida formato de URL"""
        if not isinstance(url, str):
            logger.warning(f"URL {name} debe ser string")
            return "http://localhost:11434"
        
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                raise ValueError("URL incompleta")
            return url
        except Exception:
            logger.warning(f"URL {name} inválida: {url}")
            return "http://localhost:11434"
    
    @staticmethod
    def validate_range(value: Union[int, float], min_val: Union[int, float], 
                      max_val: Union[int, float], default: Union[int, float], 
                      name: str) -> Union[int, float]:
        """Valida que un valor esté en un rango específico"""
        if not isinstance(value, (int, float)):
            logger.warning(f"{name} debe ser numérico, usando {default}")
            return default
        
        if value < min_val or value > max_val:
            logger.warning(f"{name} fuera de rango [{min_val}-{max_val}]: {value}, usando {default}")
            return default
        
        return value
    
    @staticmethod
    def validate_positive_int(value: Any, default: int, name: str) -> int:
        """Valida entero positivo"""
        if not isinstance(value, int) or value <= 0:
            logger.warning(f"{name} debe ser entero positivo: {value}, usando {default}")
            return default
        return value
    
    @staticmethod
    def validate_hotkey_format(hotkey: str, name: str) -> str:
        """Valida formato de hotkey (ej: ctrl+alt+e)"""
        if not isinstance(hotkey, str):
            logger.warning(f"Hotkey {name} debe ser string")
            return "ctrl+alt+e"
        
        # Patrón básico para hotkeys
        pattern = r'^(ctrl\+)?(alt\+)?(shift\+)?[a-z0-9]$'
        if not re.match(pattern, hotkey.lower()):
            logger.warning(f"Hotkey {name} formato inválido: {hotkey}")
            return "ctrl+alt+e"
        
        return hotkey.lower()
    
    @staticmethod
    def validate_file_path(path: str, name: str, must_exist: bool = False) -> str:
        """Valida ruta de archivo"""
        if not isinstance(path, str):
            logger.warning(f"Ruta {name} debe ser string")
            return ""
        
        if must_exist:
            import os
            if not os.path.exists(path):
                logger.warning(f"Ruta {name} no existe: {path}")
                return ""
        
        return path
    
    @staticmethod
    def validate_string_list(value: Any, valid_options: List[str], 
                           default: str, name: str) -> str:
        """Valida que un string esté en una lista de opciones válidas"""
        if not isinstance(value, str) or value not in valid_options:
            logger.warning(f"{name} inválido: {value}, opciones: {valid_options}")
            return default
        return value

def validate_full_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validación completa de toda la configuración
    Corrige valores inválidos en lugar de fallar
    """
    validator = ConfigValidator()

    # 1. Validaciones básicas existentes (mantener)
    config = _validate_basic_values(config, validator)

    # 2. Validaciones de colores RGBA
    config = _validate_colors(config, validator)

    # 3. Validaciones de configuración Ollama
    config = _validate_ollama_config(config, validator)

    # 4. Validaciones de configuración TTS
    config = _validate_tts_config(config, validator)

    # 5. Validaciones de memoria y rendimiento
    config = _validate_memory_config(config, validator)

    # 6. Validaciones de hotkeys
    config = _validate_hotkeys(config, validator)

    # 7. Validaciones de rutas
    config = _validate_paths(config, validator)

    # 8. Validaciones de plugins (Tavily, etc.)
    config = _validate_plugins_config(config, validator)

    return config

def _validate_basic_values(config: Dict[str, Any], validator: ConfigValidator) -> Dict[str, Any]:
    """Validaciones básicas (mantener las existentes)"""
    # Idioma
    config["language"] = validator.validate_string_list(
        config.get("language"), ["es", "en"], "es", "language"
    )
    
    # Tamaño de fuente
    config["font_size"] = validator.validate_range(
        config.get("font_size", 12), 8, 72, 12, "font_size"
    )
    
    # Sensibilidad
    config["sensitivity"] = validator.validate_range(
        config.get("sensitivity", 0.5), 0.0, 1.0, 0.5, "sensitivity"
    )
    
    return config

def _validate_colors(config: Dict[str, Any], validator: ConfigValidator) -> Dict[str, Any]:
    """Validar todos los colores RGBA"""
    if "colors" not in config:
        return config
    
    color_defaults = {
        "listening": [100, 255, 150, 220],
        "responding": [200, 100, 255, 220],
        "idle": [100, 200, 255, 180],
        "stealth": [80, 80, 80, 100],
        "alert": [255, 50, 50, 220],
        "conversation": [255, 150, 50, 220],
    }
    
    for color_name, default_color in color_defaults.items():
        if color_name in config["colors"]:
            config["colors"][color_name] = validator.validate_rgba_color(
                config["colors"][color_name], color_name
            )
        else:
            config["colors"][color_name] = default_color
    
    return config

def _validate_ollama_config(config: Dict[str, Any], validator: ConfigValidator) -> Dict[str, Any]:
    """Validar configuración de Ollama"""
    if "ollama" not in config:
        return config
    
    ollama = config["ollama"]
    
    # URL base
    ollama["base_url"] = validator.validate_url(
        ollama.get("base_url", "http://localhost:11434"), "ollama.base_url"
    )
    
    # Timeout
    ollama["timeout"] = validator.validate_range(
        ollama.get("timeout", 30), 5, 300, 30, "ollama.timeout"
    )
    
    # Modelo
    valid_models = ["phi3:mini", "llama2", "qwen3:4b", "codellama"]
    ollama["model"] = validator.validate_string_list(
        ollama.get("model", "phi3:mini"), valid_models, "phi3:mini", "ollama.model"
    )
    
    return config

def _validate_tts_config(config: Dict[str, Any], validator: ConfigValidator) -> Dict[str, Any]:
    """Validar configuración TTS"""
    if "tts" not in config:
        return config
    
    tts = config["tts"]
    
    # Volumen
    tts["volume"] = validator.validate_range(
        tts.get("volume", 0.8), 0.0, 1.0, 0.8, "tts.volume"
    )
    
    # Configuración MeloTTS
    if "melo_config" in tts:
        melo = tts["melo_config"]
        melo["speed"] = validator.validate_range(
            melo.get("speed", 1.0), 0.5, 2.0, 1.0, "tts.melo_config.speed"
        )
        melo["pitch"] = validator.validate_range(
            melo.get("pitch", 0.0), -1.0, 1.0, 0.0, "tts.melo_config.pitch"
        )
        melo["energy"] = validator.validate_range(
            melo.get("energy", 1.0), 0.5, 1.5, 1.0, "tts.melo_config.energy"
        )
    
    return config

def _validate_memory_config(config: Dict[str, Any], validator: ConfigValidator) -> Dict[str, Any]:
    """Validar configuración de memoria"""
    if "memory" not in config:
        return config
    
    memory = config["memory"]
    
    # Tiempo de descarga automática (5-60 minutos)
    memory["auto_unload_min"] = validator.validate_range(
        memory.get("auto_unload_min", 15), 5, 60, 15, "memory.auto_unload_min"
    )
    
    # Umbral de emergencia (100MB - 2GB)
    memory["emergency_threshold_mb"] = validator.validate_range(
        memory.get("emergency_threshold_mb", 500), 100, 2048, 500, "memory.emergency_threshold_mb"
    )
    
    # Intervalo de monitoreo (10-300 segundos)
    memory["monitoring_interval"] = validator.validate_range(
        memory.get("monitoring_interval", 30), 10, 300, 30, "memory.monitoring_interval"
    )
    
    # Umbral de advertencia VRAM (50-95%)
    memory["vram_warning_threshold"] = validator.validate_range(
        memory.get("vram_warning_threshold", 85), 50, 95, 85, "memory.vram_warning_threshold"
    )
    
    return config

def _validate_hotkeys(config: Dict[str, Any], validator: ConfigValidator) -> Dict[str, Any]:
    """Validar configuración de hotkeys"""
    if "paths" not in config or "hotkeys" not in config["paths"]:
        return config
    
    hotkeys = config["paths"]["hotkeys"]
    if not isinstance(hotkeys, list):
        logger.warning("Hotkeys debe ser una lista")
        config["paths"]["hotkeys"] = []
        return config
    
    validated_hotkeys = []
    for hotkey in hotkeys:
        if isinstance(hotkey, dict) and "key" in hotkey:
            hotkey["key"] = validator.validate_hotkey_format(
                hotkey["key"], f"hotkey.{hotkey.get('target', 'unknown')}"
            )
            validated_hotkeys.append(hotkey)
        else:
            logger.warning(f"Hotkey inválido ignorado: {hotkey}")
    
    config["paths"]["hotkeys"] = validated_hotkeys
    return config

def _validate_paths(config: Dict[str, Any], validator: ConfigValidator) -> Dict[str, Any]:
    """Validar rutas de archivos y programas"""
    if "paths" not in config:
        return config

    paths = config["paths"]

    # Validar URLs de sitios web
    if "websites" in paths and isinstance(paths["websites"], dict):
        for site, url in paths["websites"].items():
            paths["websites"][site] = validator.validate_url(url, f"websites.{site}")

    return config


def _validate_plugins_config(config: Dict[str, Any], validator: ConfigValidator) -> Dict[str, Any]:
    """Validar configuración de plugins (Tavily, etc.)"""
    if "plugins" not in config:
        config["plugins"] = {}

    plugins = config["plugins"]

    # Validar API key de Tavily
    if "tavily_api_key" in plugins:
        key = plugins["tavily_api_key"]
        if not isinstance(key, str):
            plugins["tavily_api_key"] = ""
            logger.warning("plugins.tavily_api_key debe ser string, se limpió")
        elif len(key) > 0 and len(key) < 20:
            logger.warning("plugins.tavily_api_key parece demasiado corta, se mantiene pero verifique")
    else:
        plugins["tavily_api_key"] = ""

    # Validar profundidad de búsqueda de Tavily
    valid_depths = ["basic", "advanced"]
    if "tavily_search_depth" in plugins:
        plugins["tavily_search_depth"] = validator.validate_string_list(
            plugins.get("tavily_search_depth"), valid_depths, "basic", "plugins.tavily_search_depth"
        )
    else:
        plugins["tavily_search_depth"] = "basic"

    # Validar máximo de resultados
    if "tavily_max_results" in plugins:
        plugins["tavily_max_results"] = validator.validate_range(
            plugins.get("tavily_max_results"), 1, 10, 3, "plugins.tavily_max_results"
        )
    else:
        plugins["tavily_max_results"] = 3

    return config