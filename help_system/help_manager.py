#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HelpManager - Controlador Principal del Sistema de Ayuda de EVA
==============================================================

Este módulo gestiona el sistema de ayuda interactivo de EVA, proporcionando
navegación por menús, búsqueda inteligente y soporte bilingüe.

Autor: EVA Team
Versión: 1.0
Fecha: 2025-01-15
"""

import json
import logging
from typing import Dict, Any
from pathlib import Path

from .help_navigator import HelpNavigator
from .help_search import HelpSearcher

logger = logging.getLogger("EVA")


class HelpManager:
    """
    Controlador principal del sistema de ayuda de EVA.
    
    Gestiona la carga del árbol de ayuda, navegación, búsqueda y
    respuestas contextuales en español e inglés.
    """
    
    def __init__(self, config_manager=None, language_manager=None):
        """
        Inicializa el gestor de ayuda.
        
        Args:
            config_manager: Gestor de configuración de EVA
            language_manager: Gestor de idiomas de EVA
        """
        self.config_manager = config_manager
        self.language_manager = language_manager
        self.help_tree = None
        self.current_language = "es"  # Idioma por defecto
        
        # Componentes del sistema
        self.navigator = None
        self.searcher = None
        
        # Estado de sesión por usuario
        self.user_sessions = {}  # {user_id: session_data}
        
        # Cargar árbol de ayuda
        self._load_help_tree()
        
        # Inicializar componentes
        self._initialize_components()
        
        logger.info("HelpManager inicializado correctamente")
    
    def _load_help_tree(self) -> bool:
        """
        Carga el árbol de ayuda desde el archivo JSON.
        
        Returns:
            bool: True si se cargó correctamente, False en caso contrario
        """
        try:
            # Buscar archivo de ayuda
            help_file_paths = [
                Path(__file__).parent / "data" / "help_tree.json",
                Path("help_system/data/help_tree.json"),
                Path("data/help_tree.json")
            ]
            
            help_file = None
            for path in help_file_paths:
                if path.exists():
                    help_file = path
                    break
            
            if not help_file:
                logger.error("No se encontró el archivo help_tree.json")
                return False
            
            # Cargar contenido
            with open(help_file, 'r', encoding='utf-8') as f:
                self.help_tree = json.load(f)
            
            logger.info(f"Árbol de ayuda cargado desde: {help_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error cargando árbol de ayuda: {e}")
            return False
    
    def _initialize_components(self):
        """Inicializa los componentes del sistema de ayuda."""
        if not self.help_tree:
            logger.error("No se puede inicializar componentes sin árbol de ayuda")
            return
        
        try:
            self.navigator = HelpNavigator(self.help_tree, self)
            self.searcher = HelpSearcher(self.help_tree, self)
            logger.info("Componentes del sistema de ayuda inicializados")
        except Exception as e:
            logger.error(f"Error inicializando componentes: {e}")
    
    def set_language(self, language: str):
        """
        Establece el idioma del sistema de ayuda.
        
        Args:
            language: Código de idioma ('es' o 'en')
        """
        if language in ['es', 'en']:
            self.current_language = language
            logger.info(f"Idioma del sistema de ayuda cambiado a: {language}")
        else:
            logger.warning(f"Idioma no soportado: {language}")
    
    def get_current_language(self) -> str:
        """
        Obtiene el idioma actual del sistema.
        
        Returns:
            str: Código de idioma actual
        """
        # Intentar obtener idioma del language_manager si está disponible
        if self.language_manager:
            try:
                return self.language_manager.current_language
            except Exception:
                pass
        
        return self.current_language
    
    def process_help_request(self, command: str, user_id: str = "default", chat_window=None) -> str:
        """
        Procesa una solicitud de ayuda del usuario.
        
        Args:
            command: Comando o consulta del usuario
            user_id: ID del usuario (para sesiones múltiples)
            chat_window: Ventana de chat para mostrar respuestas
            
        Returns:
            str: Respuesta del sistema de ayuda
        """
        if not self.help_tree or not self.navigator:
            return self._get_error_message("system_not_ready")
        
        try:
            # Actualizar idioma actual
            self.current_language = self.get_current_language()
            
            # Obtener o crear sesión del usuario
            if user_id not in self.user_sessions:
                self.user_sessions[user_id] = {
                    "current_node": "main",
                    "navigation_history": [],
                    "language": self.current_language
                }
            
            session = self.user_sessions[user_id]
            session["language"] = self.current_language
            
            # Procesar comando
            command_lower = command.lower().strip()
            
            # Comandos de navegación especiales
            if self._is_navigation_command(command_lower):
                return self._handle_navigation_command(command_lower, session, chat_window)
            
            # Comandos de búsqueda
            if self._is_search_command(command_lower):
                return self._handle_search_command(command, session, chat_window)
            
            # Selección numérica
            if command_lower.isdigit():
                return self._handle_numeric_selection(command_lower, session, chat_window)
            
            # Comando de ayuda inicial
            if self._is_help_activation(command_lower):
                return self._show_main_menu(session, chat_window)
            
            # Búsqueda libre
            return self._handle_free_search(command, session, chat_window)
            
        except Exception as e:
            logger.error(f"Error procesando solicitud de ayuda: {e}")
            return self._get_error_message("processing_error")
    
    def _is_navigation_command(self, command: str) -> bool:
        """Verifica si es un comando de navegación."""
        nav_commands = self.help_tree.get("navigation", {}).get("commands", {})
        
        for lang in ["es", "en"]:
            lang_commands = nav_commands.get(lang, {})
            for cmd_type, commands in lang_commands.items():
                if command in commands:
                    return True
        return False
    
    def _is_search_command(self, command: str) -> bool:
        """Verifica si es un comando de búsqueda."""
        search_keywords = ["buscar", "busca", "encontrar", "encuentra", "search", "find"]
        return any(keyword in command for keyword in search_keywords)
    
    def _is_help_activation(self, command: str) -> bool:
        """Verifica si es un comando de activación de ayuda."""
        help_keywords = ["ayuda", "manual", "help", "menu", "menú", "inicio", "home"]
        return any(command.startswith(keyword) for keyword in help_keywords)
    
    def _handle_navigation_command(self, command: str, session: Dict, chat_window) -> str:
        """Maneja comandos de navegación."""
        nav_commands = self.help_tree.get("navigation", {}).get("commands", {})
        
        # Determinar tipo de comando
        command_type = None
        for lang in ["es", "en"]:
            lang_commands = nav_commands.get(lang, {})
            for cmd_type, commands in lang_commands.items():
                if command in commands:
                    command_type = cmd_type
                    break
            if command_type:
                break
        
        if command_type == "back":
            return self.navigator.go_back(session, chat_window)
        elif command_type == "home":
            return self.navigator.go_home(session, chat_window)
        elif command_type == "exit":
            return self._handle_exit(session, chat_window)
        
        return self._get_error_message("unknown_command")
    
    def _handle_search_command(self, command: str, session: Dict, chat_window) -> str:
        """Maneja comandos de búsqueda."""
        # Extraer término de búsqueda
        search_terms = ["buscar", "busca", "encontrar", "encuentra", "search", "find"]
        search_term = command.lower()
        
        for term in search_terms:
            if term in search_term:
                search_term = search_term.replace(term, "").strip()
                break
        
        if not search_term:
            return self._get_message("search_help")
        
        return self.searcher.search(search_term, session, chat_window)
    
    def _handle_numeric_selection(self, selection: str, session: Dict, chat_window) -> str:
        """Maneja selección numérica de opciones."""
        return self.navigator.navigate_to_option(int(selection), session, chat_window)
    
    def _handle_free_search(self, query: str, session: Dict, chat_window) -> str:
        """Maneja búsqueda libre de texto."""
        return self.searcher.search(query, session, chat_window)
    
    def _show_main_menu(self, session: Dict, chat_window) -> str:
        """Muestra el menú principal."""
        session["current_node"] = "main"
        session["navigation_history"] = []
        return self.navigator.show_current_node(session, chat_window)
    
    def _handle_exit(self, session: Dict, chat_window) -> str:
        """Maneja comando de salida."""
        # Limpiar sesión
        session["current_node"] = "main"
        session["navigation_history"] = []
        
        return self._get_message("goodbye")
    
    def _get_message(self, key: str) -> str:
        """Obtiene un mensaje localizado."""
        messages = {
            "es": {
                "system_not_ready": "❌ Sistema de ayuda no disponible. Intenta más tarde.",
                "processing_error": "❌ Error procesando solicitud. Intenta de nuevo.",
                "unknown_command": "❓ Comando no reconocido. Escribe 'ayuda' para ver opciones.",
                "search_help": "🔍 Uso: 'buscar [término]' - Ejemplo: 'buscar archivos'",
                "goodbye": "👋 Saliendo del sistema de ayuda. ¡Hasta pronto!"
            },
            "en": {
                "system_not_ready": "❌ Help system not available. Try again later.",
                "processing_error": "❌ Error processing request. Please try again.",
                "unknown_command": "❓ Command not recognized. Type 'help' to see options.",
                "search_help": "🔍 Usage: 'search [term]' - Example: 'search files'",
                "goodbye": "👋 Exiting help system. See you soon!"
            }
        }
        
        lang_messages = messages.get(self.current_language, messages["es"])
        return lang_messages.get(key, f"Message not found: {key}")
    
    def _get_error_message(self, error_type: str) -> str:
        """Obtiene un mensaje de error localizado."""
        return self._get_message(error_type)
    
    def get_help_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del sistema de ayuda.
        
        Returns:
            Dict con estadísticas del sistema
        """
        if not self.help_tree:
            return {}
        
        def count_nodes(node):
            count = 1
            if "children" in node:
                for child in node["children"]:
                    count += count_nodes(child)
            return count
        
        stats = {
            "version": self.help_tree.get("metadata", {}).get("version", "unknown"),
            "total_nodes": count_nodes(self.help_tree.get("root", {})),
            "languages": self.help_tree.get("metadata", {}).get("languages", []),
            "active_sessions": len(self.user_sessions),
            "current_language": self.current_language
        }
        
        return stats
    
    def reset_user_session(self, user_id: str = "default"):
        """
        Reinicia la sesión de un usuario.
        
        Args:
            user_id: ID del usuario a reiniciar
        """
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
            logger.info(f"Sesión reiniciada para usuario: {user_id}")
    
    def is_available(self) -> bool:
        """
        Verifica si el sistema de ayuda está disponible.
        
        Returns:
            bool: True si está disponible, False en caso contrario
        """
        return (self.help_tree is not None and 
                self.navigator is not None and 
                self.searcher is not None)