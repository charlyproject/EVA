# ============================================================
# session_manager.py — VERSIÓN LIBRE (sin restricciones)
# Todas las funciones disponibles para cualquier usuario.
# Premium, contadores y límites eliminados completamente.
# ============================================================
import json
import logging
import os
import time

from core.language_manager import LanguageManager

logger = logging.getLogger("EVA")


class SessionManager:
    def __init__(self, config):
        self.config = config
        self.state_file = os.path.join("config", "session.dat")
        self.start_time = time.time()
        self.language_manager = LanguageManager()

        # Control de primer arranque
        from utils.first_run import is_first_run
        self._first_run = is_first_run()
        self._license_verified = True  # Siempre verificada (sin restricciones)
        self._is_premium = True        # Siempre premium (sin restricciones)

        # Crear directorio de configuración si no existe
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

        # Cargar idioma inicial
        self.load_initial_language()

    # ----------------------------------------------------------
    # API pública — todas las funciones liberadas
    # ----------------------------------------------------------

    def is_premium(self) -> bool:
        """Siempre True: sistema sin restricciones."""
        return True

    def can_operate(self, initial_check=False) -> bool:
        """Siempre True: sin límite de tiempo ni de cuenta."""
        return True

    def can_use_ollama(self) -> bool:
        """Siempre True: conversaciones ilimitadas."""
        return True

    def use_conversation(self):
        """Sin contador: no-op."""
        pass

    def get_remaining_conversations(self):
        """Sin límite de conversaciones."""
        return "∞"

    def remaining_time(self) -> float:
        """Sin temporizador: devuelve valor grande para compatibilidad."""
        return 999999.0

    def format_time(self) -> str:
        return "∞"

    def update_license_status(self):
        """Compatibilidad: no hace nada relevante."""
        self._first_run = False
        self._license_verified = True
        self._is_premium = True
        logger.info("Estado de sesión actualizado (modo libre, sin restricciones)")
        return True

    def save_state(self):
        """Guarda estado mínimo para compatibilidad con otros módulos."""
        try:
            data = {
                "start_time": self.start_time,
                "free_duration": 999999,
                "conversation_count_today": 0,
                "last_reset_date": None,
                "checksum": "",
            }
            with open(self.state_file, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logger.error(f"Error guardando sesión: {str(e)}")

    def load_state(self):
        """Stub de compatibilidad."""
        pass

    def get_hardware_id(self) -> str:
        """Stub de compatibilidad."""
        import platform
        import hashlib
        try:
            info = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
            return hashlib.sha256(info.encode()).hexdigest()
        except Exception:
            return "default_id"

    def encrypt_data(self, data: str) -> str:
        """Stub de compatibilidad."""
        import hashlib
        return hashlib.sha256(f"{data}{self.get_hardware_id()}".encode()).hexdigest()

    def load_initial_language(self):
        """Carga el idioma inicial desde install_config.json si existe."""
        install_config_path = "config/install_config.json"
        if os.path.exists(install_config_path):
            try:
                with open(install_config_path, "r", encoding="utf-8") as f:
                    install_config = json.load(f)
                    lang = install_config.get("default_language", "es")
                    self.language_manager.set_language(lang)
                    logger.info(f"Idioma inicial cargado: {lang}")
            except Exception as e:
                logger.error(f"Error cargando install_config.json: {str(e)}")
                self.language_manager.set_language("es")
        else:
            self.language_manager.set_language(self.config.get("language", "es"))