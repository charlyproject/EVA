import json
import logging
import threading
from datetime import datetime

from PySide6.QtCore import QObject, Signal

from core.config_manager_unified import config_manager

logger = logging.getLogger("EVA")


class ChatController(QObject):
    """Business logic for the chat window. Separated from UI concerns."""

    message_received = Signal(str, bool)
    voice_indicator_changed = Signal(bool)
    mute_state_changed = Signal(bool)
    language_applied = Signal(str)

    def __init__(self, config, session_manager, language_manager, chat_window=None):
        super().__init__()
        self.config = config
        self.session_manager = session_manager
        self.language_manager = language_manager
        self.chat_window = chat_window

        self.user_name = "Usuario"
        self.knowledge_base = self._load_knowledge_base()
        self.command_processor = None
        self.is_muted = False

        self._migrate_old_knowledge_base()
        if "user_profile" in self.knowledge_base and "name" in self.knowledge_base["user_profile"]:
            self.user_name = self.knowledge_base["user_profile"]["name"]
        elif "user_name" in self.knowledge_base:
            self.user_name = self.knowledge_base["user_name"]

        self._log_session_start()

    # --- Knowledge base ---

    def _load_knowledge_base(self):
        logger.info("Cargando base de conocimiento...")
        try:
            from utils.safe_json_manager import get_safe_json_manager
            manager = get_safe_json_manager("eva_knowledge_base.json")
            return manager.load_or_create()
        except Exception as e:
            logger.error(f"Error cargando base de conocimiento: {str(e)}")
            return {
                "user_profile": {"name": "Usuario"},
                "usage_analytics": {"most_used_commands": {}, "total_sessions": 0},
                "preferences": {"preferred_language": "es"}
            }

    def save_knowledge_base(self):
        try:
            from utils.safe_json_manager import get_safe_json_manager
            manager = get_safe_json_manager("eva_knowledge_base.json")
            manager.save(self.knowledge_base)
        except Exception as e:
            logger.error(f"Error guardando base de conocimiento: {str(e)}")
            try:
                with open("eva_knowledge_base.json", "w", encoding="utf-8") as f:
                    json.dump(self.knowledge_base, f, indent=4, ensure_ascii=False)
            except Exception as fallback_error:
                logger.error(f"Error en fallback de guardado: {str(fallback_error)}")

    def _migrate_old_knowledge_base(self):
        if "user_name" in self.knowledge_base and "user_profile" not in self.knowledge_base:
            old_name = self.knowledge_base.get("user_name", "Usuario")
            self.knowledge_base = {
                "user_profile": {"name": old_name, "greeting_preference": "auto",
                                 "preferred_model": "phi3:mini", "mute_mode": False,
                                 "timezone": "Europe/Madrid", "work_hours": "09:00-18:00"},
                "usage_analytics": {"most_used_commands": {}, "active_hours": {},
                                    "total_sessions": 0, "last_session": None},
                "command_history": {"last_commands": [], "max_history": 5},
                "context_memory": {"last_topic": None, "last_document": None,
                                   "last_question": None, "last_response": None,
                                   "conversation_context": []},
                "custom_shortcuts": {},
                "preferences": {"favorite_programs": [], "frequent_folders": [],
                                "preferred_language": "es", "auto_suggestions": True,
                                "contextual_greetings": True},
                "learning_data": {"command_patterns": {}, "time_patterns": {}, "topic_interests": {}}
            }
            self.save_knowledge_base()
            logger.info("Base de conocimiento migrada al nuevo formato")

    def _log_session_start(self):
        try:
            now = datetime.now()
            analytics = self.knowledge_base.setdefault("usage_analytics", {})
            analytics.setdefault("active_hours", {"morning": 0, "afternoon": 0, "evening": 0, "night": 0})
            analytics.setdefault("most_used_commands", {})
            analytics.setdefault("total_sessions", 0)
            analytics["total_sessions"] += 1
            analytics["last_session"] = now.isoformat()
            hour = now.hour
            period = "morning" if 6 <= hour < 12 else "afternoon" if 12 <= hour < 18 else "evening" if 18 <= hour < 22 else "night"
            analytics["active_hours"][period] += 1
            self.save_knowledge_base()
        except Exception as e:
            logger.error(f"Error registrando sesión: {str(e)}")

    # --- Command tracking ---

    def log_command_usage(self, command_text):
        try:
            self.knowledge_base.setdefault("command_history", {"last_commands": [], "max_history": 5})
            analytics = self.knowledge_base.setdefault("usage_analytics", {})
            most_used = analytics.setdefault("most_used_commands", {})
            clean_command = command_text.lower().strip()
            most_used[clean_command] = most_used.get(clean_command, 0) + 1
            history = self.knowledge_base["command_history"]["last_commands"]
            max_history = self.knowledge_base["command_history"]["max_history"]
            if clean_command in history:
                history.remove(clean_command)
            history.insert(0, clean_command)
            if len(history) > max_history:
                history[:] = history[:max_history]
            self.save_knowledge_base()
        except Exception as e:
            logger.error(f"Error registrando comando: {str(e)}")

    def update_context_memory(self, question=None, response=None, topic=None, document=None):
        try:
            context = self.knowledge_base.setdefault("context_memory", {})
            context.setdefault("conversation_context", [])
            if question:
                context["last_question"] = question
                context["conversation_context"].append({"type": "question", "content": question,
                                                        "timestamp": datetime.now().isoformat()})
            if response:
                context["last_response"] = response
                context["conversation_context"].append({"type": "response", "content": response,
                                                        "timestamp": datetime.now().isoformat()})
            if topic:
                context["last_topic"] = topic
            if document:
                context["last_document"] = document
            if len(context["conversation_context"]) > 10:
                context["conversation_context"] = context["conversation_context"][-10:]
            self.save_knowledge_base()
        except Exception as e:
            logger.error(f"Error actualizando contexto: {str(e)}")

    # --- Shortcuts ---

    def add_custom_shortcut(self, shortcut_name, commands):
        try:
            self.knowledge_base.setdefault("custom_shortcuts", {})[shortcut_name.lower()] = commands
            self.save_knowledge_base()
            return f"Atajo '{shortcut_name}' creado exitosamente"
        except Exception as e:
            logger.error(f"Error creando atajo: {str(e)}")
            return f"Error creando atajo: {str(e)}"

    def execute_custom_shortcut(self, shortcut_name):
        try:
            shortcuts = self.knowledge_base.setdefault("custom_shortcuts", {})
            if shortcut_name.lower() in shortcuts:
                commands = shortcuts[shortcut_name.lower()]
                if isinstance(commands, str):
                    commands = [commands]
                for command in commands:
                    if self.command_processor:
                        self.command_processor.process_command(command, self.chat_window)
                return True
            return False
        except Exception as e:
            logger.error(f"Error ejecutando atajo: {str(e)}")
            return False

    # --- Greetings ---

    def get_contextual_greeting(self):
        try:
            name = self.user_name
            hour = datetime.now().hour
            current_lang = self.language_manager.current_lang
            contextual_enabled = self.knowledge_base.get("preferences", {}).get("contextual_greetings", True)
            if not contextual_enabled:
                return self.language_manager.get_text("responses.welcome_message").format(user=name)
            if current_lang == "en":
                if 6 <= hour < 12:
                    greetings = [
                        f"Good morning {name}! I'm EVA, how shall we start the day?",
                        f"Good day {name}! How can I help you this morning?",
                        f"Hello {name}! How did you wake up? I'm EVA, your assistant."
                    ]
                elif 12 <= hour < 18:
                    greetings = [
                        f"Good afternoon {name}! I'm EVA, how's your day going?",
                        f"Hello {name}! How can I help you this afternoon?",
                        f"Good afternoon {name}! I'm EVA, what do you need?"
                    ]
                elif 18 <= hour < 22:
                    greetings = [
                        f"Good evening {name}! I'm EVA, how was your day?",
                        f"Hello {name}! How can I help you tonight?",
                        f"Good evening {name}! I'm EVA, how was your afternoon?"
                    ]
                else:
                    greetings = [
                        f"Hello {name}! Working late, eh? I'm EVA.",
                        f"Good evening {name}! I'm EVA, need anything?",
                        f"Hello {name}! It's late, but I'm here. I'm EVA."
                    ]
            else:
                if 6 <= hour < 12:
                    greetings = [
                        f"¡Buenos días {name}! Soy EVA, ¿cómo empezamos el día?",
                        f"¡Buen día {name}! ¿En qué puedo ayudarte esta mañana?",
                        f"¡Hola {name}! ¿Cómo amaneciste? Soy EVA, tu asistente."
                    ]
                elif 12 <= hour < 18:
                    greetings = [
                        f"¡Buenas tardes {name}! Soy EVA, ¿cómo va tu día?",
                        f"¡Hola {name}! ¿En qué puedo ayudarte esta tarde?",
                        f"¡Buenas tardes {name}! Soy EVA, ¿qué necesitas?"
                    ]
                elif 18 <= hour < 22:
                    greetings = [
                        f"¡Buenas noches {name}! Soy EVA, ¿cómo estuvo tu día?",
                        f"¡Hola {name}! ¿En qué puedo ayudarte esta noche?",
                        f"¡Buenas noches {name}! Soy EVA, ¿qué tal la tarde?"
                    ]
                else:
                    greetings = [
                        f"¡Hola {name}! Trabajando tarde, ¿eh? Soy EVA.",
                        f"¡Buenas noches {name}! Soy EVA, ¿necesitas algo?",
                        f"¡Hola {name}! Es tarde, pero aquí estoy. Soy EVA."
                    ]
            import random
            return random.choice(greetings)
        except Exception as e:
            logger.error(f"Error generando saludo: {str(e)}")
            return self.language_manager.get_text("responses.welcome_message").format(user=self.user_name)

    def get_command_suggestions(self):
        try:
            if not self.knowledge_base.get("preferences", {}).get("auto_suggestions", True):
                return []
            most_used = self.knowledge_base.get("usage_analytics", {}).get("most_used_commands", {})
            if not most_used:
                return []
            sorted_commands = sorted(most_used.items(), key=lambda x: x[1], reverse=True)[:3]
            return [cmd for cmd, count in sorted_commands if count > 2]
        except Exception as e:
            logger.error(f"Error generando sugerencias: {str(e)}")
            return []

    def get_conversation_context_for_ollama(self, current_question=None):
        try:
            context = self.knowledge_base.get("context_memory", {})
            user_name = self.knowledge_base.get("user_profile", {}).get("name", self.user_name)
            context_prompt = f"Usuario: {user_name}\n"
            if context.get("last_topic"):
                context_prompt += f"Último tema: {context['last_topic']}\n"
            if context.get("last_question") and context.get("last_response"):
                context_prompt += f"Pregunta anterior: {context['last_question']}\n"
                context_prompt += f"Respuesta anterior: {context['last_response']}\n"
            if current_question:
                context_prompt += f"Pregunta actual: {current_question}"
            return context_prompt
        except Exception as e:
            logger.error(f"Error preparando contexto: {str(e)}")
            return current_question if current_question else ""

    # --- User name ---

    def update_user_name(self, new_name):
        self.user_name = new_name
        self.knowledge_base["user_name"] = new_name
        self.save_knowledge_base()

    # --- Voice control ---

    def toggle_voice_listening(self, new_state):
        if not self.command_processor or not self.command_processor.eva:
            return False
        voice_engine = getattr(self.command_processor.eva, 'voice_engine', None)
        if not voice_engine:
            return False
        try:
            if new_state and not voice_engine.is_listening:
                voice_engine.start()
            elif not new_state and voice_engine.is_listening:
                voice_engine.stop()
            self.config["auto_listen"] = new_state
            config_manager.save()
            return True
        except Exception as e:
            logger.error(f"Error toggling voice: {str(e)}")
            return False

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.command_processor and self.command_processor.eva:
            synth = getattr(self.command_processor.eva, 'speech_synthesizer', None)
            if synth:
                try:
                    if self.is_muted:
                        synth.set_mute(True)
                    else:
                        synth.set_mute(False)
                        synth.resume_speech()
                except Exception as e:
                    logger.error(f"Error toggling mute: {str(e)}")
        return self.is_muted

    # --- Language ---

    def change_language(self, lang):
        try:
            self.language_manager.set_language(lang)
            self.config["language"] = lang
            config_manager.save()
            if self.command_processor and self.command_processor.eva:
                synth = getattr(self.command_processor.eva, 'speech_synthesizer', None)
                if synth:
                    voice_config = self.config.copy()
                    voice_config["language"] = lang
                    synth.update_config(voice_config)
            self.language_applied.emit(lang)
            return True
        except Exception as e:
            logger.error(f"Error changing language: {str(e)}")
            return False

    # --- Settings ---

    def handle_settings_result(self, result, settings_dialog):
        if result == 1:
            self.config = settings_dialog.config
            if self.command_processor:
                self.command_processor.update_settings(self.config)
                if self.command_processor.eva and hasattr(self.command_processor.eva, 'update_settings'):
                    self.command_processor.eva.update_settings(self.config)
            if "user_name" in self.config:
                self.update_user_name(self.config["user_name"])
            return True
        return False

    def open_custom_commands(self):
        try:
            from ui.custom_commands_dialog import CustomCommandsDialog
            from PySide6.QtWidgets import QDialog
            dialog = CustomCommandsDialog(self.config, self.language_manager, self.chat_window)
            if dialog.exec() == QDialog.Accepted:
                self.config = dialog.config
                if self.command_processor and self.command_processor.eva:
                    self.command_processor.eva.update_settings(self.config)
                return True
            return False
        except Exception as e:
            logger.error(f"Error en custom commands: {str(e)}")
            return False

    # --- File processing ---

    def process_selected_file(self, file_path):
        try:
            if self.command_processor and hasattr(self.command_processor, 'document_handler'):
                self.command_processor.document_handler.target_file_path = file_path
                threading.Thread(
                    target=self.command_processor.document_handler.process_document,
                    args=(file_path, self.chat_window),
                    daemon=True
                ).start()
                return True
            return False
        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            return False

    # --- Command processing ---

    def send_message(self, text):
        if not text or not text.strip():
            return
        self.message_received.emit(text.strip(), True)
        self.log_command_usage(text.strip())
        if self.execute_custom_shortcut(text.strip()):
            return
        if self.command_processor:
            self.command_processor.process_command(text.strip(), self.chat_window)
        else:
            logger.warning("No hay command_processor disponible")

    @property
    def speech_synthesizer(self):
        if self.command_processor and hasattr(self.command_processor, 'eva'):
            return getattr(self.command_processor.eva, 'speech_synthesizer', None)
        return None

    @property
    def voice_engine(self):
        if self.command_processor and hasattr(self.command_processor, 'eva'):
            return getattr(self.command_processor.eva, 'voice_engine', None)
        return None
