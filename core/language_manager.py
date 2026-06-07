# language_manager.py — alias de unified_language_manager
# Mantiene compatibilidad con imports existentes sin duplicar código
from core.unified_language_manager import UnifiedLanguageManager as LanguageManager
from core.unified_language_manager import unified_language_manager

__all__ = ["LanguageManager", "unified_language_manager"]