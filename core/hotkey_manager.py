import logging
import os
import subprocess
import threading
import time
import webbrowser

import keyboard

from PySide6.QtCore import QTimer

logger = logging.getLogger("EVA")


class HotkeyManager:
    def __init__(self, eva_instance, config):
        self.eva = eva_instance
        self.config = config
        self.running = False
        self.thread = None
        self.listening_active = True  # Por defecto activo
        self.custom_hotkeys = {}

        # Asegurar que exista la configuración de hotkeys
        self.config.setdefault(
            "hotkeys",
            {
                "activar": "ctrl+alt+e",
                "mostrar_chat": "ctrl+alt+c",
                "ocultar_chat": "ctrl+alt+h",
                "salir": "ctrl+alt+q",
                "abrir_eva": "win+e",  # Win+E global para abrir EVA
                "custom": [],
            },
        )

        # Cargar abrir_eva desde config si ya existe
        self._abrir_eva_hotkey = self.config["hotkeys"].get("abrir_eva", "win+e")

    def start(self):
        """Inicia el gestor de hotkeys en un hilo separado"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._listen, daemon=True)
            self.thread.start()
            logger.info("Gestor de hotkeys iniciado")

    def stop(self):
        """Detiene el gestor de hotkeys"""
        if self.running:
            self.running = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1.0)
            logger.info("Gestor de hotkeys detenido")

    def _listen(self):
        """Bucle principal para escuchar hotkeys"""
        try:
            # Registrar hotkeys básicas
            keyboard.add_hotkey(
                self.config["hotkeys"]["activar"], self.toggle_listening
            )
            keyboard.add_hotkey(
                self.config["hotkeys"]["mostrar_chat"], self.show_chat_window
            )
            keyboard.add_hotkey(
                self.config["hotkeys"]["ocultar_chat"], self.hide_chat_window
            )
            keyboard.add_hotkey(self.config["hotkeys"]["salir"], self.cleanup_and_exit)

            # Win+E global para abrir EVA (con supresión para evitar conflicto con Explorer)
            try:
                keyboard.add_hotkey(
                    self._abrir_eva_hotkey,
                    self._abrir_eva,
                    suppress=True
                )
                logger.info(f"Hotkey '{self._abrir_eva_hotkey}' registrada para abrir EVA")
            except Exception as e:
                logger.warning(f"No se pudo registrar hotkey '{self._abrir_eva_hotkey}': {e}")

            # Registrar hotkeys personalizadas
            for hotkey_cfg in self.config["hotkeys"].get("custom", []):
                keys = hotkey_cfg["keys"]

                # Creamos una función lambda que capture los parámetros necesarios
                def action(h=hotkey_cfg):
                    return self.execute_custom_command(h)

                keyboard.add_hotkey(keys, action)
                logger.info(f"Hotkey personalizada registrada: {keys} -> {hotkey_cfg}")

            logger.info(f"Hotkeys básicas registradas: {self.config['hotkeys']}")

            # Mantener el hilo activo
            while self.running:
                time.sleep(0.5)

        except Exception as e:
            logger.error(f"Error en gestor de hotkeys: {str(e)}")
        finally:
            keyboard.unhook_all()

    def execute_custom_command(self, hotkey_cfg):
        """Ejecuta un comando personalizado basado en la configuración de hotkey"""
        try:
            cmd_type = hotkey_cfg["type"]
            target = hotkey_cfg["target"]

            if cmd_type == "program":
                self.launch_program(target)
            elif cmd_type == "folder":
                self.open_folder(target)
            elif cmd_type == "website":
                self.open_website(target)
            elif cmd_type == "command":
                self.execute_special_command(target)
            else:
                logger.warning(f"Tipo de comando no reconocido: {cmd_type}")
        except Exception as e:
            logger.error(f"Error ejecutando comando personalizado: {str(e)}")

    def launch_program(self, program_key):
        """Lanza un programa según la clave proporcionada"""
        if program_key in self.config["programas"]:
            path = self.config["programas"][program_key]
            try:
                # Usar subprocess para evitar bloquear
                subprocess.Popen(path)
                logger.info(f"Programa lanzado: {program_key} -> {path}")

                # Notificar en la UI
                if self.eva.chat_window:
                    self.eva.chat_window.add_message(
                        f"Abriendo programa: {program_key}", is_user=False
                    )
            except Exception as e:
                logger.error(f"Error al lanzar programa: {str(e)}")
        else:
            logger.warning(f"Clave de programa no encontrada: {program_key}")

    def open_folder(self, folder_key):
        """Abre una carpeta según la clave proporcionada"""
        if folder_key in self.config["carpetas"]:
            path = self.config["carpetas"][folder_key]
            try:
                os.startfile(path)
                logger.info(f"Carpeta abierta: {folder_key} -> {path}")

                # Notificar en la UI
                if self.eva.chat_window:
                    self.eva.chat_window.add_message(
                        f"Abriendo carpeta: {folder_key}", is_user=False
                    )
            except Exception as e:
                logger.error(f"Error al abrir carpeta: {str(e)}")
        else:
            logger.warning(f"Clave de carpeta no encontrada: {folder_key}")

    def open_website(self, website_key):
        """Abre un sitio web según la clave proporcionada"""
        if website_key in self.config["websites"]:
            url = self.config["websites"][website_key]
            try:
                webbrowser.open(url)
                logger.info(f"Sitio web abierto: {website_key} -> {url}")

                # Notificar en la UI
                if self.eva.chat_window:
                    self.eva.chat_window.add_message(
                        f"Abriendo sitio web: {website_key}", is_user=False
                    )
            except Exception as e:
                logger.error(f"Error al abrir sitio web: {str(e)}")
        else:
            logger.warning(f"Clave de sitio web no encontrada: {website_key}")

    def execute_special_command(self, command_key):
        """Ejecuta un comando especial"""
        try:
            if self.eva.command_processor:
                # Simulamos un comando de voz
                fake_command = f"hotkey:{command_key}"
                self.eva.command_processor.process_command(
                    fake_command, self.eva.chat_window
                )
                logger.info(f"Comando especial ejecutado: {command_key}")
        except Exception as e:
            logger.error(f"Error ejecutando comando especial: {str(e)}")

    def toggle_listening(self):
        """Activa/desactiva el reconocimiento de voz"""
        self.listening_active = not self.listening_active
        status = "activado" if self.listening_active else "desactivado"
        logger.info(f"Reconocimiento de voz {status}")

        # Actualizar el motor de voz si existe
        if hasattr(self.eva, "voice_engine"):
            self.eva.voice_engine.toggle_listening()

        # Mostrar notificación en la UI
        if self.eva.chat_window:
            self.eva.chat_window.add_message(f"Modo de escucha {status}", is_user=False)

        # Reproducir sonido de notificación
        if hasattr(self.eva, "speech"):
            self.eva.speech.speak(f"Modo voz {status}")

    def show_chat_window(self):
        """Muestra la ventana de chat"""
        if hasattr(self.eva, "chat_window"):
            self.eva.chat_window.show()
            self.eva.chat_window.activateWindow()
            logger.info("Ventana de chat mostrada")

    def hide_chat_window(self):
        """Oculta la ventana de chat"""
        if hasattr(self.eva, "chat_window"):
            self.eva.chat_window.hide()
            logger.info("Ventana de chat ocultada")

    def cleanup_and_exit(self):
        """Cierra la aplicación completamente"""
        logger.info("Solicitado cierre por hotkey")
        if hasattr(self.eva, "cleanup"):
            self.eva.cleanup()
        if hasattr(self.eva, "application"):
            self.eva.application.quit()

    def _abrir_eva(self):
        """Win+E handler: muestra la ventana completa o mini bar"""
        try:
            eva = self.eva
            if not eva:
                return
            chat = getattr(eva, 'chat_window', None)
            mini = getattr(eva, 'mini_bar', None)

            # Si mini bar existe y está configurado para usarlo
            use_mini = eva.config.get("use_mini_mode", False) if hasattr(eva, 'config') else False

            if use_mini and mini:
                if mini.isVisible():
                    # Alternar: si ya visible y chat también, ocultar todo
                    if chat and chat.isVisible():
                        mini.hide()
                        chat.hide()
                    else:
                        mini.hide()
                else:
                    # Ocultar chat si está visible, mostrar mini
                    if chat and chat.isVisible():
                        chat.hide()
                    mini.show()
                    mini.activateWindow()
                    mini.raise_()
                    mini.message_input.setFocus()
            elif chat:
                if chat.isVisible():
                    chat.hide()
                else:
                    chat.show()
                    chat.activateWindow()
                    chat.raise_()
                    QTimer.singleShot(100, lambda: chat.message_input.setFocus() if hasattr(chat, 'message_input') else None)
            logger.info("Hotkey abrir_eva ejecutada")
        except Exception as e:
            logger.error(f"Error en abrir_eva: {e}")

    def update_config(self, config):
        pass
