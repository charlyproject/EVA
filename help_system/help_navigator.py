#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HelpNavigator - Sistema de Navegación por Menús de Ayuda
========================================================

Este módulo maneja la navegación por el árbol de ayuda de EVA,
proporcionando una interfaz intuitiva con menús numerados y
navegación contextual.

Autor: EVA Team
Versión: 1.0
Fecha: 2025-01-15
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger("EVA")


class HelpNavigator:
    """
    Navegador del sistema de ayuda de EVA.
    
    Maneja la navegación por el árbol de ayuda, mostrando menús
    contextuales y gestionando el historial de navegación.
    """
    
    def __init__(self, help_tree: Dict, help_manager):
        """
        Inicializa el navegador de ayuda.
        
        Args:
            help_tree: Árbol de ayuda cargado desde JSON
            help_manager: Referencia al HelpManager principal
        """
        self.help_tree = help_tree
        self.help_manager = help_manager
        
        logger.info("HelpNavigator inicializado correctamente")
    
    def show_current_node(self, session: Dict, chat_window=None) -> str:
        """
        Muestra el nodo actual del árbol de ayuda.
        
        Args:
            session: Datos de sesión del usuario
            chat_window: Ventana de chat para mostrar respuesta
            
        Returns:
            str: Contenido formateado del nodo actual
        """
        try:
            current_node_id = session.get("current_node", "main")
            node = self._find_node_by_id(current_node_id)
            
            if not node:
                logger.error(f"Nodo no encontrado: {current_node_id}")
                return self._get_error_message("node_not_found")
            
            # Formatear y mostrar contenido
            formatted_content = self._format_node_content(node, session)
            
            if chat_window:
                chat_window.add_message(formatted_content, is_user=False)
            
            return formatted_content
            
        except Exception as e:
            logger.error(f"Error mostrando nodo actual: {e}")
            return self._get_error_message("display_error")
    
    def navigate_to_option(self, option_number: int, session: Dict, chat_window=None) -> str:
        """
        Navega a una opción específica del menú actual.
        
        Args:
            option_number: Número de opción seleccionada
            session: Datos de sesión del usuario
            chat_window: Ventana de chat para mostrar respuesta
            
        Returns:
            str: Contenido del nodo de destino o mensaje de error
        """
        try:
            current_node_id = session.get("current_node", "main")
            current_node = self._find_node_by_id(current_node_id)
            
            if not current_node or "children" not in current_node:
                return self._get_error_message("no_options_available")
            
            children = current_node["children"]
            
            # Validar número de opción
            if option_number < 1 or option_number > len(children):
                return self._get_error_message("invalid_option_number", 
                                             max_options=len(children))
            
            # Obtener nodo de destino
            target_node = children[option_number - 1]
            target_id = target_node["id"]
            
            # Actualizar historial de navegación
            if "navigation_history" not in session:
                session["navigation_history"] = []
            
            session["navigation_history"].append(current_node_id)
            session["current_node"] = target_id
            
            # Mostrar nodo de destino
            return self.show_current_node(session, chat_window)
            
        except Exception as e:
            logger.error(f"Error navegando a opción {option_number}: {e}")
            return self._get_error_message("navigation_error")
    
    def go_back(self, session: Dict, chat_window=None) -> str:
        """
        Navega al nodo anterior en el historial.
        
        Args:
            session: Datos de sesión del usuario
            chat_window: Ventana de chat para mostrar respuesta
            
        Returns:
            str: Contenido del nodo anterior o mensaje de error
        """
        try:
            history = session.get("navigation_history", [])
            
            if not history:
                return self._get_message("already_at_root")
            
            # Obtener nodo anterior
            previous_node_id = history.pop()
            session["current_node"] = previous_node_id
            
            return self.show_current_node(session, chat_window)
            
        except Exception as e:
            logger.error(f"Error navegando hacia atrás: {e}")
            return self._get_error_message("navigation_error")
    
    def go_home(self, session: Dict, chat_window=None) -> str:
        """
        Navega al menú principal.
        
        Args:
            session: Datos de sesión del usuario
            chat_window: Ventana de chat para mostrar respuesta
            
        Returns:
            str: Contenido del menú principal
        """
        try:
            session["current_node"] = "main"
            session["navigation_history"] = []
            
            return self.show_current_node(session, chat_window)
            
        except Exception as e:
            logger.error(f"Error navegando al inicio: {e}")
            return self._get_error_message("navigation_error")
    
    def _find_node_by_id(self, node_id: str, current_node: Dict = None) -> Optional[Dict]:
        """
        Busca un nodo por su ID en el árbol de ayuda.
        
        Args:
            node_id: ID del nodo a buscar
            current_node: Nodo actual para búsqueda recursiva
            
        Returns:
            Dict: Nodo encontrado o None si no existe
        """
        if current_node is None:
            current_node = self.help_tree.get("root", {})
        
        # Verificar si es el nodo buscado
        if current_node.get("id") == node_id:
            return current_node
        
        # Buscar en hijos
        if "children" in current_node:
            for child in current_node["children"]:
                result = self._find_node_by_id(node_id, child)
                if result:
                    return result
        
        return None
    
    def _format_node_content(self, node: Dict, session: Dict) -> str:
        """
        Formatea el contenido de un nodo para mostrar al usuario.
        
        Args:
            node: Nodo a formatear
            session: Datos de sesión del usuario
            
        Returns:
            str: Contenido formateado
        """
        lang = session.get("language", "es")
        content_parts = []
        
        # Título del nodo
        title = self._get_localized_text(node.get("title", {}), lang)
        content_parts.append(f"\n{title}")
        content_parts.append("=" * len(title.replace("🏠", "").replace("🎯", "").replace("🖥️", "").replace("🤖", "").replace("📅", "").replace("⚙️", "").replace("🔧", "").replace("🆘", "").strip()))
        
        # Descripción del nodo
        description = self._get_localized_text(node.get("description", {}), lang)
        if description:
            content_parts.append(f"\n{description}")
        
        # Contenido específico del nodo
        content = self._get_localized_text(node.get("content", {}), lang)
        if content:
            content_parts.append(f"\n{content}")
            
            # Ejemplos si están disponibles
            examples = node.get("examples", {}).get(lang, [])
            if examples:
                content_parts.append("\n💡 **Ejemplos:**")
                for example in examples:
                    content_parts.append(f"   • {example}")
        
        # Opciones de navegación (hijos)
        if "children" in node:
            content_parts.append("\n📋 **Opciones disponibles:**" if lang == "es" else "\n📋 **Available options:**")
            
            for i, child in enumerate(node["children"], 1):
                child_title = self._get_localized_text(child.get("title", {}), lang)
                child_desc = self._get_localized_text(child.get("description", {}), lang)
                
                if child_desc:
                    content_parts.append(f"   {child_title}")
                    content_parts.append(f"      {child_desc}")
                else:
                    content_parts.append(f"   {child_title}")
            
            # Instrucciones de navegación
            nav_instructions = (
                "\n🔹 Escribe el número de la opción que deseas explorar"
                if lang == "es" else
                "\n🔹 Type the number of the option you want to explore"
            )
            content_parts.append(nav_instructions)
        
        # Comandos de navegación disponibles
        nav_help = self._get_navigation_help(session)
        if nav_help:
            content_parts.append(f"\n{nav_help}")
        
        return "\n".join(content_parts)
    
    def _get_localized_text(self, text_dict: Dict, language: str) -> str:
        """
        Obtiene texto localizado según el idioma.
        
        Args:
            text_dict: Diccionario con textos por idioma
            language: Código de idioma
            
        Returns:
            str: Texto localizado
        """
        if isinstance(text_dict, str):
            return text_dict
        
        if isinstance(text_dict, dict):
            return text_dict.get(language, text_dict.get("es", ""))
        
        return ""
    
    def _get_navigation_help(self, session: Dict) -> str:
        """
        Obtiene ayuda de navegación contextual.
        
        Args:
            session: Datos de sesión del usuario
            
        Returns:
            str: Texto de ayuda de navegación
        """
        lang = session.get("language", "es")
        current_node_id = session.get("current_node", "main")
        has_history = len(session.get("navigation_history", [])) > 0
        
        if lang == "es":
            help_parts = ["🔧 **Comandos de navegación:**"]
            
            if has_history:
                help_parts.append("   • 'atrás' - Volver al menú anterior")
            
            if current_node_id != "main":
                help_parts.append("   • 'inicio' - Ir al menú principal")
            
            help_parts.extend([
                "   • 'buscar [término]' - Buscar en la ayuda",
                "   • 'salir' - Cerrar sistema de ayuda"
            ])
        else:
            help_parts = ["🔧 **Navigation commands:**"]
            
            if has_history:
                help_parts.append("   • 'back' - Return to previous menu")
            
            if current_node_id != "main":
                help_parts.append("   • 'home' - Go to main menu")
            
            help_parts.extend([
                "   • 'search [term]' - Search in help",
                "   • 'exit' - Close help system"
            ])
        
        return "\n".join(help_parts)
    
    def _get_message(self, key: str, **kwargs) -> str:
        """Obtiene un mensaje localizado."""
        lang = self.help_manager.current_language
        
        messages = {
            "es": {
                "already_at_root": "ℹ️ Ya estás en el menú principal.",
                "node_not_found": "❌ Sección no encontrada.",
                "no_options_available": "ℹ️ No hay opciones disponibles en esta sección.",
                "invalid_option_number": "❌ Opción inválida. Selecciona un número entre 1 y {max_options}.",
                "display_error": "❌ Error mostrando contenido. Intenta de nuevo.",
                "navigation_error": "❌ Error de navegación. Intenta de nuevo."
            },
            "en": {
                "already_at_root": "ℹ️ You are already at the main menu.",
                "node_not_found": "❌ Section not found.",
                "no_options_available": "ℹ️ No options available in this section.",
                "invalid_option_number": "❌ Invalid option. Select a number between 1 and {max_options}.",
                "display_error": "❌ Error displaying content. Please try again.",
                "navigation_error": "❌ Navigation error. Please try again."
            }
        }
        
        lang_messages = messages.get(lang, messages["es"])
        message = lang_messages.get(key, f"Message not found: {key}")
        
        # Formatear mensaje con parámetros
        if kwargs:
            try:
                message = message.format(**kwargs)
            except Exception:
                pass
        
        return message
    
    def _get_error_message(self, error_type: str, **kwargs) -> str:
        """Obtiene un mensaje de error localizado."""
        return self._get_message(error_type, **kwargs)
    
    def get_current_path(self, session: Dict) -> List[str]:
        """
        Obtiene la ruta actual de navegación.
        
        Args:
            session: Datos de sesión del usuario
            
        Returns:
            List[str]: Lista con los IDs de nodos en la ruta actual
        """
        path = session.get("navigation_history", []).copy()
        path.append(session.get("current_node", "main"))
        return path
    
    def get_breadcrumb(self, session: Dict) -> str:
        """
        Obtiene una representación de breadcrumb de la navegación actual.
        
        Args:
            session: Datos de sesión del usuario
            
        Returns:
            str: Breadcrumb formateado
        """
        path = self.get_current_path(session)
        lang = session.get("language", "es")
        
        breadcrumb_parts = []
        for node_id in path:
            node = self._find_node_by_id(node_id)
            if node:
                title = self._get_localized_text(node.get("title", {}), lang)
                # Limpiar emojis para breadcrumb
                clean_title = title.replace("🏠", "").replace("🎯", "").replace("🖥️", "").replace("🤖", "").replace("📅", "").replace("⚙️", "").replace("🔧", "").replace("🆘", "").strip()
                breadcrumb_parts.append(clean_title)
        
        return " > ".join(breadcrumb_parts)