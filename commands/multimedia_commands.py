"""
Comandos multimedia unificados para EVA
Maneja VLC, MPC-HC y Kodi con comandos naturales
Filosofía: 1 comando = 1 función
"""

import logging
import pyautogui

from utils.bilingual_command import BilingualCommand

logger = logging.getLogger("EVA")


class MultimediaCommandHandler:
    """Handler unificado para comandos multimedia (VLC, MPC, Kodi)"""
    
    def __init__(self, processor):
        self.processor = processor
        self.config = processor.config
        self.language_manager = processor.language_manager
        
        # Comandos multimedia unificados con filosofía natural
        self.commands = {
            # Comando de pausa/reproducción universal
            BilingualCommand("pausa", "pause"): self._pause_play,
            BilingualCommand("reproduce", "play"): self._pause_play,
            
            # Comandos de navegación
            BilingualCommand("siguiente", "next"): self._next,
            BilingualCommand("anterior", "previous"): self._previous,
            BilingualCommand("para", "stop"): self._stop,
            
            # Comandos de volumen (específicos para multimedia)
            BilingualCommand("sube volumen multimedia", "volume up multimedia"): self._volume_up,
            BilingualCommand("baja volumen multimedia", "volume down multimedia"): self._volume_down,
            BilingualCommand("silencia multimedia", "mute multimedia"): self._mute,
            
            # Comando de pantalla completa
            BilingualCommand("pantalla completa", "fullscreen"): self._fullscreen,
        }
    
    def can_handle(self, text: str) -> bool:
        """Verifica si puede manejar el comando"""
        text_lower = text.lower().strip()

        # Si empieza con "eva", dejar que ConversationHandler lo procese
        if text_lower.startswith("eva "):
            return False

        # Verificar comandos multimedia
        for bilingual_cmd in self.commands.keys():
            if bilingual_cmd.matches(text_lower):
                return True

        return False
    
    def handle(self, text: str, chat_window) -> bool:
        """Maneja el comando multimedia"""
        try:
            text_lower = text.lower().strip()
            
            # Buscar comando coincidente
            for bilingual_cmd, handler_func in self.commands.items():
                if bilingual_cmd.matches(text_lower):
                    logger.info(f"🎵 Ejecutando comando multimedia: {bilingual_cmd}")
                    return handler_func(chat_window)
            
            return False
            
        except Exception as e:
            logger.error(f"Error en comando multimedia: {str(e)}")
            error_msg = self.language_manager.get_text("responses.error", default="Error en comando multimedia")
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _pause_play(self, chat_window) -> bool:
        """Pausa/reproduce multimedia"""
        try:
            pyautogui.press("space")  # Universal para VLC, MPC, Kodi
            logger.info("🎵 Comando multimedia: Pausa/Reproducir")
            
            response = self.language_manager.get_text("responses.multimedia_pause", 
                                                    default="Reproducción pausada/reanudada")
            chat_window.add_message(response, is_user=False)
            return True
            
        except Exception as e:
            logger.error(f"Error en pausa/reproducir: {str(e)}")
            return False
    
    def _next(self, chat_window) -> bool:
        """Siguiente pista/video"""
        try:
            pyautogui.press("nexttrack")  # Universal
            logger.info("🎵 Comando multimedia: Siguiente")
            
            response = self.language_manager.get_text("responses.multimedia_next", 
                                                    default="Siguiente pista")
            chat_window.add_message(response, is_user=False)
            return True
            
        except Exception as e:
            logger.error(f"Error en siguiente: {str(e)}")
            return False
    
    def _previous(self, chat_window) -> bool:
        """Anterior pista/video"""
        try:
            pyautogui.press("prevtrack")  # Universal
            logger.info("🎵 Comando multimedia: Anterior")
            
            response = self.language_manager.get_text("responses.multimedia_previous", 
                                                    default="Pista anterior")
            chat_window.add_message(response, is_user=False)
            return True
            
        except Exception as e:
            logger.error(f"Error en anterior: {str(e)}")
            return False
    
    def _stop(self, chat_window) -> bool:
        """Detener reproducción"""
        try:
            # Intentar diferentes teclas según el reproductor
            pyautogui.press("s")  # VLC
            logger.info("🎵 Comando multimedia: Detener")
            
            response = self.language_manager.get_text("responses.multimedia_stop", 
                                                    default="Reproducción detenida")
            chat_window.add_message(response, is_user=False)
            return True
            
        except Exception as e:
            logger.error(f"Error en detener: {str(e)}")
            return False
    
    def _volume_up(self, chat_window) -> bool:
        """Subir volumen multimedia"""
        try:
            pyautogui.press("volumeup")  # Universal
            logger.info("🎵 Comando multimedia: Subir volumen")
            
            response = self.language_manager.get_text("responses.multimedia_volume_up", 
                                                    default="Volumen multimedia aumentado")
            chat_window.add_message(response, is_user=False)
            return True
            
        except Exception as e:
            logger.error(f"Error subiendo volumen: {str(e)}")
            return False
    
    def _volume_down(self, chat_window) -> bool:
        """Bajar volumen multimedia"""
        try:
            pyautogui.press("volumedown")  # Universal
            logger.info("🎵 Comando multimedia: Bajar volumen")
            
            response = self.language_manager.get_text("responses.multimedia_volume_down", 
                                                    default="Volumen multimedia disminuido")
            chat_window.add_message(response, is_user=False)
            return True
            
        except Exception as e:
            logger.error(f"Error bajando volumen: {str(e)}")
            return False
    
    def _mute(self, chat_window) -> bool:
        """Silenciar multimedia"""
        try:
            pyautogui.press("volumemute")  # Universal
            logger.info("🎵 Comando multimedia: Silenciar")
            
            response = self.language_manager.get_text("responses.multimedia_mute", 
                                                    default="Multimedia silenciado")
            chat_window.add_message(response, is_user=False)
            return True
            
        except Exception as e:
            logger.error(f"Error silenciando: {str(e)}")
            return False
    
    def _fullscreen(self, chat_window) -> bool:
        """Pantalla completa"""
        try:
            pyautogui.press("f")  # Universal para la mayoría
            logger.info("🎵 Comando multimedia: Pantalla completa")
            
            response = self.language_manager.get_text("responses.multimedia_fullscreen", 
                                                    default="Pantalla completa activada")
            chat_window.add_message(response, is_user=False)
            return True
            
        except Exception as e:
            logger.error(f"Error en pantalla completa: {str(e)}")
            return False