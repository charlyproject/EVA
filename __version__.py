"""
Enhanced Voice Assistant v.1.0 - Información de Versión
Sistema optimizado con gestión unificada de memoria y manejo centralizado de errores
"""

__version__ = "1.0.0"
__title__ = "Enhanced Voice Assistant"
__description__ = "Sistema de asistente de voz mejorado con IA integrada"
__author__ = "EVA Development Team"
__license__ = "MIT"

# Información de build
BUILD_INFO = {
    "version": __version__,
    "title": __title__,
    "description": __description__,
    "features": [
        "Gestión unificada de memoria",
        "Manejo centralizado de errores", 
        "Sistema unificado Piper TTS",
        "Integración mejorada con Ollama",
        "Sistema de limpieza inteligente"
    ],
    "optimizations": [
        "Reducción de uso de CPU en limpieza de memoria",
        "Carga simplificada de modelos TTS",
        "Manejo robusto de errores GPU/CUDA",
        "Limpieza automática de recursos"
    ]
}

def get_version_string():
    """Retorna string de versión completo"""
    return f"{__title__} v.{__version__}"

def get_build_info():
    """Retorna información completa de build"""
    return BUILD_INFO.copy()