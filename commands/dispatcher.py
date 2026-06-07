import logging
from typing import List, Callable

logger = logging.getLogger("EVA")


class Middleware:
    @staticmethod
    def session_check(processor, text: str, chat_window) -> bool:
        if not processor.session_manager.can_operate():
            session_expired = processor.language_manager.get_text("responses.session_expired")
            chat_window.add_message(session_expired, is_user=False)
            return False
        return True

    @staticmethod
    def command_logging(processor, text: str, chat_window) -> bool:
        logger.info(f"Processing command: {text}")
        return True


class CommandDispatcher:
    """Routes commands to registered handlers with middleware support."""

    def __init__(self, config, language_manager, session_manager, eva=None):
        self.config = config
        self.language_manager = language_manager
        self.session_manager = session_manager
        self.eva = eva

        self.handlers: List = []
        self.middleware: List[Callable] = [
            Middleware.session_check,
            Middleware.command_logging,
        ]

        # Pending command confirmation
        self.pending_command = None
        self.wait_time = 0

    def process_command(self, text: str, chat_window):
        """Main command processing pipeline"""
        try:
            if not hasattr(chat_window, "add_message"):
                raise AttributeError("El objeto chat_window no tiene el método add_message")

            # Check for pending confirmation first
            if self.pending_command:
                self._handle_confirmation(text, chat_window)
                return

            # Check for pending file order
            processor = getattr(self, '_processor_ref', None)
            if processor and processor.context.pending_file_order:
                return

            # Check dictation mode
            if processor and processor.dictation_mode:
                if processor._handle_dictation_mode(text, chat_window):
                    return

            # Run middleware pipeline
            for middleware_fn in self.middleware:
                processor_ref = getattr(self, '_processor_ref', None)
                if not middleware_fn(processor_ref, text, chat_window):
                    return

            # Diagnosis command for folder detection
            text_lower = text.lower().strip()
            if any(cmd in text_lower for cmd in ["diagnóstico carpetas", "diagnostico carpetas", "folder diagnosis", "debug carpetas"]):
                try:
                    from utils.file_utils import test_folder_detection, get_working_folder
                    diag = test_folder_detection()
                    active = get_working_folder()
                    last = diag.get('last_saved', 'N/A')
                    response = (
                        f"📊 DIAGNÓSTICO DE CARPETAS:\n"
                        f"  • PowerShell disponible: {diag.get('powershell_available')}\n"
                        f"  • Caché: {diag.get('cache_path')}\n"
                        f"  • Actualizando: {diag.get('cache_updating')}\n"
                        f"  • Última guardada: {last}\n"
                        f"  • get_working_folder(): {active}"
                    )
                    chat_window.add_message(response, is_user=False)
                    return
                except Exception as e:
                    chat_window.add_message(f"❌ Error en diagnóstico: {e}", is_user=False)
                    logger.error(f"Error en diagnóstico de carpetas: {e}", exc_info=True)
                    return

            # Try each handler until one succeeds
            logger.info(f"PROCESANDO COMANDO: '{text}'")
            for i, handler in enumerate(self.handlers):
                handler_name = handler.__class__.__name__
                can_handle = handler.can_handle(text)
                logger.info(f"Handler {i + 1}: {handler_name}.can_handle('{text}') = {can_handle}")

                if can_handle:
                    logger.info(f"USANDO HANDLER: {handler_name}")
                    result = handler.handle(text, chat_window)
                    logger.info(f"RESULTADO: {result}")
                    if result:
                        return

            # Fallback to unknown command
            response = self.language_manager.get_text("responses.unknown_command")
            chat_window.add_message(response, is_user=False)

        except RuntimeError as e:
            if "Ollama no disponible" in str(e):
                error_msg = "Error: Ollama no está disponible. Instala/Inicia Ollama desde https://ollama.com"
                chat_window.add_message(error_msg, is_user=False)
            else:
                self._handle_command_error(e, chat_window)
        except Exception as error:
            logger.error(f"Error al procesar comando: {str(error)}")
            self._handle_command_error(error, chat_window)

    def _handle_confirmation(self, text, chat_window):
        """Handle yes/no confirmation for dangerous commands"""
        try:
            text_lower = text.lower()
            if "si" in text_lower or "sí" in text_lower:
                self._execute_dangerous_command(chat_window)
            elif "no" in text_lower:
                self.pending_command = None
                self.wait_time = 0
                action_canceled = self.language_manager.get_text("responses.action_canceled")
                chat_window.add_message(action_canceled, is_user=False)
            else:
                please_respond = self.language_manager.get_text("responses.please_respond")
                chat_window.add_message(please_respond, is_user=False)
        except Exception as error:
            logger.error(f"Error en confirmación: {error}")

    def _execute_dangerous_command(self, chat_window):
        """Execute a confirmed dangerous command (shutdown, restart, etc.)"""
        import os
        try:
            command = self.pending_command.lower()
            if "apagar" in command:
                time_str = f"{self.wait_time * 60}" if self.wait_time > 0 else "60"
                os.system(f"shutdown /s /t {time_str}")
                if self.wait_time > 0:
                    text = self.language_manager.get_text("responses.shutdown_minutes")
                    chat_window.add_message(text.format(minutes=self.wait_time), is_user=False)
                else:
                    text = self.language_manager.get_text("responses.shutdown_one_minute")
                    chat_window.add_message(text, is_user=False)
            elif "reiniciar" in command:
                os.system("shutdown /r /t 60")
                text = self.language_manager.get_text("responses.reboot_one_minute")
                chat_window.add_message(text, is_user=False)
            elif "cerrar sesion" in command:
                os.system("shutdown /l")
                text = self.language_manager.get_text("responses.logging_off")
                chat_window.add_message(text, is_user=False)
            self.pending_command = None
            self.wait_time = 0
        except Exception as error:
            logger.error(f"Error ejecutando comando peligroso: {error}")

    def _handle_command_error(self, error, chat_window):
        """Handle command processing errors gracefully"""
        try:
            from core.error_handler import ErrorHandler
            ErrorHandler.handle(error, "Error al procesar comando")
        except ImportError:
            pass
        if hasattr(chat_window, "add_message"):
            error_text = self.language_manager.get_text("responses.command_error")
            chat_window.add_message(error_text, is_user=False)

    def find_command_with_variants(self, target, available_commands):
        """Find a command using configured variants"""
        try:
            target_lower = target.lower().strip()
            variants = self.config.get("variants", {})
            for command, variant_list in variants.items():
                if command in available_commands:
                    if target_lower in [v.lower() for v in variant_list]:
                        logger.info(f"Variante encontrada: '{target}' -> '{command}'")
                        return command
            return None
        except Exception as e:
            logger.error(f"Error buscando variantes: {str(e)}")
            return None
