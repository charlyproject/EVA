#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HelpSearcher - Sistema de Búsqueda Inteligente de Ayuda
======================================================

Este módulo proporciona capacidades de búsqueda inteligente en el
sistema de ayuda de EVA, usando coincidencias difusas y indexación
de palabras clave.

Autor: EVA Team
Versión: 1.0
Fecha: 2025-01-15
"""

import logging
from typing import Dict, List, Tuple, Any
from rapidfuzz import fuzz, process

logger = logging.getLogger("EVA")


class HelpSearcher:
    """
    Motor de búsqueda inteligente para el sistema de ayuda de EVA.
    
    Proporciona búsqueda por palabras clave, coincidencias difusas
    y ranking de resultados por relevancia.
    """
    
    def __init__(self, help_tree: Dict, help_manager):
        """
        Inicializa el motor de búsqueda.
        
        Args:
            help_tree: Árbol de ayuda cargado desde JSON
            help_manager: Referencia al HelpManager principal
        """
        self.help_tree = help_tree
        self.help_manager = help_manager
        
        # Índices de búsqueda
        self.keyword_index = {}
        self.content_index = {}
        self.node_cache = {}
        
        # Configuración de búsqueda
        self.min_similarity_score = 60  # Puntuación mínima para coincidencias difusas
        self.max_results = 5  # Máximo número de resultados a mostrar
        
        # Construir índices
        self._build_search_indexes()
        
        logger.info("HelpSearcher inicializado correctamente")
    
    def _build_search_indexes(self):
        """Construye los índices de búsqueda para optimizar las consultas."""
        try:
            # Índice de palabras clave predefinidas
            search_index = self.help_tree.get("search_index", {})
            self.keyword_index = search_index.get("keywords", {})
            
            # Índice de contenido completo
            self._index_all_content()
            
            logger.info(f"Índices de búsqueda construidos: {len(self.keyword_index)} palabras clave, {len(self.content_index)} nodos")
            
        except Exception as e:
            logger.error(f"Error construyendo índices de búsqueda: {e}")
    
    def _index_all_content(self, node: Dict = None, path: str = ""):
        """
        Indexa todo el contenido del árbol de ayuda recursivamente.
        
        Args:
            node: Nodo actual (None para empezar desde la raíz)
            path: Ruta actual en el árbol
        """
        if node is None:
            node = self.help_tree.get("root", {})
            path = "root"
        
        node_id = node.get("id", path)
        
        # Cachear nodo para acceso rápido
        self.node_cache[node_id] = node
        
        # Indexar contenido del nodo
        searchable_content = self._extract_searchable_content(node)
        if searchable_content:
            self.content_index[node_id] = searchable_content
        
        # Procesar hijos recursivamente
        if "children" in node:
            for i, child in enumerate(node["children"]):
                child_path = f"{path}.{i}"
                self._index_all_content(child, child_path)
    
    def _extract_searchable_content(self, node: Dict) -> Dict[str, str]:
        """
        Extrae contenido buscable de un nodo.
        
        Args:
            node: Nodo del árbol de ayuda
            
        Returns:
            Dict con contenido buscable por idioma
        """
        searchable = {}
        
        for lang in ["es", "en"]:
            content_parts = []
            
            # Título
            title = self._get_localized_text(node.get("title", {}), lang)
            if title:
                content_parts.append(title)
            
            # Descripción
            description = self._get_localized_text(node.get("description", {}), lang)
            if description:
                content_parts.append(description)
            
            # Contenido
            content = self._get_localized_text(node.get("content", {}), lang)
            if content:
                content_parts.append(content)
            
            # Ejemplos
            examples = node.get("examples", {}).get(lang, [])
            if examples:
                content_parts.extend(examples)
            
            # Combinar todo el contenido
            if content_parts:
                searchable[lang] = " ".join(content_parts).lower()
        
        return searchable
    
    def search(self, query: str, session: Dict, chat_window=None) -> str:
        """
        Realiza una búsqueda en el sistema de ayuda.
        
        Args:
            query: Consulta de búsqueda del usuario
            session: Datos de sesión del usuario
            chat_window: Ventana de chat para mostrar resultados
            
        Returns:
            str: Resultados de búsqueda formateados
        """
        try:
            if not query or not query.strip():
                return self._get_message("empty_query")
            
            lang = session.get("language", "es")
            query_clean = query.strip().lower()
            
            # Buscar usando diferentes métodos
            results = []
            
            # 1. Búsqueda por palabras clave exactas
            keyword_results = self._search_by_keywords(query_clean, lang)
            results.extend(keyword_results)
            
            # 2. Búsqueda difusa en contenido
            content_results = self._search_in_content(query_clean, lang)
            results.extend(content_results)
            
            # 3. Búsqueda por coincidencias parciales
            partial_results = self._search_partial_matches(query_clean, lang)
            results.extend(partial_results)
            
            # Eliminar duplicados y ordenar por relevancia
            unique_results = self._deduplicate_and_rank(results)
            
            # Formatear y mostrar resultados
            if unique_results:
                formatted_results = self._format_search_results(unique_results, query, lang)
                
                if chat_window:
                    chat_window.add_message(formatted_results, is_user=False)
                
                return formatted_results
            else:
                no_results_msg = self._get_message("no_results", query=query)
                
                if chat_window:
                    chat_window.add_message(no_results_msg, is_user=False)
                
                return no_results_msg
                
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return self._get_message("search_error")
    
    def _search_by_keywords(self, query: str, language: str) -> List[Tuple[str, float, str]]:
        """
        Busca usando el índice de palabras clave predefinidas.
        
        Args:
            query: Consulta de búsqueda
            language: Idioma de búsqueda
            
        Returns:
            List de tuplas (node_id, score, match_type)
        """
        results = []
        
        for keyword, node_ids in self.keyword_index.items():
            # Calcular similitud con la consulta
            similarity = fuzz.partial_ratio(query, keyword.lower())
            
            if similarity >= self.min_similarity_score:
                if isinstance(node_ids, str):
                    node_ids = [node_ids]
                
                for node_id in node_ids:
                    results.append((node_id, similarity, "keyword"))
        
        return results
    
    def _search_in_content(self, query: str, language: str) -> List[Tuple[str, float, str]]:
        """
        Busca en el contenido completo de los nodos.
        
        Args:
            query: Consulta de búsqueda
            language: Idioma de búsqueda
            
        Returns:
            List de tuplas (node_id, score, match_type)
        """
        results = []
        
        for node_id, content_dict in self.content_index.items():
            content = content_dict.get(language, "")
            
            if content:
                # Búsqueda exacta de subcadenas
                if query in content:
                    score = 90 + (len(query) / len(content)) * 10  # Bonus por longitud de coincidencia
                    results.append((node_id, min(score, 100), "exact_content"))
                else:
                    # Búsqueda difusa
                    similarity = fuzz.partial_ratio(query, content)
                    if similarity >= self.min_similarity_score:
                        results.append((node_id, similarity, "fuzzy_content"))
        
        return results
    
    def _search_partial_matches(self, query: str, language: str) -> List[Tuple[str, float, str]]:
        """
        Busca coincidencias parciales en títulos y descripciones.
        
        Args:
            query: Consulta de búsqueda
            language: Idioma de búsqueda
            
        Returns:
            List de tuplas (node_id, score, match_type)
        """
        results = []
        query_words = query.split()
        
        for node_id, node in self.node_cache.items():
            # Buscar en título
            title = self._get_localized_text(node.get("title", {}), language).lower()
            if title:
                title_score = self._calculate_word_match_score(query_words, title)
                if title_score > 0:
                    results.append((node_id, title_score, "title_match"))
            
            # Buscar en descripción
            description = self._get_localized_text(node.get("description", {}), language).lower()
            if description:
                desc_score = self._calculate_word_match_score(query_words, description)
                if desc_score > 0:
                    results.append((node_id, desc_score * 0.8, "description_match"))  # Menor peso que título
        
        return results
    
    def _calculate_word_match_score(self, query_words: List[str], text: str) -> float:
        """
        Calcula puntuación basada en coincidencias de palabras.
        
        Args:
            query_words: Palabras de la consulta
            text: Texto donde buscar
            
        Returns:
            float: Puntuación de coincidencia (0-100)
        """
        if not query_words or not text:
            return 0
        
        matches = 0
        total_words = len(query_words)
        
        for word in query_words:
            if len(word) >= 3:  # Solo palabras de 3+ caracteres
                if word in text:
                    matches += 1
                else:
                    # Búsqueda difusa para palabras individuales
                    word_similarity = process.extractOne(word, text.split(), scorer=fuzz.ratio)
                    if word_similarity and word_similarity[1] >= 80:
                        matches += 0.7  # Coincidencia parcial
        
        return (matches / total_words) * 100 if total_words > 0 else 0
    
    def _deduplicate_and_rank(self, results: List[Tuple[str, float, str]]) -> List[Tuple[str, float, str]]:
        """
        Elimina duplicados y ordena resultados por relevancia.
        
        Args:
            results: Lista de resultados con duplicados
            
        Returns:
            List de resultados únicos ordenados por puntuación
        """
        # Agrupar por node_id y tomar la mejor puntuación
        node_scores = {}
        
        for node_id, score, match_type in results:
            if node_id not in node_scores or score > node_scores[node_id][0]:
                node_scores[node_id] = (score, match_type)
        
        # Convertir de vuelta a lista y ordenar
        unique_results = [(node_id, score, match_type) 
                         for node_id, (score, match_type) in node_scores.items()]
        
        # Ordenar por puntuación descendente
        unique_results.sort(key=lambda x: x[1], reverse=True)
        
        # Limitar número de resultados
        return unique_results[:self.max_results]
    
    def _format_search_results(self, results: List[Tuple[str, float, str]], query: str, language: str) -> str:
        """
        Formatea los resultados de búsqueda para mostrar al usuario.
        
        Args:
            results: Lista de resultados ordenados
            query: Consulta original del usuario
            language: Idioma de los resultados
            
        Returns:
            str: Resultados formateados
        """
        if language == "es":
            header = f"🔍 **Resultados de búsqueda para '{query}':**\n"
            no_content = "Sin contenido disponible"
        else:
            header = f"🔍 **Search results for '{query}':**\n"
            no_content = "No content available"
        
        content_parts = [header]
        
        for i, (node_id, score, match_type) in enumerate(results, 1):
            node = self.node_cache.get(node_id)
            if not node:
                continue
            
            # Título del resultado
            title = self._get_localized_text(node.get("title", {}), language)
            clean_title = title.replace("🏠", "").replace("🎯", "").replace("🖥️", "").replace("🤖", "").replace("📅", "").replace("⚙️", "").replace("🔧", "").replace("🆘", "").strip()
            
            # Descripción breve
            description = self._get_localized_text(node.get("description", {}), language)
            if not description:
                content = self._get_localized_text(node.get("content", {}), language)
                if content:
                    # Tomar primeras 100 caracteres como descripción
                    description = content[:100] + "..." if len(content) > 100 else content
                else:
                    description = no_content
            
            # Formatear resultado
            content_parts.append(f"\n**{i}. {clean_title}**")
            content_parts.append(f"   {description}")
            content_parts.append(f"   📍 ID: {node_id} | Relevancia: {score:.0f}%")
        
        # Instrucciones adicionales
        if language == "es":
            instructions = "\n\n💡 **Para ver más detalles:**\n   • Navega al menú correspondiente usando los números\n   • Usa 'inicio' para volver al menú principal"
        else:
            instructions = "\n\n💡 **To see more details:**\n   • Navigate to the corresponding menu using numbers\n   • Use 'home' to return to main menu"
        
        content_parts.append(instructions)
        
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
    
    def _get_message(self, key: str, **kwargs) -> str:
        """Obtiene un mensaje localizado."""
        lang = self.help_manager.current_language
        
        messages = {
            "es": {
                "empty_query": "❓ Por favor, especifica qué quieres buscar.\n💡 Ejemplo: 'buscar archivos' o 'buscar comandos de voz'",
                "no_results": "🔍 No se encontraron resultados para '{query}'.\n💡 Intenta con términos más generales o usa 'inicio' para ver todas las opciones.",
                "search_error": "❌ Error realizando búsqueda. Intenta de nuevo."
            },
            "en": {
                "empty_query": "❓ Please specify what you want to search for.\n💡 Example: 'search files' or 'search voice commands'",
                "no_results": "🔍 No results found for '{query}'.\n💡 Try more general terms or use 'home' to see all options.",
                "search_error": "❌ Error performing search. Please try again."
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
    
    def get_search_suggestions(self, partial_query: str, language: str = "es") -> List[str]:
        """
        Obtiene sugerencias de búsqueda basadas en una consulta parcial.
        
        Args:
            partial_query: Consulta parcial del usuario
            language: Idioma para las sugerencias
            
        Returns:
            List de sugerencias de búsqueda
        """
        suggestions = []
        
        if len(partial_query) < 2:
            return suggestions
        
        # Buscar en palabras clave
        for keyword in self.keyword_index.keys():
            if partial_query.lower() in keyword.lower():
                suggestions.append(keyword)
        
        # Limitar número de sugerencias
        return suggestions[:5]
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del motor de búsqueda.
        
        Returns:
            Dict con estadísticas del sistema de búsqueda
        """
        return {
            "indexed_keywords": len(self.keyword_index),
            "indexed_nodes": len(self.content_index),
            "cached_nodes": len(self.node_cache),
            "min_similarity_score": self.min_similarity_score,
            "max_results": self.max_results
        }