"""
Sistema de Comandos de Sistema - Arquitectura Limpia
Comandos naturales únicos para control del sistema
"""

import logging
try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False
    import ctypes

logger = logging.getLogger("EVA")


# --- Fallback nativo para pyautogui (sin dependencia) ---
if not HAS_PYAUTOGUI:
    _VK_VOLUME_UP = 0xAF
    _VK_VOLUME_DOWN = 0xAE
    _VK_VOLUME_MUTE = 0xAD
    _VK_MENU = 0x12  # Alt
    _VK_F4 = 0x73
    _VK_SNAPSHOT = 0x2C

    def _native_key_down(vk_code):
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)

    def _native_key_up(vk_code):
        ctypes.windll.user32.keybd_event(vk_code, 0, 0x0002, 0)

    def _native_press(key_name):
        """Simula una pulsación de tecla nativa."""
        vk_map = {
            "volumeup": _VK_VOLUME_UP,
            "volumedown": _VK_VOLUME_DOWN,
            "volumemute": _VK_VOLUME_MUTE,
        }
        vk = vk_map.get(key_name.lower())
        if vk:
            _native_key_down(vk)
            import time as _t
            _t.sleep(0.05)
            _native_key_up(vk)
        else:
            logger.warning(f"Tecla no mapeada para fallback nativo: {key_name}")

    def _native_hotkey(*keys):
        """Simula combinación de teclas nativa."""
        vk_map = {
            "alt": _VK_MENU,
            "f4": _VK_F4,
            "win": 0x5B,
            "shift": 0xA0,
            "ctrl": 0xA2,
            "c": 0x43,
            "s": 0x53,
        }
        # Mantener un pequeño delay para que el SO registre la combinación
        import time as _t
        for k in keys:
            vk = vk_map.get(k.lower())
            if vk:
                _native_key_down(vk)
                _t.sleep(0.02)
        for k in keys:
            vk = vk_map.get(k.lower())
            if vk:
                _native_key_up(vk)
                _t.sleep(0.02)

    def _native_screenshot():
        """Captura de pantalla nativa usando PrintScreen."""
        import time as _t
        import win32clipboard as _wcb
        _t.sleep(0.1)
        _native_key_down(_VK_SNAPSHOT)
        _t.sleep(0.1)
        _native_key_up(_VK_SNAPSHOT)
        _t.sleep(0.2)
        try:
            _wcb.OpenClipboard()
            if _wcb.IsClipboardFormatAvailable(_wcb.CF_BITMAP):
                data = _wcb.GetClipboardData(_wcb.CF_BITMAP)
                _wcb.CloseClipboard()
                from PIL import Image
                img = Image.frombuffer("RGBA", (data.Width, data.Height), data.GetBitmapBits(True), "raw", "RGBA", 0, 1)
                return img
            _wcb.CloseClipboard()
        except Exception:
            pass
        return None


class SystemCommandHandler:
    """Handler unificado para comandos de sistema"""
    
    def __init__(self, processor):
        self.processor = processor
        self.config = processor.config
        self.language_manager = processor.language_manager
        self.session_manager = processor.session_manager
        
        # Comandos de sistema - ÚNICOS Y NATURALES
        self.system_commands = {
            "es": {
                "sube volumen": self._volume_up,
                "baja volumen": self._volume_down,
                "silencia": self._mute,
                "volumen": self._volume_specific,
                "apaga": self._shutdown,
                "apaga pc": self._shutdown,
                "reinicia": self._restart,
                "cierra sesión": self._logout,
                "cierra ventana": self._close_window,
                "captura pantalla": self._screenshot,
                "salir": self._exit_eva
            },
            "en": {
                "volume up": self._volume_up,
                "volume down": self._volume_down,
                "mute": self._mute,
                "volume": self._volume_specific,
                "shutdown": self._shutdown,
                "restart": self._restart,
                "logout": self._logout,
                "close window": self._close_window,
                "screenshot": self._screenshot,
                "exit": self._exit_eva
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
        commands = self.system_commands.get(self.lang, {})
        
        # Verificar confirmaciones pendientes
        if hasattr(self.processor, 'pending_command') and self.processor.pending_command:
            if text_lower in ["sí", "si", "yes", "y"]:
                logger.info(f"✅ SystemCommandHandler detectó confirmación: '{text_lower}'")
                return True
            elif text_lower in ["no", "n", "cancel", "cancelar"]:
                logger.info(f"✅ SystemCommandHandler detectó cancelación: '{text_lower}'")
                return True
        
        logger.info(f"🔍 SystemCommandHandler: idioma={self.lang}, comandos={list(commands.keys())}")
        logger.info(f"🔍 SystemCommandHandler: buscando en '{text_lower}'")
        
        # Verificar coincidencias EXACTAS - filosofía "1 comando = 1 función"
        for cmd in commands.keys():
            # Solo comandos exactos o que empiecen con el comando + espacio
            if text_lower == cmd or text_lower.startswith(cmd + " "):
                logger.info(f"✅ SystemCommandHandler detectó comando EXACTO: '{cmd}' en '{text_lower}'")
                return True
        
        logger.info(f"❌ SystemCommandHandler: NO detectó ningún comando en '{text_lower}'")
        return False
    
    def handle(self, text: str, chat_window) -> bool:
        """Maneja el comando de sistema"""
        try:
            text_lower = text.lower().strip()
            
            # Manejar confirmaciones pendientes
            if hasattr(self.processor, 'pending_command') and self.processor.pending_command:
                if text_lower in ["sí", "si", "yes", "y"]:
                    return self._execute_pending_command(chat_window)
                elif text_lower in ["no", "n", "cancel", "cancelar"]:
                    return self._cancel_pending_command(chat_window)
            
            commands = self.system_commands.get(self.lang, {})
            
            # Buscar comando exacto
            for command, handler in commands.items():
                if text_lower == command or text_lower.startswith(command + " "):
                    # Para volumen específico, pasar el texto completo
                    if command in ["volumen", "volume"]:
                        return handler(chat_window, text)
                    else:
                        return handler(chat_window)
            
            return False
            
        except Exception as e:
            logger.error(f"Error en comando de sistema: {str(e)}")
            error_msg = "Error ejecutando comando de sistema"
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _volume_up(self, chat_window) -> bool:
        """Sube el volumen del sistema"""
        try:
            if HAS_PYAUTOGUI:
                pyautogui.press("volumeup")
            else:
                _native_press("volumeup")
            response = self.language_manager.get_text("responses.volume_increased")
            chat_window.add_message(response, is_user=False)
            logger.info("Comando ejecutado: Subir volumen")
            return True
        except Exception as e:
            logger.error(f"Error subiendo volumen: {e}")
            error_msg = self.language_manager.get_text("responses.volume_error")
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _volume_down(self, chat_window) -> bool:
        """Baja el volumen del sistema"""
        try:
            if HAS_PYAUTOGUI:
                pyautogui.press("volumedown")
            else:
                _native_press("volumedown")
            response = self.language_manager.get_text("responses.volume_decreased")
            chat_window.add_message(response, is_user=False)
            logger.info("Comando ejecutado: Bajar volumen")
            return True
        except Exception as e:
            logger.error(f"Error bajando volumen: {e}")
            error_msg = self.language_manager.get_text("responses.volume_error")
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _mute(self, chat_window) -> bool:
        """Silencia el audio del sistema"""
        try:
            if HAS_PYAUTOGUI:
                pyautogui.press("volumemute")
            else:
                _native_press("volumemute")
            response = self.language_manager.get_text("responses.audio_muted")
            chat_window.add_message(response, is_user=False)
            logger.info("Comando ejecutado: Silenciar audio")
            return True
        except Exception as e:
            logger.error(f"Error silenciando audio: {e}")
            error_msg = self.language_manager.get_text("responses.volume_error")
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _volume_specific(self, chat_window, text: str = "") -> bool:
        """Establece volumen específico (ej: volumen 45, volume 70)"""
        try:
            import re
            
            # Extraer número del comando
            volume_match = re.search(r'(?:volumen|volume)\s+(\d+)', text.lower())
            if not volume_match:
                error_msg = self.language_manager.get_text("responses.specify_volume")
                chat_window.add_message(error_msg, is_user=False)
                return True
            
            target_volume = int(volume_match.group(1))
            
            if not (0 <= target_volume <= 100):
                error_msg = self.language_manager.get_text("responses.volume_range_error")
                chat_window.add_message(error_msg, is_user=False)
                return True
            
            # Establecer volumen usando método simple
            self._set_volume_simple(target_volume, chat_window)
            return True
            
        except Exception as e:
            logger.error(f"Error estableciendo volumen específico: {e}")
            error_msg = self.language_manager.get_text("responses.volume_error")
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _set_volume_simple(self, target_volume: int, chat_window):
        """Establece volumen específico usando teclas"""
        try:
            # Método simple: resetear a 0 y subir al nivel deseado
            # Bajar completamente
            for _ in range(50):
                if HAS_PYAUTOGUI:
                    pyautogui.press("volumedown")
                else:
                    _native_press("volumedown")

            # Subir al nivel deseado (cada pulsación ≈ 2%)
            presses_needed = target_volume // 2
            for _ in range(presses_needed):
                if HAS_PYAUTOGUI:
                    pyautogui.press("volumeup")
                else:
                    _native_press("volumeup")

            response = self.language_manager.get_text("responses.volume_set", volume=target_volume)
            chat_window.add_message(response, is_user=False)
            logger.info(f"Volumen establecido: {target_volume}%")
            
        except Exception as e:
            logger.error(f"Error estableciendo volumen: {e}")
            error_msg = self.language_manager.get_text("responses.volume_error")
            chat_window.add_message(error_msg, is_user=False)
    
    def _shutdown(self, chat_window) -> bool:
        """Apaga el sistema (con confirmación)"""
        try:
            confirm_msg = self.language_manager.get_text("responses.confirm_shutdown")
            chat_window.add_message(confirm_msg, is_user=False)
            
            # Establecer estado de confirmación pendiente
            self.processor.pending_command = "shutdown"
            logger.info("Comando de apagado solicitado (requiere confirmación)")
            return True
        except Exception as e:
            logger.error(f"Error en comando de apagado: {e}")
            error_msg = self.language_manager.get_text("responses.shutdown_error")
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _restart(self, chat_window) -> bool:
        """Reinicia el sistema (con confirmación)"""
        try:
            confirm_msg = self.language_manager.get_text("responses.confirm_restart")
            chat_window.add_message(confirm_msg, is_user=False)
            
            # Establecer estado de confirmación pendiente
            self.processor.pending_command = "restart"
            logger.info("Comando de reinicio solicitado (requiere confirmación)")
            return True
        except Exception as e:
            logger.error(f"Error en comando de reinicio: {e}")
            error_msg = self.language_manager.get_text("responses.restart_error")
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _logout(self, chat_window) -> bool:
        """Cierra la sesión (con confirmación)"""
        try:
            confirm_msg = self.language_manager.get_text("responses.confirm_logout")
            chat_window.add_message(confirm_msg, is_user=False)
            
            # Establecer estado de confirmación pendiente
            self.processor.pending_command = "logout"
            logger.info("Comando de cierre de sesión solicitado (requiere confirmación)")
            return True
        except Exception as e:
            logger.error(f"Error en comando de cierre de sesión: {e}")
            error_msg = self.language_manager.get_text("responses.logout_error")
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _execute_pending_command(self, chat_window) -> bool:
        """Ejecuta el comando pendiente confirmado"""
        try:
            command = self.processor.pending_command
            self.processor.pending_command = None  # Limpiar estado
            
            if command == "shutdown":
                # Ejecutar apagado real
                import subprocess
                msg = self.language_manager.get_text("responses.shutting_down")
                chat_window.add_message(msg, is_user=False)
                
                subprocess.run(["shutdown", "/s", "/t", "5"], shell=True)
                logger.info("Sistema apagándose en 5 segundos")
                
            elif command == "restart":
                # Ejecutar reinicio real
                import subprocess
                msg = self.language_manager.get_text("responses.restarting_system")
                chat_window.add_message(msg, is_user=False)
                
                subprocess.run(["shutdown", "/r", "/t", "5"], shell=True)
                logger.info("Sistema reiniciándose en 5 segundos")
                
            elif command == "logout":
                # Ejecutar cierre de sesión real
                import subprocess
                msg = self.language_manager.get_text("responses.logging_out")
                chat_window.add_message(msg, is_user=False)
                
                subprocess.run(["shutdown", "/l"], shell=True)
                logger.info("Cerrando sesión del usuario")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ejecutando comando pendiente: {str(e)}")
            self.processor.pending_command = None
            error_msg = self.language_manager.get_text("responses.error_executing_command")
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _cancel_pending_command(self, chat_window) -> bool:
        """Cancela el comando pendiente"""
        try:
            self.processor.pending_command = None
            msg = self.language_manager.get_text("responses.command_cancelled")
            chat_window.add_message(msg, is_user=False)
            
            logger.info("Comando pendiente cancelado por el usuario")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelando comando: {str(e)}")
            return True
    
    def _close_window(self, chat_window) -> bool:
        """Cierra la ventana activa"""
        try:
            if HAS_PYAUTOGUI:
                pyautogui.hotkey("alt", "f4")
            else:
                _native_hotkey("alt", "f4")
            msg = self.language_manager.get_text("responses.closing_window")
            chat_window.add_message(msg, is_user=False)
            logger.info("Comando ejecutado: Cerrar ventana")
            return True
        except Exception as e:
            logger.error(f"Error cerrando ventana: {e}")
            error_msg = "Error cerrando ventana"
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _screenshot(self, chat_window) -> bool:
        """Toma captura de pantalla"""
        try:
            import os
            import datetime
            
            # Crear carpeta de capturas si no existe
            screenshots_dir = os.path.join(os.path.expanduser("~"), "Pictures", "EVA_Screenshots")
            os.makedirs(screenshots_dir, exist_ok=True)
            
            # Nombre de archivo con timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"EVA_Screenshot_{timestamp}.png"
            filepath = os.path.join(screenshots_dir, filename)
            
            # Tomar captura
            if HAS_PYAUTOGUI:
                screenshot = pyautogui.screenshot()
            else:
                screenshot = _native_screenshot()
                if screenshot is None:
                    # Fallback de emergencia: usar ctypes directamente
                    import win32gui
                    import win32ui
                    import win32con
                    hwnd = win32gui.GetDesktopWindow()
                    wDC = win32gui.GetWindowDC(hwnd)
                    dcObj = win32ui.CreateDCFromHandle(wDC)
                    cDC = dcObj.CreateCompatibleDC()
                    dataBitMap = win32ui.CreateBitmap()
                    dataBitMap.CreateCompatibleBitmap(dcObj, 1920, 1080)
                    cDC.SelectObject(dataBitMap)
                    cDC.BitBlt((0, 0), (1920, 1080), dcObj, (0, 0), win32con.SRCCOPY)
                    import PIL.Image
                    screenshot = PIL.Image.frombuffer("RGB", (1920, 1080), dataBitMap.GetBitmapBits(True), "raw", "BGRX")
                    win32gui.DeleteObject(dataBitMap.GetHandle())
                    dcObj.DeleteDC()
                    cDC.DeleteDC()
                    win32gui.ReleaseDC(hwnd, wDC)
            screenshot.save(filepath)
            
            response = self.language_manager.get_text("responses.screenshot_saved", filename=filename)
            chat_window.add_message(response, is_user=False)
            logger.info(f"Captura de pantalla guardada: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error tomando captura: {e}")
            error_msg = self.language_manager.get_text("responses.screenshot_error")
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _exit_eva(self, chat_window) -> bool:
        """Sale de EVA"""
        try:
            import os
            import threading
            import time
            
            response = self.language_manager.get_text("responses.closing_eva")
            chat_window.add_message(response, is_user=False)
            
            # Cerrar EVA después de un breve delay
            def close_eva():
                time.sleep(1)
                os._exit(0)
            
            threading.Thread(target=close_eva, daemon=True).start()
            logger.info("Comando ejecutado: Salir de EVA")
            return True
            
        except Exception as e:
            logger.error(f"Error saliendo de EVA: {e}")
            return True