import json
import logging
import os
import random
import re
import subprocess
import time
import webbrowser
from abc import ABC, abstractmethod

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    import ctypes
    import ctypes.wintypes

import win32clipboard
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from rapidfuzz import fuzz, process

from utils.command_utils import extract_conversation_text
from utils.file_utils import load_last_folder_path, save_last_folder_path, get_working_folder
from .ollama_integration import OllamaIntegration
from .ai_provider import AIProvider, OllamaProvider, OpenRouterProvider
from .system_commands import SystemCommandHandler
from .search_commands import SearchCommandHandler
from .multimedia_commands import MultimediaCommandHandler
from .file_commands import FileCommandHandler
from .windows_commands import WindowsCommandHandler
from .context_manager import ContextManager
from .dispatcher import CommandDispatcher

from utils.threading_utils import submit_background_task, submit_task, ThreadPriority


logger = logging.getLogger("EVA")


# ====================
# COMMAND HANDLER BASE
# ====================
class CommandHandler(ABC):
    def __init__(self, processor: "CommandProcessor"):
        self.processor = processor
        self.config = processor.config
        self.language_manager = processor.language_manager
        self.session_manager = processor.session_manager

    @abstractmethod
    def can_handle(self, text: str) -> bool:
        pass

    @abstractmethod
    def handle(self, text: str, chat_window) -> bool:
        pass

    @property
    def lang(self) -> str:
        # Simplified language detection - always return a valid string
        language = self.config.get("language", "es")
        if isinstance(language, str) and language in ["es", "en"]:
            return language
        return "es"  # Safe fallback

    def speak(self, text):
        """Maneja la síntesis de voz de forma segura"""
        try:
            if (
                self.processor.eva
                and hasattr(self.processor.eva, "speech")
                and self.processor.eva.speech
            ):
                self.processor.eva.speech.speak(text)
            elif self.processor.eva and hasattr(self.processor.eva, "chat_window"):
                self.processor.eva.chat_window.add_message(
                    f"Intento de hablar: {text}", is_user=False
                )
        except Exception as e:
            logger.error(f"Error al intentar hablar: {str(e)}")


# ========================
# CONCRETE HANDLER CLASSES
# ========================
class ModelSelectionHandler(CommandHandler):
    """Maneja el comando 'modelo' — soporta Ollama y OpenRouter."""
    def can_handle(self, text: str) -> bool:
        lang = self.lang
        model_keywords = self.processor.command_map.get("model", {}).get(lang, [])
        text_lower = text.lower()

        if any(kw in text_lower for kw in model_keywords):
            return True

        if re.search(r'\b(modelo|model)\b', text_lower) and re.search(r'\b\d+\b', text_lower):
            return True

        if not self._is_file_context(text):
            stripped = text.strip()
            if stripped.isdigit() and int(stripped) >= 1:
                return True
            number_words = {
                "uno": "1", "dos": "2", "tres": "3",
                "cuatro": "4", "cinco": "5", "seis": "6", "siete": "7",
                "ocho": "8", "nueve": "9", "diez": "10",
                "one": "1", "two": "2", "three": "3",
                "four": "4", "five": "5", "six": "6", "seven": "7",
                "eight": "8", "nine": "9", "ten": "10",
                "primero": "1", "segundo": "2", "tercero": "3",
                "first": "1", "second": "2", "third": "3"
            }
            if text.strip().lower() in number_words:
                return True

        return False

    def _is_file_context(self, text: str) -> bool:
        return (hasattr(self.processor, 'last_opened_folder') and
                self.processor.last_opened_folder and
                hasattr(self.processor, 'current_folder_files') and
                len(self.processor.current_folder_files) > 0)

    def _build_unified_model_list(self) -> tuple:
        """Construye lista unificada de modelos. Retorna (list, list, list) = (display_list, provider_list, model_name_list)."""
        display_list = []
        provider_list = []
        model_name_list = []

        # Modelos Ollama
        if self.processor.ollama:
            try:
                ollama_models = self.processor.ollama.get_installed_models(force_refresh=True)
                for name in ollama_models:
                    display_list.append(name)
                    provider_list.append("ollama")
                    model_name_list.append(name)
            except Exception as e:
                logger.error(f"Error obteniendo modelos Ollama: {e}")

        # Modelos OpenRouter (solo si hay API key)
        if self.processor.config.get("openrouter", {}).get("api_key", ""):
            try:
                from commands.ai_provider import OpenRouterProvider
                or_models = OpenRouterProvider.OPENROUTER_MODELS
                for name in or_models:
                    display_list.append(f"[OpenRouter] {name}")
                    provider_list.append("openrouter")
                    model_name_list.append(name)
            except Exception as e:
                logger.error(f"Error obteniendo modelos OpenRouter: {e}")

        return display_list, provider_list, model_name_list

    def handle(self, text: str, chat_window) -> bool:
        lang = self.lang
        model_keywords = self.processor.command_map.get("model", {}).get(lang, [])

        # Mostrar lista unificada de modelos
        if any(text.lower().startswith(kw) for kw in model_keywords):
            try:
                display_list, provider_list, model_name_list = self._build_unified_model_list()
                if not display_list:
                    no_models = self.language_manager.get_text("responses.no_models_available")
                    chat_window.add_message(no_models, is_user=False)
                    return True

                lines = [self.language_manager.get_text("responses.model_selection", models="")]
                current_provider = self.processor.config.get("ai_provider", "ollama")
                current_model = self.processor.ai_provider.current_model if self.processor.ai_provider else ""

                for i, display_name in enumerate(display_list, start=1):
                    is_active = False
                    if provider_list[i-1] == current_provider and model_name_list[i-1] == current_model:
                        is_active = True
                    marker = f" ({self.language_manager.get_text('responses.active', default='active')})" if is_active else ""
                    lines.append(f"  {i}. {display_name}{marker}")

                lines.append(f"\n{self.language_manager.get_text('responses.select_model_number')}")
                chat_window.add_message("\n".join(lines), is_user=False)
                return True
            except Exception as e:
                logger.error(f"Error obteniendo modelos: {str(e)}")
                error_msg = self.language_manager.get_text("responses.error_getting_models")
                chat_window.add_message(error_msg, is_user=False)
                return True

        # Seleccion por numero o palabra
        text_clean = text.strip().lower()
        number_words = {
            "uno": "1", "dos": "2", "tres": "3",
            "cuatro": "4", "cinco": "5", "seis": "6", "siete": "7",
            "ocho": "8", "nueve": "9", "diez": "10",
            "one": "1", "two": "2", "three": "3",
            "four": "4", "five": "5", "six": "6", "seven": "7",
            "eight": "8", "nine": "9", "ten": "10",
            "primero": "1", "segundo": "2", "tercero": "3",
            "first": "1", "second": "2", "third": "3"
        }
        selected = None
        if text.strip().isdigit():
            selected = text.strip()
        elif text_clean in number_words:
            selected = number_words[text_clean]

        if selected:
            try:
                idx = int(selected) - 1
                display_list, provider_list, model_name_list = self._build_unified_model_list()
                if idx < 0 or idx >= len(display_list):
                    invalid_msg = self.language_manager.get_text("responses.invalid_model_selection", count=len(display_list))
                    chat_window.add_message(invalid_msg, is_user=False)
                    return True

                target_provider = provider_list[idx]
                target_model = model_name_list[idx]

                if target_provider == "openrouter":
                    result = self.processor._update_ai_provider("openrouter", target_model)
                    if result:
                        msg = self.language_manager.get_text("responses.provider_changed_openrouter", model=target_model)
                        chat_window.add_message(msg, is_user=False)
                    else:
                        msg = self.language_manager.get_text("responses.no_openrouter_api_key")
                        chat_window.add_message(msg, is_user=False)
                else:
                    change_result = self.processor.ollama.change_model(target_model)
                    self.processor._update_ai_provider("ollama")
                    chat_window.add_message(change_result, is_user=False)

                return True
            except Exception as e:
                logger.error(f"Error cambiando modelo: {str(e)}")
                error_msg = self.language_manager.get_text("responses.error_changing_model")
                chat_window.add_message(error_msg, is_user=False)
                return True

        return False


class ConversationHandler(CommandHandler):
    def can_handle(self, text: str) -> bool:
        text_lower = text.lower().strip()
        
        # SOLO dos casos activan Ollama:
        # 1. Comandos que empiecen con "eva"
        if text_lower.startswith("eva "):
            remaining_text = text_lower[4:].strip()  # Quitar "eva "
            if len(remaining_text) > 0:  # Debe haber contenido después
                logger.info(f"🤖 Comando EVA detectado: '{remaining_text}'")
                return True
        
        # 2. Comando "resume"
        if text_lower.startswith("resume"):
            logger.info(f"🤖 Comando RESUME detectado para Ollama: '{text}'")
            return True
        
        # NO activar Ollama para ningún otro caso
        return False

    def handle(self, text: str, chat_window) -> bool:
        text_lower = text.lower().strip()
        
        if text_lower.startswith("resume"):
            logger.info("🤖 Procesando comando RESUME con Ollama")
            question = text  # Enviar comando completo a Ollama
        else:
            # Es comando "eva"
            logger.info("🤖 Procesando conversación EVA con Ollama")
            question = text[4:].strip()  # Quitar "eva " del inicio

        # Mostrar mensaje de procesamiento
        processing_text = self.language_manager.get_text("processing")
        chat_window.add_message(processing_text, is_user=False)

        # Lanzar hilo para procesamiento asíncrono
        submit_task(
            self._process_async, 
            question, chat_window,
            priority=ThreadPriority.NORMAL,
            name="ollama_conversation"
        )
        
        return True

    def _process_async(self, question, chat_window):
        """Procesa la solicitud en un hilo separado usando el proveedor activo."""
        try:
            if self.processor.ai_provider is None:
                raise RuntimeError("No hay proveedor de IA disponible")

            # Construir mensajes en formato OpenAI
            messages = []
            try:
                context = chat_window.get_conversation_context_for_ollama(question)
                if context:
                    messages.append({"role": "system", "content": context})
            except Exception:
                pass

            messages.append({"role": "user", "content": question})
            response = self.processor.ai_provider.generate_response(messages)
            
            # (Sin marca de agua: acceso libre)
                
        except RuntimeError as e:
            logger.error(f"Error procesando conversación: {str(e)}")
            response = "Error: No hay proveedor de IA disponible. Verifica que Ollama este instalado o configura OpenRouter en Ajustes."

        # --- LIMPIEZA DE BLOQUES <think> (modelos con razonamiento interno) ---
        clean_response = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()

        # Si tras eliminar el bloque <think> no queda respuesta útil,
        # extraer el contenido interno como mensaje informativo
        if len(clean_response) < 10:
            think_match = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
            if think_match:
                inner_think = think_match.group(1).strip()
                clean_response = f"[El modelo solo dio razonamiento interno] {inner_think[:300]}"
                logger.warning("El modelo solo devolvió bloque <think> sin respuesta final.")
            else:
                clean_response = "El modelo no generó respuesta. Prueba con otro modelo."
        # --- FIN LIMPIEZA <think> ---

        # SIEMPRE mostrar la respuesta de texto, independientemente del estado de mute
        if hasattr(chat_window, 'update_message_signal'):
            chat_window.update_message_signal.emit(clean_response, False)
        elif hasattr(chat_window, 'safe_add_message'):
            chat_window.safe_add_message(clean_response, is_user=False)
        else:
            # Fallback seguro para actualizar la UI
            try:
                chat_window.add_message(clean_response, is_user=False)
            except Exception as e:
                logger.error(f"Error actualizando UI desde hilo secundario: {e}")

        # SINTETIZAR VOZ CON PIPER TTS (solo si hay texto y no está silenciado)
        is_muted = hasattr(chat_window, 'is_muted') and chat_window.is_muted
        if not is_muted and clean_response and clean_response.strip():
            submit_background_task(self.speak, clean_response, name="tts_speak")

    def _extract_clean_question(self, text: str) -> str:
        """Extrae la pregunta limpiando todos los activadores de forma inteligente"""
        try:
            text_lower = text.lower().strip()
            
            # Lista completa de activadores a remover
            activators_to_remove = [
                # Variantes de EVA
                "eva", "eba", "heva", "heba", "ava", "iva",
                "oye eva", "hey eva", "hola eva", "eva por favor",
                # Variantes de asistente
                "asistente", "asistenta", "sistente", "sistenta",
                "assistant", "assistente", "asisente",
                # Variantes de ayuda
                "ayuda", "ayúdame", "ayudame", "help", "auxilio",
                # Palabras de cortesía
                "por favor", "please", "gracias", "thanks"
            ]
            
            # Ordenar por longitud (más largo primero) para evitar reemplazos parciales
            activators_to_remove.sort(key=len, reverse=True)
            
            cleaned_text = text_lower
            
            # Remover activadores
            for activator in activators_to_remove:
                if activator in cleaned_text:
                    cleaned_text = cleaned_text.replace(activator, " ")
            
            # Limpiar espacios múltiples y caracteres de puntuación inicial
            cleaned_text = " ".join(cleaned_text.split())
            cleaned_text = cleaned_text.lstrip(".,;:!?¿¡ ")
            
            # Si queda muy poco texto, usar el texto original sin el primer activador encontrado
            if len(cleaned_text.split()) < 2:
                for activator in activators_to_remove:
                    if text_lower.startswith(activator):
                        cleaned_text = text[len(activator):].strip()
                        break
            
            # Fallback: usar extract_conversation_text si está disponible
            if len(cleaned_text.split()) < 2:
                try:
                    cleaned_text = extract_conversation_text(text)
                except Exception:
                    cleaned_text = text
            
            return cleaned_text.strip() or text.strip()
            
        except Exception as e:
            logger.error(f"Error limpiando pregunta: {str(e)}")
            return text.strip()

    def _return_to_fast_mode(self):
        """Limpia memoria después de conversación con Ollama."""
        logger.info("Modo conversación finalizado.")

        # Liberar modelo de Ollama de la memoria
        try:
            if self.processor.ollama:
                logger.info("Liberando modelo de Ollama de la memoria...")
                self.processor.ollama.unload_model()
        except Exception as e:
            logger.error(f"Error liberando modelo de Ollama: {str(e)}")

        logger.info("Limpieza de memoria finalizada.")
        if hasattr(self.processor.eva, "chat_window"):
            text = self.language_manager.get_text("responses.returning_fast_mode")
            # Usar método seguro para actualizar UI
            if hasattr(self.processor.eva.chat_window, 'safe_add_message'):
                self.processor.eva.chat_window.safe_add_message(text, is_user=False)
            elif hasattr(self.processor.eva.chat_window, 'update_message_signal'):
                self.processor.eva.chat_window.update_message_signal.emit(text, False)


class OpenHandler(CommandHandler):
    def can_handle(self, text: str) -> bool:
        open_keywords = self.processor.command_map.get("open", {}).get(self.lang, [])
        result = any(text.lower().startswith(kw) for kw in open_keywords)
        logger.info(f"🔍 OpenHandler.can_handle('{text}') = {result}")
        return result

    def handle(self, text: str, chat_window) -> bool:
        target = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
        logger.info(f"🔍 OpenHandler.handle() - target extraído: '{target}'")
        self.process_open_command(target, chat_window, self.lang)
        return True

    def process_open_command(self, target, chat_window, lang):
        """VERSIÓN BASADA EN LA LÓGICA ANTIGUA QUE FUNCIONABA"""
        try:
            logger.info(f"🔍 Procesando comando 'abre': '{target}'")
            
            # USAR LA LÓGICA EXACTA DE LA VERSIÓN ANTIGUA QUE FUNCIONABA
            # 1. Intentar como programa
            if self.process_program_command(target, chat_window, lang):
                logger.info(f"✅ Comando procesado como programa: {target}")
                return

            # 2. Intentar como carpeta
            if self.process_folder_command(target, chat_window, lang):
                logger.info(f"✅ Comando procesado como carpeta: {target}")
                return

            # 3. Intentar como sitio web
            if self.process_website_command(target, chat_window, lang):
                logger.info(f"✅ Comando procesado como sitio web: {target}")
                return

            # 4. Intentar como archivo (SIEMPRE se ejecuta, igual que la versión antigua)
            logger.info(f"🎯 Intentando procesar como archivo: {target}")
            if self.process_file_command(target, chat_window, lang):
                logger.info(f"✅ Comando procesado como archivo: {target}")
                return

            # Si no se encontró nada
            logger.warning(f"❌ No se pudo procesar comando: {target}")
            not_found = self.language_manager.get_text("responses.not_found")
            chat_window.add_message(f"{not_found} '{target}'", is_user=False)
            
            # Sugerencia útil
            suggestion = self.language_manager.get_text("responses.file_command_tip", default="💡 Try: 'open file 1' to open by position, or use keywords from the name")
            chat_window.add_message(suggestion, is_user=False)

        except Exception as error:
            logger.error(f"Error procesando comando de apertura: {error}")

    def process_program_command(self, target, chat_window, lang):
        """Abre programas si están configurados"""
        try:
            programs = self.config.get("paths", {}).get("programs", {})

            # Buscar coincidencia exacta primero
            if target in programs:
                program_path = programs[target]
                if os.path.exists(program_path):
                    subprocess.Popen(program_path)
                    opening = self.language_manager.get_text("responses.opening")
                    chat_window.add_message(f"{opening} {target}", is_user=False)
                    return True

            # Buscar usando variantes configuradas
            matched_program = self.processor._find_command_with_variants(target, programs.keys())
            if matched_program and os.path.exists(programs[matched_program]):
                subprocess.Popen(programs[matched_program])
                opening = self.language_manager.get_text("responses.opening")
                chat_window.add_message(f"{opening} {matched_program}", is_user=False)
                return True

            # Búsqueda aproximada como fallback
            result = process.extractOne(
                target, programs.keys(), scorer=fuzz.token_set_ratio
            )

            if result:
                best_match, score, _ = result
                if score > 75 and os.path.exists(programs[best_match]):
                    subprocess.Popen(programs[best_match])
                    opening = self.language_manager.get_text("responses.opening")
                    approx = self.language_manager.get_text("responses.approx_match")
                    chat_window.add_message(
                        f"{opening} {best_match} ({approx})", is_user=False
                    )
                    return True

            return False
        
        except Exception as error:
            logger.error(f"Error procesando programa: {error}")
            return False
    
    def process_folder_command(self, target, chat_window, lang):
        """Abre carpetas si están configuradas - OPTIMIZADO PARA VELOCIDAD"""
        try:
            folders = self.config.get("paths", {}).get("folders", {})

            # VERIFICACIÓN MEJORADA: Solo procesar si es claramente una carpeta
            # Evitar confusión con nombres de archivos largos
            target_words = target.lower().split()
            
            # Si el comando tiene muchas palabras, probablemente es un archivo, no una carpeta
            if len(target_words) > 2:
                logger.debug(f"🔍 Comando con muchas palabras ({len(target_words)}), probablemente es archivo: '{target}'")
                return False

            # Buscar coincidencia exacta primero (SIN verificar si existe - más rápido)
            if target in folders:
                folder_path = folders[target]
                os.startfile(folder_path)
                opening = self.language_manager.get_text("responses.opening_folder").format(target=target)
                chat_window.add_message(opening, is_user=False)
                
                # GUARDAR la carpeta abierta como la última carpeta de EVA
                self.processor.context.last_opened_folder = folder_path
                save_last_folder_path(folder_path)
                return True

            # ELIMINADA búsqueda aproximada - causa demoras de 15 segundos
            # Solo coincidencias exactas para velocidad máxima

            return False

        except Exception as error:
            logger.error(f"Error procesando carpeta: {error}")
            return False

    def process_website_command(self, target, chat_window, lang):
        """Abre sitios web si están configurados"""
        try:
            websites = self.config.get("paths", {}).get("websites", {})

            # Buscar coincidencia exacta primero
            if target in websites:
                webbrowser.open(websites[target])
                opening = self.language_manager.get_text("responses.opening")
                chat_window.add_message(f"{opening} {target}", is_user=False)
                return True

            # Buscar usando variantes configuradas
            matched_website = self.processor._find_command_with_variants(target, websites.keys())
            if matched_website:
                webbrowser.open(websites[matched_website])
                opening = self.language_manager.get_text("responses.opening")
                chat_window.add_message(f"{opening} {matched_website}", is_user=False)
                return True

            # Búsqueda aproximada como fallback
            result = process.extractOne(
                target, websites.keys(), scorer=fuzz.token_set_ratio
            )

            if result:
                best_match, score, _ = result
                if score > 75:
                    webbrowser.open(websites[best_match])
                    opening = self.language_manager.get_text("responses.opening")
                    approx = self.language_manager.get_text("responses.approx_match")
                    chat_window.add_message(
                        f"{opening} {best_match} ({approx})", is_user=False
                    )
                    return True

            return False
        
        except Exception as error:
            logger.error(f"Error procesando sitio web: {error}")
            return False
    
    def _get_active_folder(self):
        """
        Obtiene la carpeta activa siguiendo el nuevo orden de prioridad:
        1. Carpeta activa del explorador de Windows (NUEVA FUNCIONALIDAD)
        2. Última carpeta abierta por EVA (funcionalidad existente)
        3. Carpetas predeterminadas del sistema (fallback)
        """
        try:
            # Usar la nueva función centralizada que implementa la lógica de prioridad
            working_folder = get_working_folder()
            
            if working_folder:
                # Actualizar la última carpeta de EVA si se detectó una carpeta activa del explorador
                # Esto mantiene la sincronización entre ambos sistemas
                if working_folder != self.processor.last_opened_folder:
                    self.processor.context.last_opened_folder = working_folder
                    # Solo guardar si es diferente para evitar escrituras innecesarias
                    save_last_folder_path(working_folder)
                
                return working_folder
            
            # Fallback adicional si get_working_folder() falla
            if (self.processor.last_opened_folder and 
                os.path.isdir(self.processor.last_opened_folder)):
                return self.processor.last_opened_folder
                
            return None
            
        except Exception as e:
            logger.warning(f"Error obteniendo carpeta activa: {str(e)}")
            # Fallback de emergencia al sistema original
            try:
                if (self.processor.last_opened_folder and 
                    os.path.isdir(self.processor.last_opened_folder)):
                    return self.processor.last_opened_folder
                
                # Último recurso: carpeta del usuario
                user_home = os.path.expanduser("~")
                if os.path.isdir(user_home):
                    return user_home
                    
            except Exception as fallback_error:
                logger.error(f"Error en fallback de carpeta activa: {str(fallback_error)}")
                
            return None

    def process_file_command(self, target, chat_window, lang):
        """
        IMPLEMENTACIÓN DIRECTA DE LA LÓGICA ANTIGUA QUE FUNCIONABA.
        Sin delegación a handlers externos que pueden fallar.
        """
        try:
            logger.info(f"🔍 process_file_command llamado con target: '{target}'")
            
            # USAR LA LÓGICA EXACTA DE LA VERSIÓN ANTIGUA
            # Priorizar carpeta activa del Explorador
            active_folder = self._get_active_folder()
            if active_folder:
                self.processor.context.last_opened_folder = active_folder
                save_last_folder_path(active_folder)
                logger.info(f"📁 Usando carpeta activa: {active_folder}")
            elif self.processor.last_opened_folder:
                logger.info(f"📁 Usando última carpeta de EVA: {self.processor.last_opened_folder}")
            else:
                # Intentar cargar la última carpeta abierta
                self.processor.context.last_opened_folder = load_last_folder_path()
                if self.processor.last_opened_folder:
                    logger.info(f"📁 Usando última carpeta cargada: {self.processor.last_opened_folder}")

            if not self.processor.last_opened_folder:
                text = self.language_manager.get_text("responses.no_recent_folder")
                chat_window.add_message(text, is_user=False)
                return False

            # Obtener archivos con información completa
            files = []
            for entry in os.scandir(self.processor.last_opened_folder):
                if entry.is_file():
                    stat = entry.stat()
                    files.append({
                        'name': entry.name,
                        'creation': stat.st_ctime,
                        'modification': stat.st_mtime
                    })

            # Ordenar según el método seleccionado por el usuario
            sort_method = getattr(self.processor, 'file_sort_method', 'creation')
            if sort_method == "name":
                files.sort(key=lambda x: x['name'].lower())
            elif sort_method == "creation":
                files.sort(key=lambda x: x['creation'], reverse=True)
            elif sort_method == "modification":
                files.sort(key=lambda x: x['modification'], reverse=True)
            
            # Extraer solo los nombres para compatibilidad
            files = [f['name'] for f in files]

            if not files:
                text = self.language_manager.get_text("responses.no_files")
                chat_window.add_message(text, is_user=False)
                return False

            logger.info(f"📋 Archivos encontrados: {len(files)}")
            logger.info(f"📋 Lista de archivos: {files[:10]}")  # Mostrar primeros 10

            # LÓGICA ORIGINAL: Buscar número en el comando
            number = None

            # Buscar formato numérico directo (1, 2, 3...)
            num_match = re.search(r"\b(\d+)\b", target)
            if num_match:
                number = int(num_match.group(1))
                logger.info(f"🔢 Número encontrado: {number}")
            else:
                # Buscar formato textual (uno, dos, tres...)
                if hasattr(self.processor, 'words_to_numbers'):
                    for word in target.split():
                        if word in self.processor.words_to_numbers:
                            number = self.processor.words_to_numbers[word]
                            logger.info(f"🔢 Número textual: {word} = {number}")
                            break
                        elif (
                            word.endswith(("o", "a"))
                            and word[:-1] in self.processor.words_to_numbers
                        ):
                            number = self.processor.words_to_numbers[word[:-1]]
                            logger.info(f"🔢 Número ordinal: {word} = {number}")
                            break

            if number is not None and 1 <= number <= len(files):
                file_path = os.path.join(
                    self.processor.last_opened_folder, files[number - 1]
                )
                os.startfile(file_path)
                opening = self.language_manager.get_text("responses.opening_file")
                chat_window.add_message(
                    f"{opening} {number}: {files[number-1]}", is_user=False
                )
                logger.info(f"✅ Archivo abierto por número: {files[number-1]}")
                return True
            elif number is not None:
                not_found = self.language_manager.get_text("responses.file_not_found")
                chat_window.add_message(f"{not_found} {number}", is_user=False)
                return True

            # LÓGICA MEJORADA: buscar por parte del nombre del archivo
            if len(target.split()) > 1:  # Si hay más de una palabra en el comando
                # Extraer palabras que podrían ser parte del nombre del archivo
                keywords = [
                    word.lower()
                    for word in target.split()
                    if word.lower()
                    not in ["abre", "abrir", "archivo", "el", "la", "de", "del", "en", "y", "con"]
                ]

                logger.info(f"🔍 Palabras clave extraídas: {keywords}")
                logger.info(f"📋 Archivos disponibles: {files}")

                if keywords:
                    # ESTRATEGIA 1: Buscar archivos que contengan TODAS las palabras clave
                    matching_files = []
                    for filename in files:
                        filename_lower = filename.lower()
                        matches = 0
                        for keyword in keywords:
                            if keyword in filename_lower:
                                matches += 1
                                logger.info(f"🎯 '{keyword}' encontrado en '{filename}'")
                        
                        if matches == len(keywords):  # TODAS las palabras presentes
                            matching_files.append(filename)
                            logger.info(f"✅ Archivo con TODAS las palabras: {filename}")

                    # ESTRATEGIA 2: Si no hay coincidencias exactas, buscar parciales
                    if not matching_files:
                        logger.info("🔄 No hay coincidencias exactas, buscando parciales...")
                        partial_matches = []
                        for filename in files:
                            filename_lower = filename.lower()
                            matches = 0
                            for keyword in keywords:
                                if keyword in filename_lower:
                                    matches += 1
                            
                            if matches > 0:
                                partial_matches.append((filename, matches))
                                logger.info(f"🔍 Coincidencia parcial: {filename} ({matches}/{len(keywords)} palabras)")
                        
                        # Ordenar por número de coincidencias
                        partial_matches.sort(key=lambda x: x[1], reverse=True)
                        
                        if partial_matches:
                            best_match = partial_matches[0]
                            if best_match[1] >= len(keywords) * 0.5:  # Al menos 50% de coincidencias
                                matching_files = [best_match[0]]
                                logger.info(f"🎯 Usando mejor coincidencia parcial: {best_match[0]}")

                    if len(matching_files) == 1:
                        # Si solo hay un archivo que coincide, abrirlo
                        file_path = os.path.join(
                            self.processor.last_opened_folder, matching_files[0]
                        )
                        os.startfile(file_path)
                        opening = self.language_manager.get_text(
                            "responses.opening_file"
                        )
                        chat_window.add_message(
                            f"{opening}: {matching_files[0]}", is_user=False
                        )
                        logger.info(f"✅ Archivo único encontrado y abierto: {matching_files[0]}")
                        return True
                    elif len(matching_files) > 1:
                        # Si hay varios archivos que coinciden, mostrar los primeros 5
                        multiple = self.language_manager.get_text(
                            "responses.multiple_files"
                        )
                        chat_window.add_message(f"{multiple}:", is_user=False)
                        for i, filename in enumerate(matching_files[:5], 1):
                            chat_window.add_message(f"{i}. {filename}", is_user=False)
                        specify = self.language_manager.get_text(
                            "responses.specify_more"
                        )
                        chat_window.add_message(specify, is_user=False)
                        logger.info(f"📋 Múltiples archivos encontrados: {len(matching_files)}")
                        return True
                    else:
                        logger.warning(f"❌ No se encontraron archivos con palabras: {keywords}")
                        logger.warning(f"📋 Archivos disponibles en carpeta: {files}")

            # Si no se encontró por número ni por nombre
            logger.warning(f"❌ No se encontró archivo para: '{target}'")
            not_found = self.language_manager.get_text("responses.file_not_found")
            chat_window.add_message(f"No se encontró archivo con '{target}'. Archivos disponibles:", is_user=False)
            
            # Mostrar los primeros 5 archivos para ayudar al usuario
            for i, filename in enumerate(files[:5], 1):
                chat_window.add_message(f"{i}. {filename}", is_user=False)
            
            if len(files) > 5:
                chat_window.add_message(f"... y {len(files)-5} archivos más", is_user=False)
            
            return False
            
        except Exception as error:
            logger.error(f"Error procesando comando de archivo: {error}")
            error_text = self.language_manager.get_text("responses.file_command_error")
            chat_window.add_message(error_text, is_user=False)
            return False

    def _normalize_text(self, text):
        """Normaliza texto removiendo acentos y caracteres especiales para mejor búsqueda"""
        import unicodedata
        
        # Convertir a minúsculas
        text = text.lower()
        
        # Remover acentos y diacríticos
        text = unicodedata.normalize('NFD', text)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        
        # Reemplazos específicos para mejorar coincidencias
        replacements = {
            'ñ': 'n',
            'ç': 'c',
            'ü': 'u',
            'ß': 'ss'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text


class ReadHandler(CommandHandler):
    def can_handle(self, text: str) -> bool:
        read_keywords = self.processor.command_map.get("read", {}).get(self.lang, [])
        return any(text.lower().startswith(kw) for kw in read_keywords)

    def handle(self, text: str, chat_window) -> bool:
        self.processor.read_selected_text(chat_window)
        return True



    def _is_special_command(self, text: str) -> bool:
        """Verifica si el texto contiene un comando especial sin ejecutarlo"""
        try:
            special_commands = self.config.get("comandos_especiales", {})

            # Commands moved to system_command_handler

            # Read text command moved to ReadHandler

            # Comandos de confirmación (con valor por defecto)
            confirm_commands = sorted(
                self.config.get("confirm", ["apagar", "reiniciar", "cerrar sesion"]),
                key=len,
                reverse=True,
            )
            for cmd in confirm_commands:
                if cmd in text:
                    return True

            # Comandos de cierre
            close_commands = sorted(
                special_commands.get("cierre", []), key=len, reverse=True
            )
            for cmd in close_commands:
                if cmd in text:
                    return True

            # Comandos de captura de pantalla
            screenshot_commands = sorted(
                special_commands.get("captura", []), key=len, reverse=True
            )
            for cmd in screenshot_commands:
                if cmd in text:
                    return True

            # Comandos de MPC
            if "mpc" in special_commands:
                mpc_commands = special_commands["mpc"]
                for sub_cmd, variants in mpc_commands.items():
                    for variant in variants:
                        if variant in text:
                            return True
            
            # Comandos de Kodi
            if "kodi" in special_commands:
                kodi_commands = special_commands["kodi"]
                for sub_cmd, variants in kodi_commands.items():
                    for variant in variants:
                        if variant in text:
                            return True
            
            # Comandos de VLC
            if "vlc" in special_commands:
                vlc_commands = special_commands["vlc"]
                for sub_cmd, variants in vlc_commands.items():
                    for variant in variants:
                        if variant in text:
                            return True

            # Comandos de hotkey (simulados)
            if text.startswith("hotkey:"):
                return True

            return False
        
        except Exception as error:
            logger.error(f"Error verificando comando especial: {error}")
            return False
    
    def execute_special_command(self, text, chat_window):
        try:
            # Acceso seguro a comandos_especiales
            special_commands = self.config.get("comandos_especiales", {})

            # Commands moved to system_command_handler

            # Comandos de confirmación (con valor por defecto)
            confirm_commands = sorted(
                self.config.get("confirm", ["apagar", "reiniciar", "cerrar sesion"]),
                key=len,
                reverse=True,
            )
            for cmd in confirm_commands:
                if cmd in text:
                    self.processor.pending_command = cmd
                    if cmd == "apagar" and "minutos" in text:
                        numbers_in_text = [
                            self.processor.convert_text_to_number(word)
                            for word in text.split()
                        ]
                        numeric_minutes = next(
                            (n for n in numbers_in_text if n is not None and n > 0), 0
                        )
                        self.processor.wait_time = numeric_minutes

                    processing = random.choice(self.config["frases_transicion"])
                    confirm_text = self.language_manager.get_text(
                        "responses.confirm_action"
                    )
                    chat_window.add_message(
                        f"{processing} {confirm_text.format(action=cmd)}", is_user=False
                    )
                    return True

            # Comandos de cierre
            close_commands = sorted(
                special_commands.get("cierre", []), key=len, reverse=True
            )
            for cmd in close_commands:
                if cmd in text:
                    closing_eva = self.language_manager.get_text(
                        "responses.closing_eva"
                    )
                    chat_window.add_message(closing_eva, is_user=False)
                    QApplication.quit()
                    return True

            # Comandos de captura de pantalla
            screenshot_commands = sorted(
                special_commands.get("captura", []), key=len, reverse=True
            )
            for cmd in screenshot_commands:
                if cmd in text:
                    taking_screenshot = self.language_manager.get_text(
                        "responses.taking_screenshot"
                    )
                    chat_window.add_message(taking_screenshot, is_user=False)
                    if HAS_PYAUTOGUI:
                        pyautogui.hotkey("win", "shift", "s")
                    else:
                        # Fallback nativo: Win+Shift+S via ctypes
                        ctypes.windll.user32.keybd_event(0x5B, 0, 0, 0)  # Win down
                        ctypes.windll.user32.keybd_event(0xA0, 0, 0, 0)  # Shift down
                        ctypes.windll.user32.keybd_event(0x53, 0, 0, 0)  # S down
                        ctypes.windll.user32.keybd_event(0x53, 0, 0x0002, 0)  # S up
                        ctypes.windll.user32.keybd_event(0xA0, 0, 0x0002, 0)  # Shift up
                        ctypes.windll.user32.keybd_event(0x5B, 0, 0x0002, 0)  # Win up
                    return True

            # MULTIMEDIA COMMANDS REMOVED - Now handled by MultimediaCommandHandler with higher priority

            # Comandos de hotkey (simulados)
            if text.startswith("hotkey:"):
                command_key = text.split(":")[1]
                # Buscar en todos los tipos de comandos especiales
                for category, commands in special_commands.items():
                    # Comandos simples
                    if isinstance(commands, list) and command_key in commands:
                        # Ejecutar la acción correspondiente
                        if category == "leer_texto":
                            self.processor.read_selected_text(chat_window)
                            return True
                        elif category == "show_chat":
                            chat_window.show()
                            return True
                        # ... otros comandos simples ...

                    # Comandos anidados - multimedia now handled by MultimediaCommandHandler
                    elif isinstance(commands, dict):
                        for sub_cmd, variants in commands.items():
                            if isinstance(variants, list) and command_key in variants:
                                # Multimedia commands now handled by MultimediaCommandHandler
                                if category in ["mpc", "kodi", "vlc"]:
                                    # Let MultimediaCommandHandler handle these
                                    return False
                return False

            return False
        
        except Exception as error:
            logger.error(f"Error ejecutando comando especial: {error}")
            return False
    
    # MULTIMEDIA METHODS REMOVED - Now using MultimediaCommandHandler


# FILE ORDER HANDLER REMOVED - Now using FileCommandHandler


# VoiceSystemCommandHandler REMOVED - Panel buttons handle voice control



class DictationCommandHandler(CommandHandler):
    """Manejador de comandos de dictado inteligente"""
    
    def can_handle(self, text: str) -> bool:
        # Usar command_map centralizado para comandos de dictado
        dictation_keywords = self.processor.command_map.get("dictation", {}).get(self.lang, [])
        text_lower = text.lower().strip()
        
        # Verificar coincidencias exactas y parciales
        return any(keyword in text_lower for keyword in dictation_keywords)
    
    def handle(self, text: str, chat_window) -> bool:
        try:
            # Mostrar mensaje de inicio
            start_msg = self.language_manager.get_text("responses.dictation_starting")
            chat_window.add_message(start_msg, is_user=False)
            
            # Importar y ejecutar el sistema de dictado
            try:
                import sys
                import os
                
                # Asegurar que el directorio EVA esté en el path
                eva_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                if eva_path not in sys.path:
                    sys.path.insert(0, eva_path)
                
                from voice.dictation_intelligent import start_dictation
                
                # Configurar dictado con el idioma actual
                config = {
                    "language": self.lang,
                    "eva_instance": self.processor.eva,
                    "tts": {"enabled": True}
                }
                
                # Iniciar dictado en hilo separado para no bloquear la UI
                submit_background_task(
                    self._start_dictation_async,
                    config, chat_window,
                    name="start_dictation"
                )
                
                return True
                
            except ImportError as e:
                logger.info(f"Módulo de dictado no disponible en modo gratuito: {str(e)}")
                info_msg = self.language_manager.get_text("responses.dictation_unavailable")
                chat_window.add_message(info_msg, is_user=False)
                return True
                
        except Exception as e:
            logger.error(f"Error en comando de dictado: {str(e)}")
            error_msg = self.language_manager.get_text("responses.dictation_error")
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _start_dictation_async(self, config, chat_window):
        """Inicia el dictado integrado al chat - VERSIÓN MEJORADA"""
        try:
            start_msg = self.language_manager.get_text("responses.dictation_started")
            instructions = self.language_manager.get_text("responses.dictation_instructions")
            
            # Mostrar inicio
            if hasattr(chat_window, 'update_message_signal'):
                chat_window.update_message_signal.emit(start_msg, False)
                chat_window.update_message_signal.emit(instructions, False)
            else:
                try:
                    chat_window.add_message(start_msg, is_user=False)
                    chat_window.add_message(instructions, is_user=False)
                except Exception as e:
                    logger.error(f"Error actualizando UI: {e}")
            
            # Activar modo dictado mejorado
            self.processor.dictation_mode = True
            self.processor.dictation_text = ""
            self.processor.dictation_chat_window = chat_window
            
            # Inicializar corrector gramatical si está disponible
            self._init_grammar_corrector()
            
            logger.info("🎤 Modo dictado mejorado activado")
                    
        except Exception as e:
            logger.error(f"Error en dictado simple: {str(e)}")
            error_msg = self.language_manager.get_text("responses.dictation_simple_error")
            
            try:
                if hasattr(chat_window, 'update_message_signal'):
                    chat_window.update_message_signal.emit(error_msg, False)
                else:
                    chat_window.add_message(error_msg, is_user=False)
            except Exception as e:
                logger.error(f"Error crítico: No se pudo mostrar mensaje de error en UI: {e}")


# SystemVolumeHandler ELIMINADO - Ahora usa SystemCommandHandler unificado


# FolderDebugHandler REMOVED - Debug functionality not needed for end users


class UpdateCommandHandler(CommandHandler):
    """Manejador de comandos relacionados con actualizaciones"""
    
    def can_handle(self, text: str) -> bool:
        update_keywords = {
            "es": [
                "verificar actualizaciones", "buscar actualizaciones", "comprobar actualizaciones",
                "actualizar eva", "nueva versión", "actualización disponible",
                "check updates", "buscar updates", "hay actualizaciones"
            ],
            "en": [
                "check updates", "check for updates", "update eva", "new version",
                "update available", "verify updates"
            ]
        }
        
        keywords = update_keywords.get(self.lang, [])
        text_lower = text.lower()
        
        return any(keyword in text_lower for keyword in keywords)
    
    def handle(self, text: str, chat_window) -> bool:
        try:
            # Verificar si EVA tiene el sistema de actualizaciones
            if not (self.processor.eva and hasattr(self.processor.eva, 'update_manager')):
                error_msg = "Sistema de actualizaciones no disponible"
                chat_window.add_message(error_msg, is_user=False)
                return True
            
            # Determinar el tipo de verificación
            text_lower = text.lower()
            
            if any(word in text_lower for word in ["manual", "ahora", "now", "forzar"]):
                # Verificación manual inmediata
                self._handle_manual_check(chat_window)
            else:
                # Verificación normal
                self._handle_normal_check(chat_window)
            
            return True
            
        except Exception as e:
            logger.error(f"Error en comando de actualización: {str(e)}")
            error_msg = "Error verificando actualizaciones"
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _handle_manual_check(self, chat_window):
        """Maneja verificación manual de actualizaciones"""
        try:
            # Mostrar mensaje de verificación
            checking_msg = "🔍 Verificando actualizaciones manualmente..."
            chat_window.add_message(checking_msg, is_user=False)
            
            # Llamar al método de verificación manual de EVA
            self.processor.eva.check_updates_manually()
            
        except Exception as e:
            logger.error(f"Error en verificación manual: {str(e)}")
            error_msg = "Error en verificación manual de actualizaciones"
            chat_window.add_message(error_msg, is_user=False)
    
    def _handle_normal_check(self, chat_window):
        """Maneja verificación normal de actualizaciones"""
        try:
            update_manager = self.processor.eva.update_manager
            
            # Verificar última verificación
            last_check = update_manager.get_last_check_time()
            
            if last_check:
                from datetime import datetime, timedelta
                time_since_check = datetime.now() - last_check
                
                if time_since_check < timedelta(hours=1):
                    # Verificación reciente
                    minutes_ago = int(time_since_check.total_seconds() / 60)
                    recent_msg = f"✅ Última verificación hace {minutes_ago} minutos. Sin actualizaciones disponibles."
                    chat_window.add_message(recent_msg, is_user=False)
                    return
            
            # Verificar actualizaciones
            checking_msg = "🔍 Verificando actualizaciones..."
            chat_window.add_message(checking_msg, is_user=False)
            
            # Iniciar verificación
            update_manager.check_for_updates(silent=False)
            
        except Exception as e:
            logger.error(f"Error en verificación normal: {str(e)}")
            error_msg = "Error verificando actualizaciones"
            chat_window.add_message(error_msg, is_user=False)


class DocumentHandler(CommandHandler):
    def __init__(self, processor: "CommandProcessor"):
        super().__init__(processor)
        # Añadir soporte para ODT
        self.supported_formats = [".pdf", ".txt", ".md", ".csv", ".json", ".docx", ".odt"]
        # COMANDOS ESPECÍFICOS PARA EVITAR CONFUSIÓN
        self.document_commands = {
            "es": ["resume"],  # Solo "resume [nombre_archivo]"
            "en": ["resume"]   # Solo "resume [filename]"
        }

    def can_handle(self, text: str) -> bool:
        # DETECCIÓN ESPECÍFICA Y ROBUSTA - Solo "resume [archivo]"
        text_lower = text.lower().strip()
        
        # SOLO reconocer comandos que empiecen con "resume"
        words = text_lower.split()
        
        # Debe empezar con "resume" y tener al menos 2 palabras
        if len(words) >= 2 and words[0] == "resume":
            logger.info(f"🔍 DocumentHandler.can_handle('{text}') = True")
            return True
        
        logger.info(f"🔍 DocumentHandler.can_handle('{text}') = False")
        return False


    def handle(self, text: str, chat_window) -> bool:
        try:
            # Obtener archivo seleccionado o reciente
            file_path = self._get_target_file(text)
            if not file_path:
                # Extraer nombre de archivo del comando para mensaje más específico
                import re
                filename_found = None
                for ext in self.supported_formats:
                    pattern = r'([a-zA-Z0-9\s_-]+\.' + ext[1:] + r')'
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        filename_found = match.group(1).strip()
                        break
                
                if filename_found:
                    error_msg = f"No pude encontrar el archivo '{filename_found}' en la carpeta actual. 💡 Puedes usar el botón 📁 del chat para seleccionar el archivo que quieres que analice."
                else:
                    error_msg = "No especificaste qué archivo quieres que analice. 💡 Puedes usar el botón 📁 del chat para seleccionar el documento o decirme 'resume archivo.pdf'."
                
                self.safe_add_message(chat_window, error_msg)
                return True
                
            # Verificar formato soportado usando el método correcto
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in self.supported_formats:
                formats = ", ".join(self.supported_formats)
                self.safe_add_message(chat_window, f"❌ No puedo analizar archivos '{file_ext}'. 💡 Formatos que sí puedo leer: {formats}")
                return True

            # Validar tamaño del archivo antes de procesarlo
            is_valid_size, size_error = self._validate_file_size(file_path)
            if not is_valid_size:
                self.safe_add_message(chat_window, f"❌ {size_error} 💡 Intenta con un archivo más pequeño o divídelo en partes.")
                return True

            # Procesar documento en segundo plano
            submit_background_task(
                self.process_document, 
                file_path, chat_window,
                name="process_document"
            )
            return True
        except Exception as e:
            logger.error(f"Error procesando documento: {str(e)}")
            self.safe_add_message(chat_window, "Error procesando documento")
            return True

    def safe_add_message(self, chat_window, message):
        """Añade mensajes de forma segura"""
        if hasattr(chat_window, 'update_message_signal'):
            chat_window.update_message_signal.emit(message, False)
        else:
            try:
                chat_window.add_message(message, is_user=False)
            except Exception as e:
                logger.error(f"Error crítico al añadir mensaje: {e}")

    def _validate_file_size(self, file_path, max_mb=50):
        """Valida que el archivo no sea demasiado grande"""
        try:
            size_bytes = os.path.getsize(file_path)
            size_mb = size_bytes / (1024 * 1024)
            
            if size_mb > max_mb:
                return False, f"Archivo muy grande ({size_mb:.1f}MB). Máximo permitido: {max_mb}MB"
            
            logger.info(f"📄 Archivo validado: {size_mb:.1f}MB (dentro del límite de {max_mb}MB)")
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validando tamaño de archivo: {str(e)}")
            return False, "No se pudo verificar el tamaño del archivo"

    def _smart_truncate(self, text, max_chars=25000):
        """Trunca texto de forma inteligente por párrafos completos"""
        if len(text) <= max_chars:
            return text
        
        # Buscar el último párrafo completo dentro del límite
        truncated = text[:max_chars]
        
        # Intentar cortar por párrafo (doble salto de línea)
        last_paragraph = truncated.rfind('\n\n')
        if last_paragraph > max_chars * 0.8:  # Si está cerca del límite (80%)
            result = text[:last_paragraph]
            logger.info(f"📄 Texto truncado por párrafo en {last_paragraph} caracteres")
            return result + "\n\n📄 *Documento extenso, analizando sección principal...*"
        
        # Si no hay párrafos, intentar cortar por oración
        last_sentence = truncated.rfind('. ')
        if last_sentence > max_chars * 0.9:  # Si está muy cerca del límite (90%)
            result = text[:last_sentence + 1]
            logger.info(f"📄 Texto truncado por oración en {last_sentence + 1} caracteres")
            return result + "\n\n📄 *Documento extenso, analizando sección principal...*"
        
        # Fallback: corte simple con mensaje
        logger.info(f"📄 Texto truncado simple en {max_chars} caracteres")
        return truncated + "\n\n📄 *Documento extenso, analizando sección principal...*"

    def _get_target_file(self, text):
        """Obtiene el archivo objetivo basado en el comando incluyendo nombres de archivo"""
        # PRIORIDAD 1: Archivo establecido por botón 📁 (drag-and-drop o file selector)
        if hasattr(self, 'target_file_path') and self.target_file_path:
            file_path = self.target_file_path
            logger.info(f"📄 Usando archivo seleccionado por botón: {os.path.basename(file_path)}")
            # NO resetear aquí - mantener para múltiples comandos
            return file_path
        
        # PRIORIDAD 2: Buscar archivo mencionado en el comando
        # Primero intentar con ventana enfocada, luego carpeta de trabajo
        from utils.file_utils import get_working_folder, get_active_explorer_folder
        
        # Intentar obtener carpeta de ventana enfocada primero
        focused_folder = get_active_explorer_folder()
        working_folder = get_working_folder()
        
        # Usar ventana enfocada si está disponible, sino usar carpeta de trabajo
        target_folder = focused_folder if focused_folder else working_folder
        
        if not target_folder:
            logger.warning("📄 No se pudo obtener carpeta objetivo (ni ventana enfocada ni carpeta de trabajo)")
            return None
        
        folder_source = "ventana enfocada" if focused_folder else "carpeta de trabajo"
        logger.info(f"📄 Carpeta objetivo ({folder_source}): {target_folder}")
        
        # Extraer nombre de archivo del comando
        import re
        logger.info(f"📄 Comando completo recibido: '{text}'")
        
        for ext in self.supported_formats:
            # Patrón para nombres con espacios: "eva.pdf", "Eva Readme Bilingual.pdf"
            pattern = r'([a-zA-Z0-9\s_-]+\.' + ext[1:] + r')'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                filename = match.group(1).strip()
                logger.info(f"📄 Archivo extraído del comando: '{filename}'")
                logger.info(f"📄 Buscando '{filename}' en carpeta objetivo: {target_folder}")
                
                # Buscar en la carpeta objetivo (ventana enfocada o carpeta de trabajo)
                full_path = os.path.join(target_folder, filename)
                logger.info(f"📄 Ruta completa a verificar: {full_path}")
                
                if os.path.exists(full_path):
                    logger.info(f"📄 ✅ Archivo encontrado: {full_path}")
                    return full_path
                else:
                    logger.warning(f"📄 ❌ Archivo no existe en: {full_path}")
                
                # Buscar case-insensitive en la carpeta objetivo
                try:
                    files_in_folder = os.listdir(target_folder)
                    logger.info(f"📄 Archivos en carpeta: {files_in_folder}")
                    
                    for file in files_in_folder:
                        if file.lower() == filename.lower():
                            full_path = os.path.join(target_folder, file)
                            logger.info(f"📄 Archivo encontrado (case-insensitive): {full_path}")
                            return full_path
                except (PermissionError, OSError) as e:
                    logger.error(f"📄 Error accediendo a carpeta {target_folder}: {e}")
                
                logger.warning(f"📄 Archivo '{filename}' no encontrado en carpeta objetivo: {target_folder}")
                logger.warning(f"📄 Archivos disponibles: {files_in_folder if 'files_in_folder' in locals() else 'No se pudo listar'}")
                return None
        
        # Si no se encontró archivo específico, continuar con lógica original
            
        # NO extraer extensión del comando - será detectada automáticamente
        self.target_extension = None
        
        # Extraer parte relevante del comando
        doc_keywords = self.document_keywords[self.lang]
        lower_text = text.lower()
        candidate_name = text
        
        # Buscar la primera palabra clave y extraer el resto del comando
        for kw in doc_keywords:
            if kw in lower_text:
                start_idx = lower_text.find(kw) + len(kw)
                candidate_name = text[start_idx:].strip()
                break
        
        # Limpiar palabras comunes que no son parte del nombre
        stop_words = ["el", "la", "los", "las", "de", "del", "archivo", "documento", "file", "document"]
        words = [word for word in candidate_name.split() if word.lower() not in stop_words]
        candidate_name = " ".join(words) if words else candidate_name
        
        # Usar el sistema de detección de carpeta activa (ventana enfocada o carpeta de trabajo)
        # Reutilizar la lógica ya implementada arriba
        active_folder = target_folder
        if not active_folder:
            return None
        
        # Actualizar la carpeta de trabajo del procesador solo si es diferente
        if active_folder != self.processor.last_opened_folder:
            self.processor.last_opened_folder = active_folder
            save_last_folder_path(active_folder)

        # 1. Si no hay nombre específico, buscar el documento más reciente
        if not candidate_name.strip() or len(candidate_name.split()) < 1:
            return self._get_most_recent_document(active_folder)
        
        # 2. Buscar coincidencia exacta en el nombre del archivo (sin extensión)
        for root, _, files in os.walk(active_folder):
            for file in files:
                # Filtrar por formatos soportados
                if any(file.lower().endswith(ext) for ext in self.supported_formats):
                    file_path = os.path.join(root, file)
                    file_name_no_ext = os.path.splitext(file)[0].lower()
                    # Verificar si el nombre coincide exactamente (sin extensión)
                    if candidate_name.lower() == file_name_no_ext:
                        return file_path
        
        # 3. Si no se encontró coincidencia exacta, buscar en subcarpetas
        all_files = []
        for root, _, files in os.walk(active_folder):
            for file in files:
                # Filtrar por formatos soportados
                if any(file.lower().endswith(ext) for ext in self.supported_formats):
                    all_files.append(os.path.join(root, file))
        
        if not all_files:
            return None

        # Extraer palabras clave del comando
        words = [
            word.lower() 
            for word in candidate_name.split() 
            if word.lower() not in doc_keywords and len(word) > 3
        ]
        
        # Buscar el archivo más relevante
        best_match = None
        best_score = 0
        
        for file_path in all_files:
            file_name = os.path.basename(file_path).lower()
            
            # Calcular puntaje de coincidencia
            score = 0
            for word in words:
                if word in file_name:
                    score += 85  # Alta prioridad si la palabra está en el nombre
                elif fuzz.partial_ratio(word, file_name) > 80:
                    score += 70
                    
            # Priorizar archivos recientes
            try:
                mtime = os.path.getmtime(file_path)
                score += mtime / 10_000_000  # A\u00f1adir peque\u00f1o bonus por reciente
            except OSError:
                pass
            
            if score > best_score:
                best_score = score
                best_match = file_path
                
        # 4. Si no encontramos coincidencia, usar el archivo más reciente
        if best_match is None and all_files:
            return self._get_most_recent_document(active_folder)
                
        return best_match
    
    def _get_most_recent_document(self, folder_path):
        """Obtiene el documento más reciente de la carpeta"""
        try:
            all_files = []
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in self.supported_formats):
                        file_path = os.path.join(root, file)
                        all_files.append(file_path)
            
            if all_files:
                # Ordenar por fecha de modificación (más reciente primero)
                all_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
                return all_files[0]
            return None
        except Exception as e:
            logger.error(f"Error obteniendo documento más reciente: {str(e)}")
            return None

    def process_document(self, file_path, chat_window):
        """Procesa el documento y genera resumen con Ollama"""
        try:
            # Verificar si el archivo existe
            if not os.path.exists(file_path):
                error_msg = f"Archivo no encontrado: {os.path.basename(file_path)}"
                self.safe_add_message(chat_window, error_msg)
                return
                
            # Mostrar mensaje de procesamiento usando señal segura
            self.safe_add_message(chat_window, "📄 Analizando tu documento, esto puede tomar unos momentos...")
            
            # Extraer texto del documento
            text_content = self.extract_text(file_path)
            
            if not text_content.strip():
                self.safe_add_message(chat_window, "❌ No pude leer el contenido de este documento. Verifica que no esté dañado o protegido con contraseña.")
                return

            # Limitar tamaño para no sobrecargar a Ollama (25,000 caracteres - mejorado)
            max_chars = 25000
            if len(text_content) > max_chars:
                text_content = self._smart_truncate(text_content, max_chars)
                
            # Crear prompt mejorado para resumen
            prompt = f"""Eres un asistente especializado en resumir documentos. Tu tarea es crear un resumen conciso y claro del siguiente documento.

INSTRUCCIONES:
- Resume ÚNICAMENTE el contenido del documento proporcionado
- Mantén el resumen entre 3-5 puntos principales
- Usa un lenguaje claro y directo
- NO incluyas información externa o ejemplos no relacionados

DOCUMENTO A RESUMIR:
{text_content}

RESUMEN:"""
            
            # Mostrar mensaje de que se está generando el resumen
            self.safe_add_message(chat_window, "🤖 Generando resumen inteligente...")
            
            # Verificar que el proveedor de IA esté disponible
            if self.processor.ai_provider is None:
                self.safe_add_message(chat_window, "❌ El motor de IA no está disponible. Instala Ollama o configura OpenRouter en Ajustes.")
                return

            response = self.processor.ai_provider.generate_response([{"role": "user", "content": prompt}])
            
            # Limpiar respuesta de posibles artefactos
            cleaned_response = self.clean_ollama_response(response)
            
            # Mostrar resultado usando señal segura
            self.safe_add_message(chat_window, f"📋 **Resumen del documento:**\n\n{cleaned_response}")
            
            # Sintetizar voz en el hilo principal
            QTimer.singleShot(0, lambda: self.speak(cleaned_response))
        except Exception as e:
            logger.error(f"Error procesando documento: {str(e)}")
            self.safe_add_message(chat_window, "❌ Hubo un problema generando el resumen. Intenta con otro documento o verifica tu conexión.")

    def clean_ollama_response(self, response):
        """Limpia la respuesta de Ollama de artefactos y contenido no relacionado"""
        try:
            if not response:
                return "No se pudo generar resumen"
            
            # Eliminar caracteres de escape Unicode mal formateados
            cleaned = response.replace('\\u00', '')
            
            # Buscar y eliminar contenido que parece ser de otros contextos
            # Patrones comunes de contaminación
            contamination_patterns = [
                r'# query:.*?# response:',  # Patrones de query/response
                r'```python.*?```',         # Bloques de código Python
                r'def \w+\(.*?\):.*?return', # Definiciones de funciones
                r'Certainly!.*?Below is',   # Respuestas en inglés típicas
                r'Here.*?function.*?which', # Explicaciones de funciones
            ]
            
            import re
            for pattern in contamination_patterns:
                cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
            
            # Limpiar espacios múltiples y saltos de línea excesivos
            cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)
            cleaned = re.sub(r' +', ' ', cleaned)
            
            # Si la respuesta está muy corrupta, devolver mensaje genérico
            if len(cleaned.strip()) < 20 or 'calculate_average' in cleaned:
                return "El documento ha sido procesado, pero no se pudo generar un resumen claro debido a problemas en el modelo."
            
            return cleaned.strip()
            
        except Exception as e:
            logger.error(f"Error limpiando respuesta de Ollama: {str(e)}")
            return "Error procesando la respuesta del modelo"

    def extract_text(self, file_path):
        """Extrae texto de diferentes formatos de archivo"""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == ".pdf":
                return self.extract_pdf(file_path)
            elif ext in [".txt", ".md"]:
                return self.extract_txt(file_path)
            elif ext == ".csv":
                return self.extract_csv(file_path)
            elif ext == ".json":
                return self.extract_json(file_path)
            elif ext == ".docx":
                return self.extract_docx(file_path)
            elif ext == ".odt":
                return self.extract_odt(file_path)  # Nuevo soporte para ODT
            else:
                return ""
        except Exception as e:
            logger.error(f"Error extrayendo texto de {file_path}: {str(e)}")
            return ""

    def extract_pdf(self, file_path):
        """Extrae texto de PDF usando PyMuPDF (más robusto)"""
        try:
            import fitz  # PyMuPDF
            text = ""
            with fitz.open(file_path) as doc:
                for page in doc:
                    text += page.get_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extrayendo PDF: {str(e)}")
            return ""

    def extract_txt(self, file_path):
        """Lee archivos de texto plano"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error leyendo archivo de texto: {str(e)}")
            return ""

    def extract_csv(self, file_path):
        """Convierte CSV a texto legible"""
        try:
            import csv
            text = ""
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    text += ", ".join(row) + "\n"
            return text
        except Exception as e:
            logger.error(f"Error procesando CSV: {str(e)}")
            return ""

    def extract_json(self, file_path):
        """Convierte JSON a texto estructurado"""
        try:
            import json
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return json.dumps(data, indent=2)
        except Exception as e:
            logger.error(f"Error procesando JSON: {str(e)}")
            return ""

    def extract_docx(self, file_path):
        """Extrae texto de documentos Word"""
        try:
            from docx import Document
            doc = Document(file_path)
            return "\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            logger.error(f"Error extrayendo DOCX: {str(e)}")
            return ""
            
    def extract_odt(self, file_path):
        """Extrae texto de archivos ODT usando odfpy"""
        try:
            from odf import text, teletype
            from odf.opendocument import load
            
            doc = load(file_path)
            text_content = []
            
            # Recorrer todos los elementos de texto
            for element in doc.getElementsByType(text.P):
                text_content.append(teletype.extractText(element))
            
            # Agregar texto de encabezados (todos los niveles)
            for element in doc.getElementsByType(text.H):
                text_content.append(teletype.extractText(element))
            
            return '\n'.join(text_content)
        except Exception as e:
            logger.error(f"Error extrayendo ODT: {str(e)}")
            return ""


# ====================
# REFACTORED PROCESSOR
# ====================
class CommandProcessor:
    def __init__(self, config, session_manager, language_manager):
        self.config = config
        self.session_manager = session_manager
        self.language_manager = language_manager
        logger.info("Constructor CommandProcessor iniciado")

        self.user_name = "Usuario"
        self.words_to_numbers = self._init_words_to_numbers()
        self.eva = None

        # Context manager (folder state, sorting)
        self.context = ContextManager(config, language_manager)

        # Estado para dictado mejorado
        self.dictation_mode = False
        self.dictation_text = ""

        try:
            self.ollama = OllamaIntegration(self.config)
            logger.info("Ollama Integration inicializado correctamente")
        except Exception as e:
            logger.error(f"No se pudo inicializar Ollama: {str(e)}")
            self.ollama = None

        # Inicializar AI Provider (Ollama u OpenRouter)
        self.ai_provider = self._init_ai_provider()

        logger.info("CommandProcessor inicializado")

        # Cargar configuración de instalación
        self.install_config = {}
        if os.path.exists("config/install_config.json"):
            with open("config/install_config.json") as f:
                self.install_config = json.load(f)

        # Backward compat aliases (properties handle dynamic delegation to self.context)

        logger.info(
            f"Modelos instalados: {self.install_config.get('installed_models', [])}"
        )

        # Mapa de comandos bilingüe
        self.command_map = self._init_command_map()

        # Sistema de Factory para comandos (Fase 3)
        try:
            from commands.command_factory import CommandFactory
            self.command_factory = CommandFactory(self)
        except ImportError:
            logger.warning("CommandFactory no disponible, continuando sin él")
            self.command_factory = None
        
        # Initialize command handlers
        self.model_handler = ModelSelectionHandler(self)
        self.conversation_handler = ConversationHandler(self)
        self.open_handler = OpenHandler(self)
        self.read_handler = ReadHandler(self)
        # self.system_handler = SystemCommandHandler(self) # REMOVED - Using system_command_handler instead
        self.document_handler = DocumentHandler(self)
        self.search_handler = SearchCommandHandler(self)
        # file_order_handler REMOVED - Now using FileCommandHandler

        # Handler de citas simple (NUEVO SISTEMA ÚNICO)
        from .simple_cita_handler import SimpleCitaHandler
        self.simple_cita_handler = SimpleCitaHandler(self)
        
        # MemoryCleanupHandler REMOVED - Automatic memory management preserved in utils/vram_manager.py
        
        # Handler de volumen del sistema

        
        # Handler de actualizaciones
        self.update_handler = UpdateCommandHandler(self)
        
        # Handler de VRAM
        # IntelligentOllamaCommandHandler REMOVED - Automatic functions preserved, user commands eliminated
        
        # VRAM handler REMOVED - User commands eliminated, automatic functions preserved in intelligent_ollama_handler
        
        # Handler de dictado inteligente
        self.dictation_handler = DictationCommandHandler(self)
        
        # Handler del sistema de voz
        # self.voice_system_handler = VoiceSystemCommandHandler(self) # REMOVED - Panel buttons handle voice control
        
        # Handler de debugging de carpetas
        # self.folder_debug_handler = FolderDebugHandler(self) # REMOVED - Debug functionality not needed
        
        # WindowsControlHandler ELIMINADO - Now using WindowsCommandHandler
        
        # Handler del sistema de ayuda UNIFICADO (NUEVO)
        from .help_commands import HelpCommandHandler
        self.help_command_handler = HelpCommandHandler(self)
        
        # Sistema de calendario eliminado - ahora usa simple_cita_handler
        
        # NUEVO SISTEMA LIMPIO - Comandos de sistema unificados
        self.system_command_handler = SystemCommandHandler(self)
        
        # NUEVO SISTEMA LIMPIO - Comandos multimedia unificados
        self.multimedia_command_handler = MultimediaCommandHandler(self)
        
        # NUEVO SISTEMA LIMPIO - Comandos de archivos unificados
        self.file_command_handler = FileCommandHandler(self)
        
        # NUEVO SISTEMA LIMPIO - Comandos de Windows unificados
        self.windows_command_handler = WindowsCommandHandler(self)
        
        # ⚡ ORDEN CORREGIDO: ModelSelectionHandler antes que HelpCommandHandler
        self.handlers = [
            self.system_command_handler,      # 1. Comandos de sistema
            self.multimedia_command_handler,  # 2. Multimedia
            self.file_command_handler,        # 3. Archivos
            self.windows_command_handler,     # 4. Windows
            self.dictation_handler,          # 5. Dictado
            self.simple_cita_handler,        # 6. Citas
            self.document_handler,           # 7. Documentos
            self.model_handler,              # 8. SELECCIÓN DE MODELO (antes que ayuda)
            self.help_command_handler,       # 9. Ayuda (después de modelo)
            self.conversation_handler,       # 10. Conversación
            self.open_handler,               # 11. Abrir
            self.read_handler,               # 12. Leer
            self.search_handler,             # 13. Búsqueda
            self.update_handler              # 14. Actualizaciones
        ]

        # Configurar CommandDispatcher con handlers y middleware
        self.dispatcher = CommandDispatcher(self.config, self.language_manager, self.session_manager, self.eva)
        self.dispatcher._processor_ref = self
        self.dispatcher.handlers = self.handlers

        # Backward compat: pending command delegation
        self.pending_command = self.dispatcher.pending_command
        self.wait_time = self.dispatcher.wait_time
        
        # Integrar sistema bilingüe DESPUÉS de inicializar handlers
        self._integrate_bilingual_system()

    def _integrate_bilingual_system(self):
        """Integra el sistema bilingüe unificado"""
        try:
            self.bilingual_system = None
            logger.info("Sistema bilingüe integrado en EVA core")
        except ImportError as e:
            logger.info(f"Sistema bilingüe no disponible: {e}")
            self.bilingual_system = None
        except Exception as e:
            logger.error(f"Error integrando sistema bilingüe: {e}")
            self.bilingual_system = None

    def _find_command_with_variants(self, target, available_commands):
        """Busca un comando usando el sistema de variantes configurado."""
        return self.dispatcher.find_command_with_variants(target, available_commands)

    def _init_command_map(self):
        """Inicializa el mapa de comandos bilingüe"""
        return {
            "open": {"es": ["abre"], "en": ["open"]},
            "search": {"es": ["busca"], "en": ["search"]},
            "read": {"es": ["lee"], "en": ["read"]},
            "close": {"es": ["cierra"], "en": ["close"]},
            "model": {"es": ["modelo"], "en": ["model"]},
            "premium": {"es": ["premium"], "en": ["premium"]},
            "help": {"es": ["ayuda"], "en": ["help"]},
            "dictation": {"es": ["dictado"], "en": ["dictation"]},
            "volume": {"es": ["volumen"], "en": ["volume"]},
            "wifi": {"es": ["wifi"], "en": ["wifi"]},
            "files": {"es": ["ordena archivos"], "en": ["sort files"]},
            "appointment": {"es": ["cita"], "en": ["appointment"]},
            "appointments": {"es": ["citas"], "en": ["appointments"]},
            "exit_eva": {"es": ["salir"], "en": ["exit"]},
            "shutdown": {"es": ["apagar"], "en": ["shutdown"]},
            "restart": {"es": ["reiniciar"], "en": ["restart"]},
            "logout": {"es": ["cerrar sesion"], "en": ["logout"]}
        }

    def _init_ai_provider(self) -> AIProvider:
        provider_type = self.config.get("ai_provider", "ollama")
        if provider_type == "openrouter":
            api_key = self.config.get("openrouter", {}).get("api_key", "")
            if not api_key:
                logger.warning("OpenRouter seleccionado pero sin API key. Usando Ollama como fallback.")
                return OllamaProvider(self.ollama) if self.ollama else None
            model = self.config.get("openrouter", {}).get("model", "openrouter/free")
            logger.info(f"Usando OpenRouter con modelo: {model}")
            return OpenRouterProvider(api_key, model)
        else:
            return OllamaProvider(self.ollama) if self.ollama else None

    def _update_ai_provider(self, provider_type: str, model_name: str = None):
        """Cambia el proveedor activo en tiempo real."""
        if provider_type == "openrouter":
            api_key = self.config.get("openrouter", {}).get("api_key", "")
            if not api_key:
                logger.warning("No hay API key de OpenRouter configurada")
                return False
            if model_name is None:
                model_name = self.config.get("openrouter", {}).get("model", "openrouter/free")
            self.ai_provider = OpenRouterProvider(api_key, model_name)
            self.config["ai_provider"] = "openrouter"
            self.config["openrouter"]["model"] = model_name
            logger.info(f"Proveedor cambiado a OpenRouter, modelo: {model_name}")
        else:
            if self.ollama is None:
                logger.warning("Ollama no disponible")
                return False
            self.ai_provider = OllamaProvider(self.ollama)
            if model_name:
                self.ollama.change_model(model_name)
            self.config["ai_provider"] = "ollama"
            logger.info(f"Proveedor cambiado a Ollama, modelo: {self.ollama.current_model}")
        from core.config_manager_unified import config_manager
        config_manager.save()
        return True

    def update_settings(self, config):
        """Actualiza la configuración del procesador de comandos"""
        logger.info("Actualizando configuración de comandos...")
        self.config = config
        if hasattr(self.ollama, "update_settings"):
            self.ollama.update_settings(config)
        self.ai_provider = self._init_ai_provider()
        logger.info("Configuración de comandos actualizada")

    def _init_words_to_numbers(self):
        return {
            "uno": 1,
            "dos": 2,
            "tres": 3,
            "cuatro": 4,
            "cinco": 5,
            "seis": 6,
            "siete": 7,
            "ocho": 8,
            "nueve": 9,
            "diez": 10,
            "once": 11,
            "doce": 12,
            "trece": 13,
            "catorce": 14,
            "quince": 15,
            "dieciséis": 16,
            "dieciseis": 16,
            "diecisiete": 17,
            "dieciocho": 18,
            "diecinueve": 19,
            "veinte": 20,
            "veintiuno": 21,
            "veintidós": 22,
            "veintidos": 22,
            "veintitrés": 23,
            "veintitres": 23,
            "veinticuatro": 24,
            "veinticinco": 25,
            "veintiséis": 26,
            "veintiseis": 26,
            "veintisiete": 27,
            "veintiocho": 28,
            "veintinueve": 29,
            "treinta": 30,
            "treinta y uno": 31,
            "treinta y dos": 32,
            "treinta y tres": 33,
            "treinta y cuatro": 34,
            "treinta y cinco": 35,
            "treinta y seis": 36,
            "treinta y siete": 37,
            "treinta y ocho": 38,
            "treinta y nueve": 39,
            "cuarenta": 40,
            "cuarenta y uno": 41,
            "cuarenta y dos": 42,
            "cuarenta y tres": 43,
            "cuarenta y cuatro": 44,
            "cuarenta y cinco": 45,
            "cuarenta y seis": 46,
            "cuarenta y siete": 47,
            "cuarenta y ocho": 48,
            "cuarenta y nueve": 49,
            "cincuenta": 50,
            "primer": 1,
            "primero": 1,
            "segundo": 2,
            "tercero": 3,
            "cuarto": 4,
            "quinto": 5,
            "sexto": 6,
            "séptimo": 7,
            "septimo": 7,
            "octavo": 8,
            "noveno": 9,
            "décimo": 10,
            "decimo": 10,
            "undécimo": 11,
            "duodécimo": 12,
            "decimotercero": 13,
            "decimocuarto": 14,
            "decimoquinto": 15,
            "decimosexto": 16,
            "decimoséptimo": 17,
            "decimoseptimo": 17,
            "decimoctavo": 18,
            "decimonoveno": 19,
            "vigésimo": 20,
            "vigesimo": 20,
            "vigésimo primero": 21,
            "vigésimo segundo": 22,
            "vigésimo tercero": 23,
            "vigésimo cuarto": 24,
            "vigésimo quinto": 25,
            "vigésimo sexto": 26,
            "vigésimo séptimo": 27,
            "vigésimo octavo": 28,
            "vigésimo noveno": 29,
            "trigésimo": 30,
            "trigesimo": 30,
        }

    def convert_text_to_number(self, text):
        try:
            text = text.lower().strip()
            text = text.translate(str.maketrans("áéíóú", "aeiou"))

            if text in self.words_to_numbers:
                return self.words_to_numbers[text]

            result = process.extractOne(
                text, self.words_to_numbers.keys(), scorer=fuzz.token_set_ratio
            )

            if result:
                best_match, score, _ = result
                return self.words_to_numbers[best_match] if score > 75 else None

            return None
        except Exception as error:
            logger.error(f"Error en convert_text_to_number: {str(error)}")
            return None

    def read_selected_text(self, chat_window):
        """Lee el texto seleccionado usando el portapapeles"""
        try:
            # Simular Ctrl+C para copiar la selección
            if HAS_PYAUTOGUI:
                pyautogui.hotkey("ctrl", "c")
            else:
                # Fallback nativo: Ctrl+C via ctypes
                ctypes.windll.user32.keybd_event(0xA2, 0, 0, 0)  # Ctrl down
                ctypes.windll.user32.keybd_event(0x43, 0, 0, 0)  # C down
                ctypes.windll.user32.keybd_event(0x43, 0, 0x0002, 0)  # C up
                ctypes.windll.user32.keybd_event(0xA2, 0, 0x0002, 0)  # Ctrl up
            time.sleep(0.2)  # Esperar un momento para que se copie

            # Acceder al portapapeles
            win32clipboard.OpenClipboard()
            try:
                texto = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
            except Exception:
                texto = None
            finally:
                win32clipboard.CloseClipboard()

            if texto and texto.strip():
                # Eliminar espacios en blanco al principio y final
                texto = texto.strip()
                # Usar el sintetizador de voz para leer el texto
                text = self.language_manager.get_text("responses.reading_selection")
                chat_window.add_message(f"{text}: {texto[:50]}...", is_user=False)
                # Verificación segura del sintetizador
                if self.eva and hasattr(self.eva, "speech") and self.eva.speech:
                    self.eva.speech.speak(texto)
            else:
                text = self.language_manager.get_text("responses.no_selection")
                chat_window.add_message(text, is_user=False)
                if self.eva and hasattr(self.eva, "speech") and self.eva.speech:
                    self.eva.speech.speak(text)
        
        except Exception as error:
            logger.error(f"Error leyendo texto seleccionado: {error}")
            return False
    
    def process_command(self, text, chat_window):
        """Delegates command processing to the CommandDispatcher."""
        self.dispatcher.process_command(text, chat_window)

    def _handle_dictation_mode(self, text: str, chat_window) -> bool:
        """Maneja el modo de dictado con corrección automática"""
        try:
            text_lower = text.lower().strip()
            
            # Comandos para finalizar dictado
            finish_commands = [
                "finalizar dictado", "terminar dictado", "acabar dictado", "parar dictado",
                "finish dictation", "end dictation", "stop dictation"
            ]
            
            if any(cmd in text_lower for cmd in finish_commands):
                return self._finalize_dictation(chat_window)
            
            # Acumular texto dictado
            self.dictation_text += text + " "
            
            # Mostrar progreso cada 5 palabras
            word_count = len(self.dictation_text.split())
            if word_count % 5 == 0:
                chat_window.add_message(f"📝 Dictando... ({word_count} palabras)", is_user=False)
            
            return True
                
        except Exception as e:
            logger.error(f"Error en dictado: {str(e)}")
            self.dictation_mode = False
            self.dictation_text = ""
            chat_window.add_message("❌ Error en dictado - modo desactivado", is_user=False)
            return True
    
    def _finalize_dictation(self, chat_window) -> bool:
        """Finaliza el dictado con corrección automática"""
        try:
            raw_text = self.dictation_text.strip()
            
            if not raw_text:
                msg = self.language_manager.get_text("responses.no_dictation_text")
                chat_window.add_message(msg, is_user=False)
                self._reset_dictation()
                return True
            
            # Mostrar texto original
            msg = self.language_manager.get_text("responses.dictation_original")
            chat_window.add_message(msg, is_user=False)
            chat_window.add_message(raw_text, is_user=True)  # Como si el usuario lo hubiera escrito
            
            # Corregir automáticamente si está disponible
            corrected_text = self._correct_grammar(raw_text)
            
            # Mostrar resultado final
            if corrected_text != raw_text:
                msg = self.language_manager.get_text("responses.dictation_corrected")
                chat_window.add_message(msg, is_user=False)
                chat_window.add_message(corrected_text, is_user=False)
                final_text = corrected_text
            else:
                msg = self.language_manager.get_text("responses.dictation_no_corrections")
                chat_window.add_message(msg, is_user=False)
                final_text = raw_text
            
            # Copiar automáticamente al portapapeles
            try:
                import pyperclip
                pyperclip.copy(final_text)
                word_count = len(final_text.split())
                chat_window.add_message(f"📋 Dictado completado - {word_count} palabras copiadas al portapapeles", is_user=False)
                
                # Feedback vocal
                if self.eva and hasattr(self.eva, "speech") and self.eva.speech:
                    self.eva.speech.speak(f"Dictado completado con {word_count} palabras y copiado al portapapeles")
                    
            except Exception as e:
                logger.warning(f"No se pudo copiar al portapapeles: {str(e)}")
                chat_window.add_message("✓ Dictado completado", is_user=False)
            
            self._reset_dictation()
            return True
            
        except Exception as e:
            logger.error(f"Error finalizando dictado: {str(e)}")
            chat_window.add_message(f"❌ Error procesando dictado: {str(e)}", is_user=False)
            self._reset_dictation()
            return True
    
    def _reset_dictation(self):
        """Resetea el estado del dictado"""
        self.dictation_mode = False
        self.dictation_text = ""
        if hasattr(self, 'dictation_chat_window'):
            delattr(self, 'dictation_chat_window')
    
    def _init_grammar_corrector(self):
        """Inicializa el corrector gramatical si está disponible"""
        try:
            # Intentar importar el corrector del módulo inteligente
            from voice.dictation_intelligent import GrammarCorrector
            self.grammar_corrector = GrammarCorrector(self.lang)
            logger.info("Corrector gramatical inicializado")
        except Exception as e:
            logger.warning(f"Corrector gramatical no disponible: {str(e)}")
            self.grammar_corrector = None
    
    def _correct_grammar(self, text: str) -> str:
        """Corrige la gramática del texto si el corrector está disponible"""
        if hasattr(self, 'grammar_corrector') and self.grammar_corrector:
            try:
                return self.grammar_corrector.correct_text(text)
            except Exception as e:
                logger.warning(f"Error en corrección gramatical: {str(e)}")
        return text

    def handle_confirmation(self, text, chat_window):
        self.dispatcher._handle_confirmation(text, chat_window)

    def execute_dangerous_command(self, chat_window):
        self.dispatcher._execute_dangerous_command(chat_window)

    # --- Dynamic context properties (fix: avoid stale copies of mutable state) ---
    @property
    def last_opened_folder(self):
        return self.context.last_opened_folder

    @last_opened_folder.setter
    def last_opened_folder(self, value):
        self.context.last_opened_folder = value

    @property
    def current_folder_files(self):
        return self.context.current_folder_files

    @current_folder_files.setter
    def current_folder_files(self, value):
        self.context.current_folder_files = value

    @property
    def pending_file_order(self):
        return self.context.pending_file_order

    @pending_file_order.setter
    def pending_file_order(self, value):
        self.context.pending_file_order = value

    @property
    def file_sort_method(self):
        return self.context.file_sort_method

    @file_sort_method.setter
    def file_sort_method(self, value):
        self.context.file_sort_method = value
