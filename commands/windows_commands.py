"""
Comandos de Windows unificados para EVA
Maneja WiFi, Bluetooth y brillo con comandos naturales
Filosofía: 1 comando = 1 función
"""

import logging
import subprocess

from utils.bilingual_command import BilingualCommand
from utils.threading_utils import submit_background_task

WIFI_TIMEOUT = 10
BT_TIMEOUT = 15

logger = logging.getLogger("EVA")




class WindowsCommandHandler:
    """Handler unificado para comandos de Windows (WiFi, Bluetooth, Brillo)"""
    
    def __init__(self, processor):
        self.processor = processor
        self.config = processor.config
        self.language_manager = processor.language_manager
        
        # Comandos de Windows unificados con filosofía natural
        self.commands = {
            # Comandos WiFi
            BilingualCommand("activa wifi", "enable wifi"): self._enable_wifi,
            BilingualCommand("desactiva wifi", "disable wifi"): self._disable_wifi,
            BilingualCommand("estado wifi", "wifi status"): self._wifi_status,
            
            # Comandos Bluetooth
            BilingualCommand("activa bluetooth", "enable bluetooth"): self._enable_bluetooth,
            BilingualCommand("desactiva bluetooth", "disable bluetooth"): self._disable_bluetooth,
            BilingualCommand("estado bluetooth", "bluetooth status"): self._bluetooth_status,
            
            # Comandos Brillo
            BilingualCommand("sube brillo", "brightness up"): self._brightness_up,
            BilingualCommand("baja brillo", "brightness down"): self._brightness_down,
        }
    
    def can_handle(self, text: str) -> bool:
        """Verifica si puede manejar el comando"""
        text_lower = text.lower().strip()
        
        # Verificar comandos de Windows
        for bilingual_cmd in self.commands.keys():
            if bilingual_cmd.matches(text_lower):
                return True
        
        # Verificar brillo específico (ej: "brillo 70", "brightness 50")
        if any(word in text_lower for word in ["brillo", "brightness"]) and any(char.isdigit() for char in text_lower):
            return True
        
        return False
    
    def handle(self, text: str, chat_window) -> bool:
        """Maneja el comando de Windows"""
        try:
            text_lower = text.lower().strip()
            
            # Verificar brillo específico primero
            import re
            brightness_match = re.search(r'(?:brillo|brightness)\s+(\d+)', text_lower)
            if brightness_match:
                target_brightness = int(brightness_match.group(1))
                if 0 <= target_brightness <= 100:
                    submit_background_task(
                        self._set_brightness,
                        target_brightness, chat_window,
                        name="set_brightness"
                    )
                    return True
                else:
                    error_msg = "El brillo debe estar entre 0 y 100" if self.processor.config.get("language", "es") == "es" else "Brightness must be between 0 and 100"
                    chat_window.add_message(error_msg, is_user=False)
                    return True
            
            # Buscar comando coincidente
            for bilingual_cmd, handler_func in self.commands.items():
                if bilingual_cmd.matches(text_lower):
                    logger.info(f"🪟 Ejecutando comando de Windows: {bilingual_cmd}")
                    return handler_func(chat_window)
            
            return False
            
        except Exception as e:
            logger.error(f"Error en comando de Windows: {str(e)}")
            error_msg = self.language_manager.get_text("responses.windows_control_error", 
                                                     default="Error en comando de Windows")
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    # ==================
    # COMANDOS WIFI
    # ==================
    
    def _enable_wifi(self, chat_window) -> bool:
        """Activa WiFi"""
        try:
            processing_msg = self.language_manager.get_text("responses.processing_wifi_command", 
                                                          default="🔄 Activando WiFi...")
            chat_window.add_message(processing_msg, is_user=False)
            
            submit_background_task(
                self._execute_wifi_command,
                "enable", chat_window,
                name="enable_wifi"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error activando WiFi: {str(e)}")
            return False
    
    def _disable_wifi(self, chat_window) -> bool:
        """Desactiva WiFi"""
        try:
            processing_msg = self.language_manager.get_text("responses.processing_wifi_command", 
                                                          default="🔄 Desactivando WiFi...")
            chat_window.add_message(processing_msg, is_user=False)
            
            submit_background_task(
                self._execute_wifi_command,
                "disable", chat_window,
                name="disable_wifi"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error desactivando WiFi: {str(e)}")
            return False
    
    def _wifi_status(self, chat_window) -> bool:
        """Verifica estado WiFi"""
        try:
            submit_background_task(
                self._execute_wifi_command,
                "status", chat_window,
                name="wifi_status"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error verificando WiFi: {str(e)}")
            return False
    
    def _execute_wifi_command(self, action: str, chat_window):
        """Ejecuta comandos WiFi usando netsh"""
        try:
            if action == "enable":
                result = subprocess.run(
                    ["netsh", "interface", "set", "interface", "Wi-Fi", "enable"],
                    capture_output=True, text=True, timeout=WIFI_TIMEOUT
                )
                
                if result.returncode == 0:
                    response = self.language_manager.get_text("responses.wifi_enabled", 
                                                            default="✅ WiFi activado")
                    logger.info("WiFi activado correctamente")
                else:
                    response = self.language_manager.get_text("responses.wifi_error_enable", 
                                                            default="❌ Error activando WiFi")
                    logger.error(f"Error activando WiFi: {result.stderr}")
                    
            elif action == "disable":
                result = subprocess.run(
                    ["netsh", "interface", "set", "interface", "Wi-Fi", "disable"],
                    capture_output=True, text=True, timeout=WIFI_TIMEOUT
                )
                
                if result.returncode == 0:
                    response = self.language_manager.get_text("responses.wifi_disabled", 
                                                            default="✅ WiFi desactivado")
                    logger.info("WiFi desactivado correctamente")
                else:
                    response = self.language_manager.get_text("responses.wifi_error_disable", 
                                                            default="❌ Error desactivando WiFi")
                    logger.error(f"Error desactivando WiFi: {result.stderr}")
                    
            elif action == "status":
                result = subprocess.run(
                    ["netsh", "wlan", "show", "interfaces"],
                    capture_output=True, text=True, timeout=WIFI_TIMEOUT
                )
                
                if result.returncode == 0:
                    output = result.stdout
                    if "connected" in output.lower() or "conectado" in output.lower():
                        # Extraer nombre de la red
                        lines = output.split('\n')
                        ssid = "Red desconocida"
                        for line in lines:
                            if "SSID" in line and "BSSID" not in line:
                                ssid = line.split(':')[-1].strip()
                                break
                        response = self.language_manager.get_text("responses.wifi_connected", 
                                                                default="📶 WiFi conectado a: {ssid}").format(ssid=ssid)
                    else:
                        response = self.language_manager.get_text("responses.wifi_disconnected", 
                                                                default="📶 WiFi desconectado")
                else:
                    response = self.language_manager.get_text("responses.wifi_error_status", 
                                                            default="❌ Error verificando WiFi")
            
            # Mostrar resultado
            self._safe_add_message(chat_window, response)
                
        except subprocess.TimeoutExpired:
            error_msg = self.language_manager.get_text("responses.wifi_timeout", 
                                                     default="⏱️ Timeout en comando WiFi")
            self._safe_add_message(chat_window, error_msg)
        except Exception as e:
            logger.error(f"Error ejecutando comando WiFi: {str(e)}")
            error_msg = self.language_manager.get_text("responses.wifi_error", 
                                                     default="❌ Error en WiFi")
            self._safe_add_message(chat_window, error_msg)
    
    # ==================
    # COMANDOS BLUETOOTH
    # ==================
    
    def _enable_bluetooth(self, chat_window) -> bool:
        """Activa Bluetooth"""
        try:
            processing_msg = self.language_manager.get_text("responses.processing_bluetooth_command", 
                                                          default="🔄 Activando Bluetooth...")
            chat_window.add_message(processing_msg, is_user=False)
            
            submit_background_task(
                self._execute_bluetooth_command,
                "enable", chat_window,
                name="enable_bluetooth"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error activando Bluetooth: {str(e)}")
            return False
    
    def _disable_bluetooth(self, chat_window) -> bool:
        """Desactiva Bluetooth"""
        try:
            processing_msg = self.language_manager.get_text("responses.processing_bluetooth_command", 
                                                          default="🔄 Desactivando Bluetooth...")
            chat_window.add_message(processing_msg, is_user=False)
            
            submit_background_task(
                self._execute_bluetooth_command,
                "disable", chat_window,
                name="disable_bluetooth"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error desactivando Bluetooth: {str(e)}")
            return False
    
    def _bluetooth_status(self, chat_window) -> bool:
        """Verifica estado Bluetooth"""
        try:
            submit_background_task(
                self._execute_bluetooth_command,
                "status", chat_window,
                name="bluetooth_status"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error verificando Bluetooth: {str(e)}")
            return False
    
    def _execute_bluetooth_command(self, action: str, chat_window):
        """Ejecuta comandos Bluetooth usando PowerShell simplificado"""
        try:
            if action == "enable":
                # PowerShell simplificado para activar Bluetooth
                powershell_cmd = """
                try {
                    Get-PnpDevice -Class Bluetooth | Enable-PnpDevice -Confirm:$false
                    Write-Output "SUCCESS"
                } catch {
                    Write-Output "ERROR: $($_.Exception.Message)"
                }
                """
                
                result = subprocess.run(
                    ["powershell", "-Command", powershell_cmd],
                    capture_output=True, text=True, timeout=BT_TIMEOUT
                )
                
                if result.returncode == 0 and "SUCCESS" in result.stdout:
                    response = self.language_manager.get_text("responses.bluetooth_enabled", 
                                                            default="✅ Bluetooth activado")
                else:
                    response = self.language_manager.get_text("responses.bluetooth_error_enable", 
                                                            default="❌ Error activando Bluetooth")
                    
            elif action == "disable":
                # PowerShell simplificado para desactivar Bluetooth
                powershell_cmd = """
                try {
                    Get-PnpDevice -Class Bluetooth | Disable-PnpDevice -Confirm:$false
                    Write-Output "SUCCESS"
                } catch {
                    Write-Output "ERROR: $($_.Exception.Message)"
                }
                """
                
                result = subprocess.run(
                    ["powershell", "-Command", powershell_cmd],
                    capture_output=True, text=True, timeout=BT_TIMEOUT
                )
                
                if result.returncode == 0 and "SUCCESS" in result.stdout:
                    response = self.language_manager.get_text("responses.bluetooth_disabled", 
                                                            default="✅ Bluetooth desactivado")
                else:
                    response = self.language_manager.get_text("responses.bluetooth_error_disable", 
                                                            default="❌ Error desactivando Bluetooth")
                    
            elif action == "status":
                # Verificar estado Bluetooth
                powershell_cmd = """
                $bluetooth = Get-PnpDevice -Class Bluetooth | Where-Object {$_.Status -eq "OK"}
                if ($bluetooth) {
                    Write-Output "ENABLED"
                } else {
                    Write-Output "DISABLED"
                }
                """
                
                result = subprocess.run(
                    ["powershell", "-Command", powershell_cmd],
                    capture_output=True, text=True, timeout=BT_TIMEOUT
                )
                
                if result.returncode == 0:
                    state = result.stdout.strip()
                    if "ENABLED" in state:
                        response = self.language_manager.get_text("responses.bluetooth_on", 
                                                                default="🔵 Bluetooth activado")
                    else:
                        response = self.language_manager.get_text("responses.bluetooth_off", 
                                                                default="⚫ Bluetooth desactivado")
                else:
                    response = self.language_manager.get_text("responses.bluetooth_error_status", 
                                                            default="❌ Error verificando Bluetooth")
            
            # Mostrar resultado
            self._safe_add_message(chat_window, response)
                
        except subprocess.TimeoutExpired:
            error_msg = self.language_manager.get_text("responses.bluetooth_timeout", 
                                                     default="⏱️ Timeout en comando Bluetooth")
            self._safe_add_message(chat_window, error_msg)
        except Exception as e:
            logger.error(f"Error ejecutando comando Bluetooth: {str(e)}")
            error_msg = self.language_manager.get_text("responses.bluetooth_error", 
                                                     default="❌ Error en Bluetooth")
            self._safe_add_message(chat_window, error_msg)
    
    # ==================
    # COMANDOS BRILLO
    # ==================

    BRIGHTNESS_STEP = 10

    def _brightness_up(self, chat_window) -> bool:
        submit_background_task(
            self._adjust_brightness, self.BRIGHTNESS_STEP, chat_window,
            name="brightness_up"
        )
        return True

    def _brightness_down(self, chat_window) -> bool:
        submit_background_task(
            self._adjust_brightness, -self.BRIGHTNESS_STEP, chat_window,
            name="brightness_down"
        )
        return True

    def _set_brightness(self, target_brightness: int, chat_window):
        """Establece brillo específico usando WMI"""
        try:
            powershell_cmd = f"""
            try {{
                (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{target_brightness})
                Write-Output "SUCCESS"
            }} catch {{
                Write-Output "ERROR: $($_.Exception.Message)"
            }}
            """

            result = subprocess.run(
                ["powershell", "-Command", powershell_cmd],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0 and "SUCCESS" in result.stdout:
                response = self.language_manager.get_text("responses.brightness_set",
                                                        default="☀️ Brillo establecido a {brightness}%").format(brightness=target_brightness)
                logger.info(f"🪟 Brillo establecido: {target_brightness}%")
            else:
                response = self.language_manager.get_text("responses.brightness_error",
                                                        default="❌ Error estableciendo brillo")
                logger.error(f"Error estableciendo brillo: {result.stderr}")

            self._safe_add_message(chat_window, response)

        except Exception as e:
            logger.error(f"Error estableciendo brillo específico: {str(e)}")
            error_msg = self.language_manager.get_text("responses.brightness_error",
                                                     default="❌ Error en brillo")
            self._safe_add_message(chat_window, error_msg)

    def _adjust_brightness(self, delta: int, chat_window):
        """Ajusta brillo relativo vía WMI"""
        try:
            cmd = """
            $current = (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness
            $new = [Math]::Max(0, [Math]::Min(100, $current + {delta}))
            Write-Output $new
            """.format(delta=delta)
            result = subprocess.run(
                ["powershell", "-Command", cmd],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip().isdigit():
                new_val = int(result.stdout.strip())
                self._set_brightness(new_val, chat_window)
            else:
                self._safe_add_message(chat_window, "❌ Error leyendo brillo actual")
        except Exception as e:
            logger.error(f"Error ajustando brillo: {e}")
    
    # ==================
    # UTILIDADES
    # ==================
    
    def _safe_add_message(self, chat_window, message):
        """Añade mensaje de forma segura desde hilos secundarios"""
        try:
            if hasattr(chat_window, 'update_message_signal'):
                chat_window.update_message_signal.emit(message, False)
            else:
                chat_window.add_message(message, is_user=False)
        except Exception as e:
            logger.error(f"Error añadiendo mensaje: {str(e)}")
