"""
Unified Language Manager for EVA
Centralizes all language detection, validation, and management functionality
"""

import json
import logging
import os
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger("EVA")

class UnifiedLanguageManager(QObject):
    """Centralized language management for EVA"""
    
    # Signal emitted when language changes
    language_changed = Signal(str)
    
    SUPPORTED_LANGUAGES = ["es", "en"]
    DEFAULT_LANGUAGE = "es"
    
    def __init__(self, config_path: str = "config"):
        super().__init__()
        self.config_path = config_path
        self._current_lang = self.DEFAULT_LANGUAGE
        self._translations = {}
        self._load_translations()
        
    @property
    def current_lang(self) -> str:
        """Get current language with validation"""
        if self._current_lang in self.SUPPORTED_LANGUAGES:
            return self._current_lang
        logger.warning(f"Invalid language {self._current_lang}, using default")
        return self.DEFAULT_LANGUAGE
    
    @current_lang.setter
    def current_lang(self, lang: str):
        """Set current language with validation"""
        if isinstance(lang, str) and lang in self.SUPPORTED_LANGUAGES:
            old_lang = self._current_lang
            self._current_lang = lang
            logger.info(f"Language changed to: {lang}")
            # Emit signal if language actually changed
            if old_lang != lang:
                self.language_changed.emit(lang)
        else:
            logger.warning(f"Invalid language '{lang}', keeping current: {self._current_lang}")
    
    def set_language(self, lang: str):
        """Set language method for compatibility with existing code"""
        self.current_lang = lang
    
    def _load_translations(self):
        """Load translation files"""
        for lang in self.SUPPORTED_LANGUAGES:
            try:
                lang_file = os.path.join(self.config_path, f"lang_{lang}.json")
                if os.path.exists(lang_file):
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self._translations[lang] = json.load(f)
                    logger.info(f"Loaded translations for {lang}")
                else:
                    logger.warning(f"Translation file not found: {lang_file}")
                    self._translations[lang] = {}
            except Exception as e:
                logger.error(f"Error loading translations for {lang}: {str(e)}")
                self._translations[lang] = {}
    
    def get_text(self, key: str, default: str = None, **kwargs) -> str:
        """
        Get translated text with fallback
        VERSIÓN ROBUSTA: Acepta parámetro default para compatibilidad con llamadas antiguas
        """
        try:
            # Navigate nested keys (e.g., "responses.welcome_message")
            keys = key.split('.')
            text = self._translations.get(self.current_lang, {})
            
            for k in keys:
                if isinstance(text, dict) and k in text:
                    text = text[k]
                else:
                    # Fallback to default language
                    text = self._translations.get(self.DEFAULT_LANGUAGE, {})
                    for k in keys:
                        if isinstance(text, dict) and k in text:
                            text = text[k]
                        else:
                            # Usar default si se proporciona, sino formato de error
                            return default if default is not None else f"[Missing: {key}]"
                    break
            
            # Format with provided kwargs
            if isinstance(text, str) and kwargs:
                return text.format(**kwargs)
            
            result = str(text) if text else (default if default is not None else f"[Missing: {key}]")
            return result
            
        except Exception as e:
            logger.error(f"Error getting text for key '{key}': {str(e)}")
            return default if default is not None else f"[Error: {key}]"
    
    def detect_language_from_text(self, text: str) -> str:
        """Simple language detection based on common words"""
        if not text:
            return self.current_lang
            
        text_lower = text.lower()
        
        # Spanish indicators
        spanish_words = ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'una', 'tiene', 'más', 'este', 'está', 'como', 'pero', 'sus', 'muy', 'todo', 'hacer', 'puede', 'tiempo', 'año', 'años', 'dos', 'vida', 'trabajo', 'casa', 'día', 'parte', 'mundo', 'país', 'forma', 'estado', 'lugar', 'grupo', 'manera', 'caso', 'gobierno', 'empresa', 'servicio', 'hombre', 'mujer', 'agua', 'historia', 'desarrollo', 'proceso', 'resultado', 'momento', 'derecho', 'sistema', 'programa', 'problema', 'pregunta', 'información', 'número', 'punto', 'proyecto', 'mes', 'millones', 'durante', 'siempre', 'embargo', 'ejemplo', 'tipo', 'nivel', 'valor', 'precio', 'hora', 'cuenta', 'nombre', 'razón', 'situación', 'producto', 'actividad', 'medida', 'condición', 'campo', 'cuerpo', 'libro', 'reportar', 'sistema', 'programa', 'cuestión', 'lugar', 'caso', 'parte', 'grupo', 'problema', 'mano', 'área', 'hecho', 'forma', 'manera', 'tipo', 'medio', 'millón', 'gracias', 'favor', 'ayuda', 'bien', 'mal', 'mejor', 'peor', 'grande', 'pequeño', 'nuevo', 'viejo', 'bueno', 'malo', 'primero', 'último', 'mismo', 'otro', 'cada', 'algún', 'mucho', 'poco', 'todo', 'nada', 'algo', 'alguien', 'nadie', 'donde', 'cuando', 'como', 'porque', 'aunque', 'mientras', 'hasta', 'desde', 'hacia', 'según', 'entre', 'sobre', 'bajo', 'ante', 'tras', 'durante', 'mediante', 'excepto', 'salvo', 'incluso', 'además', 'también', 'tampoco', 'sino', 'pero', 'aunque', 'si', 'cuando', 'donde', 'como', 'que', 'quien', 'cual', 'cuyo', 'cuanto']
        
        # English indicators  
        english_words = ['the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'she', 'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us', 'is', 'water', 'long', 'find', 'here', 'thing', 'great', 'man', 'world', 'life', 'still', 'public', 'human', 'get', 'own', 'say', 'her', 'old', 'see', 'him', 'two', 'more', 'go', 'no', 'way', 'could', 'my', 'than', 'first', 'been', 'call', 'who', 'oil', 'sit', 'now', 'find', 'long', 'down', 'day', 'did', 'get', 'come', 'made', 'may', 'part']
        
        spanish_count = sum(1 for word in spanish_words if word in text_lower)
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if spanish_count > english_count:
            return "es"
        elif english_count > spanish_count:
            return "en"
        else:
            return self.current_lang  # Default to current if unclear
    
    def is_valid_language(self, lang: str) -> bool:
        """Check if language is supported"""
        return isinstance(lang, str) and lang in self.SUPPORTED_LANGUAGES
    
    def get_available_languages(self) -> list:
        """Get list of available languages"""
        return self.SUPPORTED_LANGUAGES.copy()
    
    def reload_translations(self):
        """Reload translation files"""
        self._load_translations()
        logger.info("Translations reloaded")

# Global instance
unified_language_manager = UnifiedLanguageManager()