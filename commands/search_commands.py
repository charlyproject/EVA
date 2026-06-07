"""
Sistema de Comandos de Búsqueda - Arquitectura Limpia
Comandos naturales únicos para búsqueda web.
Añadido: soporte para Tavily (web, internet, tavily)
         Añadido: soporte para DuckDuckGo (ddg, pato, duck)
         Fallback automático: Tavily → DuckDuckGo si Tavily falla
"""

import logging
import webbrowser
from urllib.parse import quote

logger = logging.getLogger("EVA")


class SearchCommandHandler:
    """Handler unificado para comandos de búsqueda"""

    def __init__(self, processor):
        self.processor = processor
        self.config = processor.config
        self.language_manager = processor.language_manager
        self.session_manager = processor.session_manager

        # Comandos de búsqueda - ÚNICOS Y NATURALES
        self.search_commands = {
            "es": {
                "busca": self._search_google,
                "web": self._search_tavily,
                "internet": self._search_tavily,
                "tavily": self._search_tavily,
                "ddg": self._search_duckduckgo,
                "pato": self._search_duckduckgo,
                "duck": self._search_duckduckgo,
            },
            "en": {
                "search": self._search_google,
                "web": self._search_tavily,
                "internet": self._search_tavily,
                "tavily": self._search_tavily,
                "ddg": self._search_duckduckgo,
                "duck": self._search_duckduckgo,
            }
        }

    @property
    def lang(self) -> str:
        """Obtiene el idioma actual"""
        language = self.config.get("language", "es")
        if isinstance(language, str) and language in ["es", "en"]:
            return language
        return "es"

    def can_handle(self, text: str) -> bool:
        """Verifica si puede manejar el comando"""
        text_lower = text.lower().strip()
        commands = self.search_commands.get(self.lang, {})
        return any(text_lower.startswith(cmd) for cmd in commands.keys())

    def handle(self, text: str, chat_window) -> bool:
        """Maneja el comando de búsqueda"""
        try:
            text_lower = text.lower().strip()
            commands = self.search_commands.get(self.lang, {})

            # Buscar comando que coincida
            for command, handler in commands.items():
                if text_lower.startswith(command):
                    return handler(text, chat_window)
            return False
        except Exception as e:
            logger.error(f"Error en comando de búsqueda: {str(e)}")
            error_msg = "Error ejecutando búsqueda"
            chat_window.add_message(error_msg, is_user=False)
            return True

    def _search_google(self, text: str, chat_window) -> bool:
        """Realiza búsqueda en Google"""
        try:
            query = self._extract_query(text)
            if not query:
                error_msg = self.language_manager.get_text("responses.search_no_query")
                chat_window.add_message(error_msg, is_user=False)
                return True

            search_url = f"https://www.google.com/search?q={quote(query)}"
            webbrowser.open(search_url)

            response = self.language_manager.get_text("responses.searching", query=query)
            chat_window.add_message(response, is_user=False)
            logger.info(f"Búsqueda ejecutada: {query}")
            return True
        except Exception as e:
            logger.error(f"Error en búsqueda de Google: {e}")
            error_msg = self.language_manager.get_text("responses.search_error")
            chat_window.add_message(error_msg, is_user=False)
            return True

    def _search_tavily(self, text: str, chat_window, fallback_on_failure: bool = True) -> bool:
        """Realiza búsqueda en Tavily y muestra resultados en el chat.
        Si fallback_on_failure=True, recurre a DuckDuckGo si Tavily falla."""
        try:
            query = self._extract_query(text)
            if not query:
                msg = self.language_manager.get_text("responses.search_tavily_no_query")
                chat_window.add_message(msg, is_user=False)
                return True

            api_key = self.config.get("plugins", {}).get("tavily_api_key", "")
            if not api_key:
                # Sin API key de Tavily: fallback automático a DuckDuckGo
                if fallback_on_failure:
                    logger.info("Tavily API key no configurada. Redirigiendo a DuckDuckGo.")
                    return self._search_duckduckgo(text, chat_window)
                msg = self.language_manager.get_text("responses.search_tavily_no_api_key")
                chat_window.add_message(msg, is_user=False)
                return True

            search_depth = self.config.get("plugins", {}).get("tavily_search_depth", "basic")
            max_results = self.config.get("plugins", {}).get("tavily_max_results", 3)

            try:
                import requests
                response = requests.post(
                    "https://api.tavily.com/search",
                    json={"api_key": api_key, "query": query, "search_depth": search_depth, "max_results": max_results},
                    timeout=15
                )
            except requests.exceptions.RequestException as req_err:
                logger.warning(f"Error de conexión con Tavily: {req_err}")
                if fallback_on_failure:
                    logger.info("Tavily no responde. Fallback a DuckDuckGo.")
                    chat_window.add_message("Tavily no disponible. Buscando con DuckDuckGo...", is_user=False)
                    return self._search_duckduckgo(text, chat_window)
                msg = self.language_manager.get_text("responses.search_tavily_error")
                chat_window.add_message(msg, is_user=False)
                return True

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if not results:
                    msg = self.language_manager.get_text("responses.search_tavily_no_results").format(query=query)
                    chat_window.add_message(msg, is_user=False)
                    return True

                answer = self.language_manager.get_text("responses.search_tavily_results").format(query=query) + "<br>"
                for i, res in enumerate(results, 1):
                    title = res.get("title", "Sin título")
                    url = res.get("url", "")
                    snippet = res.get("content", "")[:200]
                    answer += f"<p><b>{i}. <a href='{url}'>{title}</a></b><br>{snippet}...</p>"
                chat_window.add_message(answer, is_user=False)
            else:
                logger.warning(f"Tavily respondió con código {response.status_code}")
                if fallback_on_failure:
                    logger.info("Tavily devolvió error HTTP. Fallback a DuckDuckGo.")
                    msg = self.language_manager.get_text("responses.tavily_fallback")
                    chat_window.add_message(msg, is_user=False)
                    return self._search_duckduckgo(text, chat_window)
                msg = self.language_manager.get_text("responses.search_tavily_error")
                chat_window.add_message(msg, is_user=False)
            return True
        except Exception as e:
            logger.error(f"Error en Tavily: {e}")
            if fallback_on_failure:
                logger.info("Excepción en Tavily. Fallback a DuckDuckGo.")
                return self._search_duckduckgo(text, chat_window)
            msg = self.language_manager.get_text("responses.search_tavily_error")
            chat_window.add_message(msg, is_user=False)
            return True

    def _search_duckduckgo(self, text: str, chat_window) -> bool:
        """Realiza búsqueda en DuckDuckGo y muestra resultados en el chat"""
        try:
            query = self._extract_query(text)
            if not query:
                msg = self.language_manager.get_text("responses.search_tavily_no_query")
                chat_window.add_message(msg, is_user=False)
                return True

            try:
                try:
                    from ddgs import DDGS
                except ImportError:
                    from duckduckgo_search import DDGS
            except ImportError:
                msg = self.language_manager.get_text("responses.search_tavily_error")
                chat_window.add_message(msg, is_user=False)
                logger.error("Paquete 'ddgs' no instalado. Ejecuta: pip install ddgs")
                return True

            try:
                raw_results = list(DDGS().text(query, max_results=3))
            except Exception as ddg_error:
                logger.error(f"Error en DuckDuckGo: {ddg_error}")
                msg = self.language_manager.get_text("responses.search_tavily_error")
                chat_window.add_message(msg, is_user=False)
                return True

            # Convertir resultados a formato de diccionario unificado
            results = []
            if raw_results is not None:
                for res in raw_results:
                    if isinstance(res, dict):
                        results.append(res)
                    elif isinstance(res, (tuple, list)):
                        results.append({
                            "title": res[0] if len(res) > 0 else "",
                            "href": res[1] if len(res) > 1 else "",
                            "body": res[2] if len(res) > 2 else ""
                        })

            if not results:
                msg = self.language_manager.get_text("responses.search_ddg_no_results").format(query=query)
                chat_window.add_message(msg, is_user=False)
                return True

            answer = self.language_manager.get_text("responses.search_ddg_results").format(query=query) + "<br>"
            for i, res in enumerate(results, 1):
                title = res.get("title", "Sin título")
                url = res.get("href", "")
                snippet = res.get("body", "")
                if snippet:
                    snippet = snippet[:200]
                answer += f"<p><b>{i}. <a href='{url}'>{title}</a></b><br>{snippet}...</p>"
            chat_window.add_message(answer, is_user=False)
            logger.info(f"Búsqueda DuckDuckGo ejecutada: {query}")
            return True

        except Exception as e:
            logger.error(f"Error en DuckDuckGo: {e}")
            msg = self.language_manager.get_text("responses.search_tavily_error")
            chat_window.add_message(msg, is_user=False)
            return True

    def _extract_query(self, text: str) -> str:
        """Extrae la consulta de búsqueda del comando (para todos los prefijos)"""
        try:
            text_lower = text.lower().strip()
            # Prefijos ordenados de más largo a más corto para evitar conflictos
            prefixes = ["internet ", "tavily ", "busca ", "search ", "web ", "ddg ", "pato ", "duck "]
            for prefix in prefixes:
                if text_lower.startswith(prefix):
                    return text[len(prefix):].strip()
            return ""
        except Exception as e:
            logger.error(f"Error extrayendo consulta: {e}")
            return ""