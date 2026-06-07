import logging
import os
import webbrowser
from datetime import datetime

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QFrame,
                               QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QSlider, QVBoxLayout,
                               QWidget, QScrollArea, QListWidget)

from core.config_manager_unified import config_manager

try:
    from core.licensing import LicenseValidator
except ImportError:
    LicenseValidator = None

try:
    from ui.custom_commands_dialog import CustomCommandsDialog
except ImportError:
    try:
        from ui.custom_commands_dialog_simple import CustomCommandsDialog
    except ImportError:
        CustomCommandsDialog = None

# GPU config dialog removed - obsolete after Piper TTS migration

try:
    from utils.hardware import configure_hardware
except ImportError:
    def configure_hardware():
        pass

logger = logging.getLogger("EVA")


class SettingsWindow(QDialog):
    settings_updated = Signal(dict)
    # gpu_settings_updated signal removed - obsolete after Piper TTS migration

    def __init__(self, config, language_manager, chat_window, parent=None):
        super().__init__(parent)
        self.es_button = None
        self.en_button = None
        self.license_group = None
        self.license_label = None
        self.license_input = None
        self.license_status = None
        self.validate_btn = None
        self.buy_btn = None
        self.remove_license_btn = None
        self.commands_group = None
        self.custom_cmd_btn = None
        self.custom_cmd_desc = None
        self.general_group = None
        self.name_label = None
        self.name_input = None
        self.auto_start_label = None
        self.auto_start_check = None
        self.minimize_label = None
        self.minimize_check = None
        self.sensitivity_label = None
        self.sensitivity_slider = None
        self.voice_group = None
        self.voice_label = None
        self.voice_combo = None
        self.voice_model_label = None
        self.voice_model_combo = None
        self.volume_label = None
        self.volume_slider = None
        self.coqui_label = None
        self.coqui_check = None
        self.auto_listen_label = None
        self.auto_listen_check = None
        self.vad_mode_combo = None
        # Hardware group removed - obsolete after Piper TTS migration
        # GPU label removed - obsolete after Piper TTS migration
        # GPU UI elements removed - obsolete after Piper TTS migration
        self.advanced_gpu_btn = None
        self.save_btn = None
        self.cancel_btn = None
        self.config = config
        self.language_manager = language_manager
        self.chat_window = chat_window
        self.license_validator = LicenseValidator() if LicenseValidator else None

        # Configurar ventana para que esté por encima de la ventana principal
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        # Fix window title - use translation key
        self.setWindowTitle(self.language_manager.get_text("ui.settings_window.title"))
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        
        # Configurar icono de la ventana usando icon.ico
        icon_path = os.path.join("resources", "icon.ico")
        if os.path.exists(icon_path):
            from PySide6.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))
        else:
            logger.warning("Icono de ventana no encontrado en: " + icon_path)

        # Tamaño ajustado y redimensionable
        self.setMinimumSize(450, 280)
        self.resize(600, 450)  # Tamaño inicial más adecuado

        # Layout principal de la ventana
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(4)
        self.layout.setContentsMargins(8, 8, 8, 4)

        # Contenedor para el contenido que será scrollable
        self.scrollable_content_widget = QWidget()
        self.scrollable_content_widget.setStyleSheet("background-color: rgb(25, 25, 35);")
        self.scrollable_content_layout = QVBoxLayout(self.scrollable_content_widget)
        self.scrollable_content_layout.setSpacing(4)
        self.scrollable_content_layout.setContentsMargins(0, 0, 0, 0)

        # QScrollArea para el contenido
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scrollable_content_widget)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        self.scroll_area.verticalScrollBar().setStyleSheet(
            """
            QScrollBar:vertical {
                border: 1px solid #4db6ac;
                background: #303040;
                width: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #00bcd4;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            """
        )

        # Estilo con colores de fondo completamente opacos
        self.setStyleSheet(
            """
            QDialog {
                background-color: rgb(25, 25, 35);
                font-family: 'Segoe UI', 'Open Sans', sans-serif;
                font-size: 13px;
                border: 2px solid #4db6ac;
                border-radius: 12px;
            }
            QGroupBox {
                font-weight: 600;
                font-size: 13px;
                color: #bb86fc;
                border: 1px solid rgba(77, 182, 172, 0.3);
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 15px;
                background-color: rgb(30, 30, 40);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 8px;
                background-color: rgb(30, 30, 40);
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
            QPushButton {
                background-color: rgba(63, 81, 181, 0.3);
                border: 1px solid rgba(63, 81, 181, 0.5);
                border-radius: 6px;
                padding: 6px 12px;
                min-height: 28px;
                font-weight: 500;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: rgba(63, 81, 181, 0.4);
                border: 1px solid rgba(63, 81, 181, 0.7);
            }
            QCheckBox {
                color: #ffffff;
                spacing: 6px;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid rgba(77, 182, 172, 0.5);
                background-color: rgb(30, 30, 40);
            }
            QCheckBox::indicator:checked {
                background-color: #00bcd4;
                border: 1px solid #ffffff;
            }
            QSlider::groove:horizontal {
                height: 7px;
                background: rgba(77, 182, 172, 0.2);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00bcd4;
                border: 1px solid rgba(0, 0, 0, 0.2);
                width: 16px;
                height: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #00bcd4;
                border-radius: 3px;
            }
            QLineEdit {
                background-color: rgb(30, 30, 40);
                border: 1px solid rgba(77, 182, 172, 0.3);
                border-radius: 5px;
                padding: 6px;
                color: #ffffff;
                font-size: 12px;
            }
            QComboBox {
                background-color: rgb(30, 30, 40);
                border: 1px solid rgba(77, 182, 172, 0.3);
                border-radius: 5px;
                padding: 5px;
                min-height: 28px;
                color: #ffffff;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: rgb(30, 30, 40);
                border: 1px solid rgba(77, 182, 172, 0.3);
                selection-background-color: rgba(0, 188, 212, 0.3);
                color: #ffffff;
            }
        """
        )

        # Conectar señal ANTES de configurar la UI
        self.language_manager.language_changed.connect(self.update_language)

        # Setup UI sections
        self.setup_language_switcher()
        self.setup_license_settings()
        self.setup_general_settings()
        self.setup_voice_settings()  # Simplified Piper TTS settings
        # Hardware settings removed - obsolete after Piper TTS migration (CPU only)
        self.setup_update_settings()  # Nueva sección para configuración de actualizaciones
        self.setup_knowledge_base_settings()  # Nueva sección para base de conocimiento
        self.setup_plugins_settings()  # Nueva sección para plugins (Tavily API key)
        self.setup_openrouter_settings()  # Nueva sección para OpenRouter AI
        self.setup_custom_commands_settings()  # Nueva sección para comandos personalizados

        # Añadir scroll area al layout principal
        self.layout.addWidget(self.scroll_area)

        # Configurar botones de acción
        self.setup_action_buttons()

        # Load current settings and license
        self.load_current_settings()
        self.load_stored_license()
        self.load_knowledge_base_settings()
        self.load_plugins_settings()
        self.load_openrouter_settings()

        # Centrar la ventana con respecto a la ventana principal
        if parent:
            self.center_on_parent(parent)

    def get_text(self, key: str, default: str = None) -> str:
        """Helper method to get translated text with VAD support"""
        try:
            # VAD-specific translations
            vad_translations = {
                "es": {
                    "ui.vad_title": "Detección de Actividad de Voz",
                    "ui.vad_description": "VAD filtra el ruido de fondo y solo procesa voz, reduciendo el uso de CPU en 60-80%.",
                    "ui.vad_mode": "Modo de Detección",
                    "ui.vad_conservative": "🛡️ Conservador - Filtrado máximo de ruido",
                    "ui.vad_balanced": "⚖️ Balanceado - Óptimo para la mayoría de entornos",
                    "ui.vad_sensitive": "🎯 Sensible - Detecta voz suave",
                    "ui.vad_test": "Probar Configuración VAD",
                    "ui.vad_mode_1_desc": "Modo sensible - detecta voz suave pero puede captar algo de ruido de fondo",
                    "ui.vad_mode_2_desc": "Modo balanceado - óptimo para la mayoría de entornos con buen filtrado de ruido",
                    "ui.vad_mode_3_desc": "Modo conservador - filtrado máximo de ruido, requiere voz clara",
                    "ui.vad_test_message": "Configuración VAD actualizada. Intenta hablar para probar la nueva configuración.\n\nModo seleccionado: {mode}\n\n{description}",
                    "ui.vad_test_preview": "Vista Previa de Configuración VAD:\n\nModo seleccionado: {mode}\n\n{description}\n\nLa configuración se aplicará al guardar.",
                    "ui.error_testing_vad": "Error probando configuración VAD"
                },
                "en": {
                    "ui.vad_title": "Voice Activity Detection",
                    "ui.vad_description": "VAD filters background noise and only processes speech, reducing CPU usage by 60-80%.",
                    "ui.vad_mode": "Detection Mode",
                    "ui.vad_conservative": "🛡️ Conservative - Maximum noise filtering",
                    "ui.vad_balanced": "⚖️ Balanced - Optimal for most environments",
                    "ui.vad_sensitive": "🎯 Sensitive - Detects quiet speech",
                    "ui.vad_test": "Test VAD Configuration",
                    "ui.vad_mode_1_desc": "Sensitive mode - detects quiet speech but may pick up some background noise",
                    "ui.vad_mode_2_desc": "Balanced mode - optimal for most environments with good noise filtering",
                    "ui.vad_mode_3_desc": "Conservative mode - maximum noise filtering, requires clear speech",
                    "ui.vad_test_message": "VAD configuration updated. Try speaking to test the new settings.\n\nSelected mode: {mode}\n\n{description}",
                    "ui.vad_test_preview": "VAD Configuration Preview:\n\nSelected mode: {mode}\n\n{description}\n\nSettings will be applied when you save.",
                    "ui.error_testing_vad": "Error testing VAD configuration"
                }
            }
            
            # Get current language
            current_lang = getattr(self.language_manager, 'current_lang', 'es')
            
            # Check if we have a VAD translation for this key
            if key in vad_translations.get(current_lang, {}):
                return vad_translations[current_lang][key]
            
            # Fall back to language manager
            return self.language_manager.get_text(key, default)
        except Exception as e:
            logger.error(f"Error getting text for key {key}: {str(e)}")
            return default or key

    def center_on_parent(self, parent):
        """Centra la ventana de ajustes sobre la ventana principal y asegura visibilidad en pantalla."""
        self.adjustSize()

        # Obtener la geometría global del área cliente de la ventana principal
        parent_global_rect = parent.geometry()

        # Obtener la geometría de la pantalla disponible
        screen_rect = parent.screen().availableGeometry()

        # Calcular la posición x para centrar horizontalmente sobre el padre
        x = parent_global_rect.x() + (parent_global_rect.width() - self.width()) // 2

        # Calcular la posición y para que la ventana de configuración inicie justo debajo de la barra de título del padre
        y = parent_global_rect.y() + 60

        # Asegurarse de que la ventana esté completamente dentro de la pantalla
        x = max(screen_rect.left(), min(x, screen_rect.right() - self.width()))

        if y < screen_rect.top() + 20:
            y = screen_rect.top() + 20

        if y + self.height() > screen_rect.bottom() - 20:
            y = screen_rect.bottom() - self.height() - 20
            if y < screen_rect.top() + 20:
                y = screen_rect.top() + 20

        self.move(x, y)

    def setup_language_switcher(self):
        lang_frame = QFrame()
        lang_layout = QHBoxLayout(lang_frame)
        lang_layout.setContentsMargins(0, 0, 0, 0)

        lang_layout.addWidget(QLabel(self.language_manager.get_text("ui.language") + ":"))

        self.es_button = QPushButton(self.language_manager.get_text("ui.spanish"))
        self.es_button.setCheckable(True)
        self.es_button.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(63, 81, 181, 0.3);
                border: 1px solid rgba(63, 81, 181, 0.5);
                border-radius: 6px;
                padding: 6px 12px;
                min-height: 28px;
                font-weight: 500;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: rgba(63, 81, 181, 0.4);
                border: 1px solid rgba(63, 81, 181, 0.7);
            }
            QPushButton:checked {
                background-color: rgba(0, 188, 212, 0.6);
                border: 2px solid rgba(0, 188, 212, 0.9);
                font-weight: 600;
                color: #ffffff;
            }
        """
        )
        self.es_button.clicked.connect(lambda: self.change_language("es"))

        self.en_button = QPushButton(self.language_manager.get_text("ui.english"))
        self.en_button.setCheckable(True)
        self.en_button.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(63, 81, 181, 0.3);
                border: 1px solid rgba(63, 81, 181, 0.5);
                border-radius: 6px;
                padding: 6px 12px;
                min-height: 28px;
                font-weight: 500;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: rgba(63, 81, 181, 0.4);
                border: 1px solid rgba(63, 81, 181, 0.7);
            }
            QPushButton:checked {
                background-color: rgba(0, 188, 212, 0.6);
                border: 2px solid rgba(0, 188, 212, 0.9);
                font-weight: 600;
                color: #ffffff;
            }
        """
        )
        self.en_button.clicked.connect(lambda: self.change_language("en"))

        # Set initial button states properly
        current_lang = self.config.get("language", "es")
        if current_lang == "es":
            self.es_button.setChecked(True)
            self.en_button.setChecked(False)
        else:
            self.es_button.setChecked(False)
            self.en_button.setChecked(True)

        lang_layout.addWidget(self.es_button)
        lang_layout.addWidget(self.en_button)
        lang_layout.addStretch()

        # Añadir al contenido scrollable
        self.scrollable_content_layout.addWidget(lang_frame)

    def change_language(self, lang):
        try:
            logger.info(f"🌐 Changing language to: {lang}")
            
            # Update config first
            self.config["language"] = lang
            
            # Set language in language manager FIRST
            self.language_manager.current_lang = lang
            
            # Fix button states - only one should be checked
            if lang == "es":
                self.es_button.setChecked(True)
                self.en_button.setChecked(False)
            else:
                self.es_button.setChecked(False)
                self.en_button.setChecked(True)
            
            # Window title is always in English
            self.setWindowTitle("EVA - Enhancement Assistant Voice - Settings")
            
            # IMMEDIATELY update ALL settings window UI texts
            logger.info("🌐 Updating settings window language...")
            
            # Update language buttons first
            self.es_button.setText(self.get_text("ui.spanish", default="Español"))
            self.en_button.setText(self.get_text("ui.english", default="English"))
            
            # Update ALL group box titles
            if hasattr(self, 'license_group'):
                self.license_group.setTitle(self.get_text("ui.license_section", default="License Configuration"))
            if hasattr(self, 'general_group'):
                self.general_group.setTitle(self.get_text("ui.general", default="General"))
            if hasattr(self, 'voice_group'):
                self.voice_group.setTitle("🎵 " + self.get_text("ui.voice", default="Voice"))
            # Hardware group title update removed - obsolete after Piper TTS migration
            if hasattr(self, 'update_group'):
                self.update_group.setTitle(self.get_text("ui.updates_section", default="Updates Configuration"))
            if hasattr(self, 'knowledge_group'):
                self.knowledge_group.setTitle(self.get_text("ui.knowledge_base_section", default="Personal Knowledge Base"))
            if hasattr(self, 'commands_group'):
                self.commands_group.setTitle(self.get_text("ui.custom_commands", default="Custom Commands"))
            if hasattr(self, 'plugins_group'):
                self.plugins_group.setTitle(self.get_text("ui.plugins_section", default="Plugins"))
            if hasattr(self, 'openrouter_group'):
                self.openrouter_group.setTitle(self.get_text("ui.openrouter_section", default="OpenRouter AI"))
            
            # Update ALL labels immediately
            self.update_all_labels_immediately()
            
            # Update voice combo items
            self.update_voice_combo_items()
            
            # Update button texts
            self.update_button_texts()
            
            # Update ALL dynamic content
            self.update_all_dynamic_content()
            
            # Force complete UI refresh
            self.repaint()
            self.update()
            
            # Process events to ensure all updates are applied
            from PySide6.QtWidgets import QApplication
            QApplication.processEvents()
            
            # Save the language change immediately via ConfigManager
            try:
                config_manager.save()
                logger.info("Language configuration saved via ConfigManager")
            except Exception as e:
                logger.error(f"Error saving language configuration: {str(e)}")
            
            # Notify chat window of language change
            if hasattr(self, 'chat_window') and self.chat_window:
                self.chat_window.language_manager.set_language(lang)
                self.chat_window.update_ui_texts()
                logger.info(f"Chat window language updated to: {lang}")
            
            logger.info(f"🌐 Settings window language successfully changed to: {lang}")
            self.settings_updated.emit(self.config)
            
        except Exception as e:
            logger.error(f"Error changing language: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def update_all_labels_immediately(self):
        """Update ALL labels in the settings window immediately"""
        try:
            # License section
            if hasattr(self, 'license_label'):
                self.license_label.setText(self.get_text("ui.license_key", default="License Key") + ":")
            if hasattr(self, 'validate_btn'):
                self.validate_btn.setText(self.get_text("ui.validate", default="Validate"))
            if hasattr(self, 'buy_btn'):
                self.buy_btn.setText(self.get_text("ui.buy_license", default="Buy License"))
            if hasattr(self, 'remove_license_btn'):
                self.remove_license_btn.setText(self.get_text("ui.remove_license", default="Remove License"))
            
            # General section
            if hasattr(self, 'name_label'):
                self.name_label.setText(self.get_text("ui.your_name", default="Your name") + ":")
            if hasattr(self, 'auto_start_label'):
                self.auto_start_label.setText(self.get_text("ui.auto_start", default="Auto start") + ":")
            if hasattr(self, 'minimize_label'):
                self.minimize_label.setText(self.get_text("ui.minimize_start", default="Minimize on start") + ":")
            if hasattr(self, 'sensitivity_label'):
                self.sensitivity_label.setText(self.get_text("ui.sensitivity", default="Voice sensitivity") + ":")
            if hasattr(self, 'auto_listen_label'):
                self.auto_listen_label.setText(self.get_text("ui.auto_listen", default="Auto Listen") + ":")
            
            # Voice section
            if hasattr(self, 'voice_label'):
                self.voice_label.setText(self.get_text("ui.voice_selection", default="Voice Selection") + ":")
            if hasattr(self, 'volume_label'):
                self.volume_label.setText(self.get_text("ui.volume", default="Volume") + ":")
            if hasattr(self, 'speed_label'):
                self.speed_label.setText(self.get_text("ui.speech_speed", default="Speech Speed") + ":")
            
            # VAD section
            for widget in self.findChildren(QLabel):
                text = widget.text()
                if "🎙️ Voice Activity Detection" in text or "🎙️ Detección de Actividad de Voz" in text:
                    widget.setText("🎙️ " + self.get_text("ui.vad_title", default="Voice Activity Detection"))
                elif "VAD filters background noise" in text or "VAD filtra el ruido de fondo" in text:
                    widget.setText(self.get_text("ui.vad_description", default="VAD filters background noise and only processes speech, reducing CPU usage by 60-80%."))
                elif "Detection Mode:" in text or "Modo de Detección:" in text:
                    widget.setText(self.get_text("ui.vad_mode", default="Detection Mode") + ":")
            
            # Hardware section
            # GPU label update removed - obsolete after Piper TTS migration
            if hasattr(self, 'advanced_gpu_btn'):
                self.advanced_gpu_btn.setText(self.get_text("ui.gpu_config", default="GPU Configuration"))
            
            # Updates section
            if hasattr(self, 'auto_check_label'):
                self.auto_check_label.setText(self.get_text("ui.auto_check_updates", default="Check Updates Automatically") + ":")
            if hasattr(self, 'interval_label'):
                self.interval_label.setText(self.get_text("ui.check_interval", default="Check Interval (hours)") + ":")
            if hasattr(self, 'critical_only_label'):
                self.critical_only_label.setText(self.get_text("ui.critical_only", default="Notify Critical Updates Only") + ":")
            if hasattr(self, 'backup_label'):
                self.backup_label.setText(self.get_text("ui.auto_backup", default="Create Automatic Backups") + ":")
            
            # Commands section
            if hasattr(self, 'custom_cmd_btn'):
                self.custom_cmd_btn.setText(self.get_text("ui.manage_commands", default="Manage Commands"))
            if hasattr(self, 'custom_cmd_desc'):
                self.custom_cmd_desc.setText(self.get_text("ui.commands_description", default="Here you can customize voice commands and shortcuts"))
            
            # Update ALL buttons in the window
            for button in self.findChildren(QPushButton):
                text = button.text()
                if "Check Updates Now" in text or "Verificar Actualizaciones Ahora" in text:
                    button.setText(self.get_text("ui.check_updates_now", default="Check Updates Now"))
                elif "Test Voice" in text or "Probar Voz" in text:
                    button.setText("🔊 " + self.get_text("ui.test_voice", default="Test Voice"))
                elif "Test VAD Configuration" in text or "Probar Configuración VAD" in text:
                    button.setText("🧪 " + self.get_text("ui.vad_test", default="Test VAD Configuration"))
                elif "Advanced Knowledge" in text or "Editor Avanzado" in text:
                    button.setText(self.get_text("ui.advanced_knowledge_editor", default="📝 Advanced Knowledge Base Editor"))
                elif text in ["Add", "Añadir"]:
                    button.setText(self.get_text("ui.add", default="Add"))
                elif text in ["Edit", "Editar"]:
                    button.setText(self.get_text("ui.edit", default="Edit"))
                elif text in ["Remove", "Eliminar"]:
                    button.setText(self.get_text("ui.remove", default="Remove"))
            
            # Update ALL checkboxes
            for checkbox in self.findChildren(QCheckBox):
                text = checkbox.text()
                if "Contextual greetings" in text or "Saludos contextuales" in text:
                    checkbox.setText(self.get_text("ui.contextual_greetings", default="Contextual greetings (Good morning, good afternoon, etc.)"))
                elif "Automatic suggestions" in text or "Sugerencias automáticas" in text:
                    checkbox.setText(self.get_text("ui.auto_suggestions", default="Automatic suggestions based on frequent commands"))
            
            # Update ALL description labels
            for label in self.findChildren(QLabel):
                text = label.text()
                if "When enabled, EVA continuously listens" in text or "Cuando está habilitado, EVA escucha continuamente" in text:
                    label.setText(self.get_text("ui.auto_listen_description", default="When enabled, EVA continuously listens for voice commands. Disable to use only text chat."))
                elif "EVA now uses Piper TTS with premium" in text or "EVA ahora usa Piper TTS con voces" in text:
                    label.setText(self.get_text("ui.piper_voice_description", default="EVA now uses Piper TTS with premium female voices for both Spanish and English. These voices provide excellent quality with instant synthesis and no memory issues."))
                elif "Castellano: Mexican voice adapted" in text or "Castellano: Voz mexicana adaptada" in text:
                    label.setText("• " + self.get_text("ui.castellano_voice_details", default="Castellano: Mexican voice adapted with Spanish vocabulary and pronunciation"))
                elif "Neutro: Natural Mexican voice" in text or "Neutro: Voz mexicana natural" in text:
                    label.setText("• " + self.get_text("ui.neutro_voice_details", default="Neutro: Natural Mexican voice with neutral Latin American accent"))
                elif "English: Clear American female voice" in text or "Inglés: Voz femenina americana clara" in text:
                    label.setText("• " + self.get_text("ui.english_voice_details", default="English: Clear American female voice, perfect for professional communication"))
                elif "🎤 Voice Details" in text or "🎤 Detalles de Voz" in text:
                    label.setText("🎤 " + self.get_text("ui.voice_details", default="Voice Details"))
                elif text in ["Low", "Baja"]:
                    label.setText(self.get_text("ui.low", default="Low"))
                elif text in ["High", "Alta"]:
                    label.setText(self.get_text("ui.high", default="High"))
                elif text in ["Slow", "Lenta"]:
                    label.setText(self.get_text("ui.slow", default="Slow"))
                elif text in ["Fast", "Rápida"]:
                    label.setText(self.get_text("ui.fast", default="Fast"))
                elif text in ["to", "a"]:
                    label.setText(self.get_text("ui.to", default="to"))
            
            logger.info("🌐 All labels updated immediately")
            
        except Exception as e:
            logger.error(f"Error updating labels immediately: {str(e)}")
            import traceback
            traceback.print_exc()

    def update_language(self):
        # FIXED: Window title is ALWAYS "EVA - Enhancement Assistant Voice" regardless of language
        self.setWindowTitle("EVA - Enhancement Assistant Voice - Settings")

        # Update language buttons
        self.es_button.setText(self.get_text("ui.spanish", default="Español"))
        self.en_button.setText(self.get_text("ui.english", default="English"))

        # License section - COMPLETE UPDATE
        if getattr(self, 'license_group', None):
            self.license_group.setTitle(self.get_text("ui.license_section", default="License Configuration"))
            self.license_label.setText(self.get_text("ui.license_key", default="License Key") + ":")
            self.validate_btn.setText(self.get_text("ui.validate", default="Validate"))
            self.buy_btn.setText(self.get_text("ui.buy_license", default="Buy License"))
            self.remove_license_btn.setText(self.get_text("ui.remove_license", default="Remove License"))
            
            # Update license status
            stored_license = self.license_validator.load_stored_license()
            if stored_license:
                valid_text = self.get_text("ui.license_valid", default="Valid License")
                self.license_status.setText(f"{valid_text} ({stored_license['type']})")
            else:
                invalid_text = self.get_text("ui.license_invalid", default="Invalid License")
                self.license_status.setText(invalid_text)

        # General section - COMPLETE UPDATE
        if hasattr(self, 'general_group'):
            self.general_group.setTitle(self.get_text("ui.general", default="General"))
            self.auto_start_label.setText(self.get_text("ui.auto_start", default="Auto start") + ":")
            self.minimize_label.setText(self.get_text("ui.minimize_start", default="Minimize on start") + ":")
            self.sensitivity_label.setText(self.get_text("ui.sensitivity", default="Voice sensitivity") + ":")
            self.name_label.setText(self.get_text("ui.your_name", default="Your name") + ":")
            self.auto_listen_label.setText(self.get_text("ui.auto_listen", default="Auto Listen") + ":")
            
            # Update auto listen description
            if hasattr(self, 'auto_listen_desc'):
                self.auto_listen_desc.setText(self.get_text("ui.auto_listen_description", default="When enabled, EVA continuously listens for voice commands. Disable to use only text chat."))

        # Voice section - COMPLETE UPDATE
        if hasattr(self, 'voice_group'):
            self.voice_group.setTitle("🎵 " + self.get_text("ui.voice", default="Voice"))
            self.voice_label.setText(self.get_text("ui.voice_selection", default="Voice Selection") + ":")
            self.volume_label.setText(self.get_text("ui.volume", default="Volume") + ":")
            self.speed_label.setText(self.get_text("ui.speech_speed", default="Speech Speed") + ":")
            
            # Update voice info description
            if hasattr(self, 'voice_info'):
                self.voice_info.setText(self.get_text("ui.piper_voice_description", 
                    "EVA now uses Piper TTS with premium female voices for both Spanish and English. "
                    "These voices provide excellent quality with instant synthesis and no memory issues."))
            
            # Update voice details
            if hasattr(self, 'voice_details_title'):
                self.voice_details_title.setText("🎤 " + self.get_text("ui.voice_details", default="Voice Details"))
            
            if hasattr(self, 'spanish_details'):
                self.spanish_details.setText("• " + self.get_text("ui.spanish_voice_details", default="Spanish: Professional female voice with natural Castilian pronunciation"))
            
            if hasattr(self, 'english_details'):
                self.english_details.setText("• " + self.get_text("ui.english_voice_details", default="English: Clear American female voice, perfect for professional communication"))

            # Update VAD section
            for widget in self.voice_group.findChildren(QLabel):
                text = widget.text()
                if "🎙️ Voice Activity Detection" in text or "🎙️ Detección de Actividad de Voz" in text:
                    widget.setText("🎙️ " + self.get_text("ui.vad_title", default="Voice Activity Detection"))
                elif "VAD filters background noise" in text or "VAD filtra el ruido de fondo" in text:
                    widget.setText(self.get_text("ui.vad_description", default="VAD filters background noise and only processes speech, reducing CPU usage by 60-80%."))
                elif "Detection Mode:" in text or "Modo de Detección:" in text:
                    widget.setText(self.get_text("ui.vad_mode", default="Detection Mode") + ":")

        # Hardware section - COMPLETE UPDATE
        # Hardware group title update removed - obsolete after Piper TTS migration
            # GPU elements update removed - obsolete after Piper TTS migration

        # Updates section - COMPLETE UPDATE
        if hasattr(self, 'update_group'):
            self.update_group.setTitle(self.get_text("ui.updates_section", default="Updates Configuration"))
            self.auto_check_label.setText(self.get_text("ui.auto_check_updates", default="Check Updates Automatically") + ":")
            self.interval_label.setText(self.get_text("ui.check_interval", default="Check Interval (hours)") + ":")
            self.critical_only_label.setText(self.get_text("ui.critical_only", default="Notify Critical Updates Only") + ":")
            self.backup_label.setText(self.get_text("ui.auto_backup", default="Create Automatic Backups") + ":")
            
            # Update ALL description labels in updates section
            for widget in self.update_group.findChildren(QLabel):
                text = widget.text()
                if "Cuando está habilitado, EVA verificará automáticamente" in text or "When enabled, EVA will automatically check" in text:
                    widget.setText(self.get_text("ui.updates_auto_check_description", default="When enabled, EVA will automatically check if new versions are available."))
                elif "Solo mostrar notificaciones para actualizaciones" in text or "Only show notifications for security updates" in text:
                    widget.setText(self.get_text("ui.updates_critical_only_description", default="Only show notifications for security updates or critical fixes."))
                elif "Crear automáticamente una copia de seguridad" in text or "Automatically create a backup before each update" in text:
                    widget.setText(self.get_text("ui.updates_backup_description", default="Automatically create a backup before each update."))
                elif "Última verificación:" in text or "Last check:" in text:
                    # Update last check label
                    self.update_last_check_display()
            
            # Update manual check button
            for widget in self.update_group.findChildren(QPushButton):
                if "Check Updates Now" in widget.text() or "Verificar Actualizaciones Ahora" in widget.text():
                    widget.setText(self.get_text("ui.check_updates_now", default="Check Updates Now"))

        # Knowledge Base section - COMPLETE UPDATE
        if hasattr(self, 'knowledge_group'):
            self.knowledge_group.setTitle(self.get_text("ui.knowledge_base_section", default="Personal Knowledge Base"))
            
            # Update knowledge base description
            for widget in self.knowledge_group.findChildren(QLabel):
                if "Customize how EVA knows you" in widget.text() or "Personaliza cómo EVA te conoce" in widget.text():
                    widget.setText(self.get_text("ui.knowledge_base_description", default="Customize how EVA knows you and behaves with you. These settings are saved in eva_knowledge_base.json"))
            
            # Update user profile section
            for widget in self.knowledge_group.findChildren(QLabel):
                if "👤 User Profile" in widget.text() or "👤 Perfil de Usuario" in widget.text():
                    widget.setText(self.get_text("ui.user_profile", default="👤 User Profile"))
                elif "Timezone:" in widget.text() or "Zona Horaria:" in widget.text():
                    widget.setText(self.get_text("ui.timezone", default="Timezone:"))
                elif "Work Hours:" in widget.text() or "Horario de Trabajo:" in widget.text():
                    widget.setText(self.get_text("ui.work_hours", default="Work Hours:"))
                elif "⚡ Custom Shortcuts" in widget.text() or "⚡ Atajos Personalizados" in widget.text():
                    widget.setText(self.get_text("ui.custom_shortcuts", default="⚡ Custom Shortcuts"))
                elif "🎯 Behavior" in widget.text() or "🎯 Comportamiento" in widget.text():
                    widget.setText(self.get_text("ui.behavior", default="🎯 Behavior"))
            
            # Update checkboxes in knowledge base
            for widget in self.knowledge_group.findChildren(QCheckBox):
                if "Contextual greetings" in widget.text() or "Saludos contextuales" in widget.text():
                    widget.setText(self.get_text("ui.contextual_greetings", default="Contextual greetings (Good morning, good afternoon, etc.)"))
                elif "Automatic suggestions" in widget.text() or "Sugerencias automáticas" in widget.text():
                    widget.setText(self.get_text("ui.auto_suggestions", default="Automatic suggestions based on frequent commands"))

        # Commands section - COMPLETE UPDATE
        if hasattr(self, 'commands_group'):
            self.commands_group.setTitle(self.get_text("ui.custom_commands", default="Custom Commands"))
            self.custom_cmd_btn.setText(self.get_text("ui.manage_commands", default="Manage Commands"))
            self.custom_cmd_desc.setText(self.get_text("ui.commands_description", default="Here you can customize voice commands and shortcuts"))

        # Update ALL slider labels and dynamic content
        self.update_all_slider_labels()
        
        # Update voice combo items
        self.update_voice_combo_items()
        
        # Update VAD combo items
        if hasattr(self, 'vad_mode_combo'):
            self.update_vad_combo_items()
        
        # Update action buttons
        self.update_button_texts()
        
        # Update ALL dynamic content
        self.update_all_dynamic_content()

        # Force complete repaint
        self.repaint()
        self.update()
        
        logger.info(f"Complete language update applied: {self.language_manager.current_lang}")

    def update_all_slider_labels(self):
        """Update ALL slider labels with proper translations"""
        try:
            # Find and update all QLabel widgets that are slider labels
            for widget in self.findChildren(QLabel):
                text = widget.text()
                
                # Update slider range labels
                if text in ["Low", "Baja"]:
                    widget.setText(self.get_text("ui.low", default="Low"))
                elif text in ["High", "Alta"]:
                    widget.setText(self.get_text("ui.high", default="High"))
                elif text in ["Slow", "Lenta"]:
                    widget.setText(self.get_text("ui.slow", default="Slow"))
                elif text in ["Fast", "Rápida"]:
                    widget.setText(self.get_text("ui.fast", default="Fast"))
                elif text in ["to", "a"]:
                    widget.setText(self.get_text("ui.to", default="to"))
                elif text in ["1h"]:
                    widget.setText("1h")  # Universal
                elif text in ["24h"]:
                    widget.setText("24h")  # Universal
                    
            # Update GPU combo items
            # GPU combo update removed - obsolete after Piper TTS migration
                    
            # Update placeholder texts
            if hasattr(self, 'name_input'):
                self.name_input.setPlaceholderText(self.get_text("ui.enter_name", default="Enter your name"))
            
            if hasattr(self, 'license_input'):
                self.license_input.setPlaceholderText(self.get_text("ui.license_placeholder", default="EVA-XXXX-XXXX-XXXX"))
            
            # Update ALL buttons with hardcoded text
            for widget in self.findChildren(QPushButton):
                text = widget.text()
                
                # Update common button texts
                if text in ["Add", "Añadir"]:
                    widget.setText(self.get_text("ui.add", default="Add"))
                elif text in ["Edit", "Editar"]:
                    widget.setText(self.get_text("ui.edit", default="Edit"))
                elif text in ["Remove", "Eliminar"]:
                    widget.setText(self.get_text("ui.remove", default="Remove"))
                elif text in ["Save", "Guardar"]:
                    widget.setText(self.get_text("ui.save", default="Save"))
                elif text in ["Cancel", "Cancelar"]:
                    widget.setText(self.get_text("ui.cancel", default="Cancel"))
                elif text in ["Validate", "Validar"]:
                    widget.setText(self.get_text("ui.validate", default="Validate"))
                elif text in ["Buy License", "Comprar Licencia"]:
                    widget.setText(self.get_text("ui.buy_license", default="Buy License"))
                elif text in ["Remove License", "Eliminar Licencia"]:
                    widget.setText(self.get_text("ui.remove_license", default="Remove License"))
                elif text in ["Manage Commands", "Administrar Comandos"]:
                    widget.setText(self.get_text("ui.manage_commands", default="Manage Commands"))
                elif text in ["GPU Configuration", "Configuración GPU"]:
                    widget.setText(self.get_text("ui.gpu_config", default="GPU Configuration"))
                elif text in ["Check Updates Now", "Verificar Actualizaciones Ahora"]:
                    widget.setText(self.get_text("ui.check_updates_now", default="Check Updates Now"))
                elif "Test Voice" in text or "Probar Voz" in text:
                    widget.setText("🔊 " + self.get_text("ui.test_voice", default="Test Voice"))
                elif "Advanced Knowledge" in text or "Editor Avanzado" in text:
                    widget.setText(self.get_text("ui.advanced_knowledge_editor", default="📝 Advanced Knowledge Base Editor"))
            
            # Update ALL description labels that might have mixed languages
            for widget in self.findChildren(QLabel):
                text = widget.text()
                
                # Updates section descriptions
                if "Cuando está habilitado, EVA verificará automáticamente" in text or "When enabled, EVA will automatically check" in text:
                    widget.setText(self.get_text("ui.updates_auto_check_description", default="When enabled, EVA will automatically check if new versions are available."))
                elif "Solo mostrar notificaciones para actualizaciones" in text or "Only show notifications for security updates" in text:
                    widget.setText(self.get_text("ui.updates_critical_only_description", default="Only show notifications for security updates or critical fixes."))
                elif "Crear automáticamente una copia de seguridad" in text or "Automatically create a backup before each update" in text:
                    widget.setText(self.get_text("ui.updates_backup_description", default="Automatically create a backup before each update."))
                
                # Knowledge base descriptions
                elif "Customize how EVA knows you" in text or "Personaliza cómo EVA te conoce" in text:
                    widget.setText(self.get_text("ui.knowledge_base_description", default="Customize how EVA knows you and behaves with you. These settings are saved in eva_knowledge_base.json"))
                
                # Voice descriptions
                elif "EVA now uses" in text and "Piper TTS" in text:
                    widget.setText(self.get_text("ui.piper_voice_description", default="EVA uses Piper TTS with high-quality female voices for Spanish and English. Both voices provide excellent quality with instant synthesis."))
                elif "When enabled, EVA continuously listens" in text or "Cuando está habilitado, EVA escucha continuamente" in text:
                    widget.setText(self.get_text("ui.auto_listen_description", default="When enabled, EVA continuously listens for voice commands. Disable to use only text chat."))
                elif "Español:" in text and ("Voz femenina" in text or "voice" in text):
                    widget.setText("• " + self.get_text("ui.spanish_voice_details", default="Español: Voz femenina natural con pronunciación mexicana clara"))
                elif "English: Clear American female voice" in text or "Inglés: Voz femenina americana clara" in text:
                    widget.setText("• " + self.get_text("ui.english_voice_details", default="English: Clear American female voice, perfect for professional communication"))
                    
        except Exception as e:
            logger.error(f"Error updating slider labels: {str(e)}")

    def setup_license_settings(self):
        """Sección de licencia eliminada — EVA es completamente libre."""
        pass

    def setup_custom_commands_settings(self):
        """Nueva sección para comandos personalizados"""
        self.commands_group = QGroupBox(self.get_text("ui.custom_commands", default="Custom Commands"))
        layout = QVBoxLayout(self.commands_group)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 15, 8, 8)

        # Botón para abrir la ventana de personalización
        self.custom_cmd_btn = QPushButton(self.get_text("ui.manage_commands", default="Manage Commands"))
        self.custom_cmd_btn.setStyleSheet("background-color: rgba(156, 39, 176, 0.3);")
        self.custom_cmd_btn.clicked.connect(self.open_custom_commands)
        layout.addWidget(self.custom_cmd_btn)

        # Descripción
        self.custom_cmd_desc = QLabel(self.get_text("ui.commands_description", default="Here you can customize voice commands and shortcuts"))
        self.custom_cmd_desc.setWordWrap(True)
        self.custom_cmd_desc.setStyleSheet("font-size: 12px; color: #aaaaaa;")
        layout.addWidget(self.custom_cmd_desc)

        self.scrollable_content_layout.addWidget(self.commands_group)

    def setup_general_settings(self):
        self.general_group = QGroupBox(self.language_manager.get_text("ui.general"))
        layout = QVBoxLayout(self.general_group)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 15, 8, 8)

        # Nombre de usuario
        name_layout = QHBoxLayout()
        self.name_label = QLabel(self.language_manager.get_text("ui.your_name") + ":")
        name_layout.addWidget(self.name_label)
        self.name_input = QLineEdit()
        placeholder_text = self.get_text("ui.enter_name", default="Enter your name")
        self.name_input.setPlaceholderText(placeholder_text)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Auto startup
        auto_start_layout = QHBoxLayout()
        self.auto_start_label = QLabel(self.language_manager.get_text("ui.auto_start") + ":")
        auto_start_layout.addWidget(self.auto_start_label)
        self.auto_start_check = QCheckBox()
        self.auto_start_check.setChecked(self.config.get("auto_start", False))
        auto_start_layout.addStretch()
        auto_start_layout.addWidget(self.auto_start_check)
        layout.addLayout(auto_start_layout)

        # Minimize on startup
        minimize_layout = QHBoxLayout()
        self.minimize_label = QLabel(self.language_manager.get_text("ui.minimize_start") + ":")
        minimize_layout.addWidget(self.minimize_label)
        self.minimize_check = QCheckBox()
        self.minimize_check.setChecked(self.config.get("minimize_start", True))
        minimize_layout.addStretch()
        minimize_layout.addWidget(self.minimize_check)
        layout.addLayout(minimize_layout)

        # Microphone sensitivity
        sensitivity_layout = QVBoxLayout()
        self.sensitivity_label = QLabel(self.language_manager.get_text("ui.sensitivity") + ":")
        sensitivity_layout.addWidget(self.sensitivity_label)

        slider_layout = QHBoxLayout()
        low_text = self.get_text("ui.low", default="Baja")
        high_text = self.get_text("ui.high", default="Alta")
        slider_layout.addWidget(QLabel(low_text))
        self.sensitivity_slider = QSlider(Qt.Horizontal)
        self.sensitivity_slider.setRange(0, 100)
        slider_layout.addWidget(self.sensitivity_slider)
        slider_layout.addWidget(QLabel(high_text))
        
        sensitivity_layout.addLayout(slider_layout)
        layout.addLayout(sensitivity_layout)

        # Auto listen con explicación clara
        auto_listen_layout = QVBoxLayout()
        auto_listen_header = QHBoxLayout()
        self.auto_listen_label = QLabel(self.get_text("ui.auto_listen", default="Auto Listen") + ":")
        auto_listen_header.addWidget(self.auto_listen_label)
        self.auto_listen_check = QCheckBox()
        self.auto_listen_check.setChecked(self.config.get("auto_listen", True))
        auto_listen_header.addStretch()
        auto_listen_header.addWidget(self.auto_listen_check)
        auto_listen_layout.addLayout(auto_listen_header)
        
        self.auto_listen_desc = QLabel(self.get_text("ui.auto_listen_description", default="When enabled, EVA continuously listens for voice commands. Disable to use only text chat."))
        self.auto_listen_desc.setWordWrap(True)
        self.auto_listen_desc.setStyleSheet("font-size: 10px; color: #888888; margin-left: 20px;")
        auto_listen_layout.addWidget(self.auto_listen_desc)
        layout.addLayout(auto_listen_layout)

        self.scrollable_content_layout.addWidget(self.general_group)

    def setup_voice_settings(self):
        self.voice_group = QGroupBox("🎵 " + self.language_manager.get_text("ui.voice"))
        layout = QVBoxLayout(self.voice_group)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 15, 8, 8)

        # Explicación del sistema Piper TTS simplificado
        voice_info_text = self.get_text("ui.piper_voice_description", 
            "EVA uses Piper TTS with high-quality female voices for Spanish and English. "
            "Both voices provide excellent quality with instant synthesis.")
        self.voice_info = QLabel(voice_info_text)
        self.voice_info.setWordWrap(True)
        self.voice_info.setStyleSheet("font-size: 11px; color: #aaaaaa; margin-bottom: 8px;")
        layout.addWidget(self.voice_info)

        # Selección de voz principal
        voice_layout = QHBoxLayout()
        self.voice_label = QLabel(self.get_text("ui.voice_selection", default="Voice Selection") + ":")
        voice_layout.addWidget(self.voice_label)
        self.voice_combo = QComboBox()
        
        # Solo 2 voces: Español e Inglés
        self.update_voice_combo_items()
        
        voice_layout.addWidget(self.voice_combo, 1)
        layout.addLayout(voice_layout)

        # Información de las voces
        voice_details_frame = QFrame()
        voice_details_frame.setStyleSheet("background-color: rgba(40, 40, 50, 0.5); border-radius: 6px; padding: 8px;")
        voice_details_layout = QVBoxLayout(voice_details_frame)
        
        self.voice_details_title = QLabel("🎤 " + self.get_text("ui.voice_details", default="Voice Details"))
        self.voice_details_title.setStyleSheet("font-weight: bold; color: #bb86fc;")
        voice_details_layout.addWidget(self.voice_details_title)
        
        self.spanish_details = QLabel("• " + self.get_text("ui.spanish_voice_details", default="Español: Voz femenina natural con pronunciación mexicana clara"))
        self.spanish_details.setStyleSheet("font-size: 11px; color: #ffffff; margin-left: 10px;")
        voice_details_layout.addWidget(self.spanish_details)
        
        self.english_details = QLabel("• " + self.get_text("ui.english_voice_details", default="English: Clear American female voice, perfect for professional communication"))
        self.english_details.setStyleSheet("font-size: 11px; color: #ffffff; margin-left: 10px;")
        voice_details_layout.addWidget(self.english_details)
        
        layout.addWidget(voice_details_frame)

        # Configuración de velocidad
        speed_layout = QVBoxLayout()
        self.speed_label = QLabel(self.get_text("ui.speech_speed", default="Speech Speed") + ":")
        speed_layout.addWidget(self.speed_label)

        speed_slider_layout = QHBoxLayout()
        slow_text = self.get_text("ui.slow", default="Slow")
        fast_text = self.get_text("ui.fast", default="Fast")
        speed_slider_layout.addWidget(QLabel(slow_text))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(50, 150)  # 0.5x to 1.5x speed
        self.speed_slider.setValue(100)  # Default 1.0x
        speed_slider_layout.addWidget(self.speed_slider)
        speed_slider_layout.addWidget(QLabel(fast_text))
        
        # Speed value label
        self.speed_value_label = QLabel("1.0x")  # Speed values are universal numbers
        self.speed_value_label.setStyleSheet("font-weight: bold; color: #00bcd4;")
        speed_slider_layout.addWidget(self.speed_value_label)
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        
        speed_layout.addLayout(speed_slider_layout)
        layout.addLayout(speed_layout)

        # Volume
        volume_layout = QVBoxLayout()
        self.volume_label = QLabel(self.language_manager.get_text("ui.volume") + ":")
        volume_layout.addWidget(self.volume_label)

        vol_slider_layout = QHBoxLayout()
        low_text = self.get_text("ui.low", default="Low")
        high_text = self.get_text("ui.high", default="High")
        vol_slider_layout.addWidget(QLabel(low_text))
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        vol_slider_layout.addWidget(self.volume_slider)
        vol_slider_layout.addWidget(QLabel(high_text))
        
        # Volume value label
        self.volume_value_label = QLabel("80%")  # Volume percentages are universal numbers
        self.volume_value_label.setStyleSheet("font-weight: bold; color: #00bcd4;")
        vol_slider_layout.addWidget(self.volume_value_label)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        
        volume_layout.addLayout(vol_slider_layout)
        layout.addLayout(volume_layout)

        # VAD (Voice Activity Detection) Configuration
        vad_frame = QFrame()
        vad_frame.setStyleSheet("background-color: rgba(40, 40, 50, 0.5); border-radius: 6px; padding: 8px; margin-top: 8px;")
        vad_layout = QVBoxLayout(vad_frame)
        
        vad_title = QLabel("🎙️ " + self.get_text("ui.vad_title", default="Voice Activity Detection"))
        vad_title.setStyleSheet("font-weight: bold; color: #bb86fc; margin-bottom: 4px;")
        vad_layout.addWidget(vad_title)
        
        vad_description = QLabel(self.get_text("ui.vad_description", default="VAD filters background noise and only processes speech, reducing CPU usage by 60-80%."))
        vad_description.setWordWrap(True)
        vad_description.setStyleSheet("font-size: 10px; color: #aaaaaa; margin-bottom: 8px;")
        vad_layout.addWidget(vad_description)
        
        # VAD Mode Selection
        vad_mode_layout = QHBoxLayout()
        vad_mode_label = QLabel(self.get_text("ui.vad_mode", default="Detection Mode") + ":")
        vad_mode_layout.addWidget(vad_mode_label)
        
        self.vad_mode_combo = QComboBox()
        self.update_vad_combo_items()
        vad_mode_layout.addWidget(self.vad_mode_combo, 1)
        vad_layout.addLayout(vad_mode_layout)
        
        # VAD Test Button
        vad_test_layout = QHBoxLayout()
        vad_test_btn = QPushButton("🧪 " + self.get_text("ui.vad_test", default="Test VAD Configuration"))
        vad_test_btn.setStyleSheet("background-color: rgba(156, 39, 176, 0.3); min-height: 30px; font-size: 11px;")
        vad_test_btn.clicked.connect(self.test_vad_configuration)
        vad_test_layout.addWidget(vad_test_btn)
        vad_test_layout.addStretch()
        vad_layout.addLayout(vad_test_layout)
        
        layout.addWidget(vad_frame)

        # Botón de prueba de voz
        test_voice_btn = QPushButton("🔊 " + self.get_text("ui.test_voice", default="Test Voice"))
        test_voice_btn.setStyleSheet("background-color: rgba(33, 150, 243, 0.3); min-height: 35px;")
        test_voice_btn.clicked.connect(self.test_selected_voice)
        layout.addWidget(test_voice_btn)

        # Botón de diagnóstico de micrófono (NUEVO)
        mic_diag_layout = QHBoxLayout()
        self.test_mic_btn = QPushButton("🎤 " + self.get_text("ui.test_microphone", default="Test Microphone"))
        self.test_mic_btn.setStyleSheet("background-color: rgba(76, 175, 80, 0.3); min-height: 35px;")
        self.test_mic_btn.clicked.connect(self.test_microphone_button)
        mic_diag_layout.addWidget(self.test_mic_btn)

        diag_mic_btn = QPushButton("🔍 " + self.get_text("ui.diagnose_audio", default="Diagnose Audio System"))
        diag_mic_btn.setStyleSheet("background-color: rgba(255, 152, 0, 0.3); min-height: 35px;")
        diag_mic_btn.clicked.connect(self.diagnose_audio_button)
        mic_diag_layout.addWidget(diag_mic_btn)

        layout.addLayout(mic_diag_layout)

        # Resultado del test de micrófono
        self.mic_test_result_label = QLabel("")
        self.mic_test_result_label.setWordWrap(True)
        self.mic_test_result_label.setStyleSheet("font-size: 11px; color: #888888; margin-top: 5px;")
        layout.addWidget(self.mic_test_result_label)

        self.scrollable_content_layout.addWidget(self.voice_group)

    # TTS Management section removed - Piper TTS doesn't need complex management

    def on_speed_changed(self, value):
        """Handle speech speed change"""
        speed_value = value / 100.0
        self.speed_value_label.setText(f"{speed_value:.1f}x")
        
        # Update config immediately
        if "tts" not in self.config:
            self.config["tts"] = {}
        self.config["tts"]["speed"] = speed_value
        
        # Apply changes in real-time if possible
        try:
            if self.chat_window.speech_synthesizer is not None:
                self.chat_window.speech_synthesizer.update_config(self.config)
        except Exception as e:
            logger.debug(f"Could not apply speed change in real-time: {str(e)}")

    def on_volume_changed(self, value):
        """Handle volume change"""
        self.volume_value_label.setText(f"{value}%")
        
        # Update config immediately
        if "tts" not in self.config:
            self.config["tts"] = {}
        self.config["tts"]["volume"] = value / 100.0
        
        # Apply changes in real-time if possible
        try:
            if self.chat_window.speech_synthesizer is not None:
                self.chat_window.speech_synthesizer.update_config(self.config)
        except Exception as e:
            logger.debug(f"Could not apply volume change in real-time: {str(e)}")

    def test_selected_voice(self):
        """Test the currently selected voice"""
        try:
            selected_language = self.voice_combo.currentData()
            
            # Test messages for each language
            test_messages = {
                "es": self.get_text("ui.voice_test_message_es", default="Hola, soy EVA. Esta es mi voz en español con pronunciación natural y clara articulación."),
                "en": self.get_text("ui.voice_test_message_en", default="Hello, I am EVA. This is my English voice with natural pronunciation and clear articulation.")
            }
            
            test_message = test_messages.get(selected_language, test_messages["es"])
            
            # Try to use the speech synthesizer if available
            if self.chat_window.speech_synthesizer is not None:
                # Temporarily update config for testing
                temp_config = self.config.copy()
                if "tts" not in temp_config:
                    temp_config["tts"] = {}
                temp_config["tts"]["speed"] = self.speed_slider.value() / 100.0
                temp_config["tts"]["volume"] = self.volume_slider.value() / 100.0
                
                self.chat_window.speech_synthesizer.update_config(temp_config)
                self.chat_window.speech_synthesizer.speak(test_message)
                
                QMessageBox.information(
                    self,
                    self.get_text("ui.voice_test", default="Voice Test"),
                    self.get_text("ui.voice_test_message", default="Voice test started. You should hear EVA speaking now.")
                )
            else:
                QMessageBox.warning(
                    self,
                    self.get_text("ui.voice_test", default="Voice Test"),
                    self.get_text("ui.voice_test_unavailable", default="Voice test unavailable. Speech synthesizer not initialized.")
                )
                
        except Exception as e:
            logger.error(f"Error testing voice: {str(e)}")
            QMessageBox.critical(
                self,
                self.language_manager.get_text("ui.dialogs.error"),
                self.get_text("ui.error_testing_voice", default="Error testing voice") + f": {str(e)}"
            )

    def test_vad_configuration(self):
        """Test the currently selected VAD configuration"""
        try:
            selected_mode = self.vad_mode_combo.currentData()

            # Mode descriptions for user feedback
            mode_descriptions = {
                1: self.get_text("ui.vad_mode_1_desc", default="Sensitive mode - detects quiet speech but may pick up some background noise"),
                2: self.get_text("ui.vad_mode_2_desc", default="Balanced mode - optimal for most environments with good noise filtering"),
                3: self.get_text("ui.vad_mode_3_desc", default="Conservative mode - maximum noise filtering, requires clear speech")
            }

            mode_desc = mode_descriptions.get(selected_mode, mode_descriptions[2])

            # Try to test VAD if voice engine is available
            if self.chat_window.voice_engine is not None:
                # Temporarily update VAD config for testing
                temp_config = self.config.copy()
                if "vad" not in temp_config:
                    temp_config["vad"] = {}
                temp_config["vad"]["enabled"] = True
                temp_config["vad"]["mode"] = selected_mode

                # Apply temporary config to voice engine
                self.chat_window.voice_engine.update_vad_config(temp_config.get("vad", {}))

                QMessageBox.information(
                    self,
                    self.get_text("ui.vad_test", default="VAD Test"),
                    self.get_text("ui.vad_test_message", default="VAD configuration updated. Try speaking to test the new settings.\n\nSelected mode: {mode}\n\n{description}").format(
                        mode=self.vad_mode_combo.currentText().split(" - ")[0],
                        description=mode_desc
                    )
                )
            else:
                QMessageBox.information(
                    self,
                    self.get_text("ui.vad_test", default="VAD Test"),
                    self.get_text("ui.vad_test_preview", default="VAD Configuration Preview:\n\nSelected mode: {mode}\n\n{description}\n\nSettings will be applied when you save.").format(
                        mode=self.vad_mode_combo.currentText().split(" - ")[0],
                        description=mode_desc
                    )
                )

        except Exception as e:
            logger.error(f"Error testing VAD configuration: {str(e)}")
            QMessageBox.critical(
                self,
                self.language_manager.get_text("ui.dialogs.error"),
                self.get_text("ui.error_testing_vad", default="Error testing VAD configuration") + f": {str(e)}"
            )

    def test_microphone_button(self):
        """Handle microphone test button click"""
        try:
            if self.chat_window is None or self.chat_window.command_processor is None:
                QMessageBox.warning(self, "Error", "Voice engine not available")
                return

            voice_engine = self.chat_window.command_processor.eva.voice_engine
            if voice_engine is None:
                QMessageBox.warning(self, "Error", "Voice engine not initialized yet")
                return

            self.test_mic_btn.setEnabled(False)
            self.test_mic_btn.setText("⏳ Testing...")
            QApplication.processEvents()

            result = voice_engine.test_microphone(duration=3)

            self.test_mic_btn.setEnabled(True)
            self.test_mic_btn.setText("🎤 " + self.get_text("ui.test_microphone", default="Test Microphone"))

            if result["success"]:
                has_audio = result.get("has_audio", False)
                avg_rms = result.get("avg_rms", 0)
                max_rms = result.get("max_rms", 0)
                device = result.get("device", "Unknown")

                if has_audio:
                    status = "✅ PASS"
                    detail = (f"Microphone '{device}' is working correctly!\n"
                             f"  Average RMS: {avg_rms:.1f}\n"
                             f"  Peak RMS: {max_rms:.1f}\n"
                             f"  Status: Audio detected")
                else:
                    status = "⚠️ LOW AUDIO"
                    detail = (f"Microphone '{device}' is detected but audio level is very low.\n"
                             f"  Average RMS: {avg_rms:.1f}\n"
                             f"  Peak RMS: {max_rms:.1f}\n"
                             f"  Possible causes:\n"
                             f"    - Microphone is muted\n"
                             f"    - Microphone sensitivity is too low\n"
                             f"    - Privacy settings blocking access\n\n"
                             f"  Try adjusting your microphone settings in Windows.")

                self.mic_test_result_label.setText(f"{status}\n{detail}")
                self.mic_test_result_label.setStyleSheet(
                    "font-size: 11px; color: #4caf50; margin-top: 5px;" if has_audio
                    else "font-size: 11px; color: #ff9800; margin-top: 5px;"
                )
            else:
                error = result.get("error", "Unknown error")
                status_text = (f"❌ FAILED\n"
                              f"Error: {error}\n\n"
                              f"Troubleshooting:\n"
                              f"  1. Check microphone is connected\n"
                              f"  2. Check Windows Privacy > Microphone settings\n"
                              f"  3. Check no other app is using the microphone\n"
                              f"  4. Try running EVA as Administrator")
                self.mic_test_result_label.setText(status_text)
                self.mic_test_result_label.setStyleSheet("font-size: 11px; color: #ff5252; margin-top: 5px;")

        except Exception as e:
            logger.error(f"Error in microphone test: {str(e)}")
            self.test_mic_btn.setEnabled(True)
            self.test_mic_btn.setText("🎤 " + self.get_text("ui.test_microphone", default="Test Microphone"))
            self.mic_test_result_label.setText(f"❌ Error: {str(e)}")
            self.mic_test_result_label.setStyleSheet("font-size: 11px; color: #ff5252; margin-top: 5px;")

    def diagnose_audio_button(self):
        """Handle audio diagnosis button click"""
        try:
            if self.chat_window is None or self.chat_window.command_processor is None:
                QMessageBox.warning(self, "Error", "Voice engine not available")
                return

            voice_engine = self.chat_window.command_processor.eva.voice_engine
            if voice_engine is None:
                QMessageBox.warning(self, "Error", "Voice engine not initialized yet")
                return

            result = voice_engine.diagnose_audio_system()

            # Format diagnosis results
            lines = ["🔍 AUDIO SYSTEM DIAGNOSIS", "=" * 40]

            lines.append(f"\nDefault Input Device: {result.get('default_input', 'N/A')}")
            lines.append(f"Selected Input Device: {result.get('selected_input', 'N/A')}")
            lines.append(f"Has Valid Input: {'Yes' if result.get('has_valid_input') else 'No'}")

            lines.append(f"\n📋 DEVICES ({len(result.get('devices', []))} found):")
            for dev in result.get("devices", []):
                marker = " ← DEFAULT" if dev.get("is_default") else ""
                input_marker = " [INPUT]" if dev.get("is_input") else ""
                lines.append(f"  [{dev['index']}] {dev['name']}"
                           f" (in:{dev['max_input_ch']} out:{dev['max_output_ch']}){input_marker}{marker}")

            if result.get("issues"):
                lines.append("\n⚠️ ISSUES:")
                for issue in result["issues"]:
                    lines.append(f"  - {issue}")

            lines.append("\n" + "=" * 40)

            # Show in message box
            msg = QMessageBox.information(
                self,
                "Audio System Diagnosis",
                "\n".join(lines)
            )

        except Exception as e:
            logger.error(f"Error in audio diagnosis: {str(e)}")
            QMessageBox.critical(self, "Error", f"Diagnosis failed: {str(e)}")

    # Legacy Coqui models loading removed - using Piper TTS

    # Hardware settings method removed - obsolete after Piper TTS migration
    # Piper TTS uses CPU exclusively, Ollama manages GPU automatically
    # Original method contained 44 lines of obsolete GPU configuration UI

    def setup_update_settings(self):
        """Configuración del sistema de actualizaciones"""
        self.update_group = QGroupBox(self.get_text("ui.updates_section", default="Updates Configuration"))
        layout = QVBoxLayout(self.update_group)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 15, 8, 8)

        # Verificación automática de actualizaciones
        auto_check_layout = QVBoxLayout()
        auto_check_header = QHBoxLayout()
        self.auto_check_label = QLabel(self.get_text("ui.auto_check_updates", default="Check Updates Automatically") + ":")
        auto_check_header.addWidget(self.auto_check_label)
        self.auto_check_updates = QCheckBox()
        self.auto_check_updates.setChecked(self.config.get("updates", {}).get("check_automatically", True))
        self.auto_check_updates.stateChanged.connect(self.on_auto_check_changed)
        auto_check_header.addStretch()
        auto_check_header.addWidget(self.auto_check_updates)
        auto_check_layout.addLayout(auto_check_header)
        
        auto_check_desc = QLabel(self.get_text("ui.updates_auto_check_description", default="When enabled, EVA will automatically check if new versions are available."))
        auto_check_desc.setWordWrap(True)
        auto_check_desc.setStyleSheet("font-size: 10px; color: #888888; margin-left: 20px;")
        auto_check_layout.addWidget(auto_check_desc)
        layout.addLayout(auto_check_layout)

        # Intervalo de verificación
        interval_layout = QVBoxLayout()
        self.interval_label = QLabel(self.get_text("ui.check_interval", default="Check Interval (hours)") + ":")
        interval_layout.addWidget(self.interval_label)

        interval_slider_layout = QHBoxLayout()
        interval_slider_layout.addWidget(QLabel(self.get_text("ui.one_hour", default="1h")))
        self.interval_slider = QSlider(Qt.Horizontal)
        self.interval_slider.setRange(1, 24)
        self.interval_slider.setValue(self.config.get("updates", {}).get("check_interval_hours", 6))
        self.interval_slider.valueChanged.connect(self.on_interval_changed)
        interval_slider_layout.addWidget(self.interval_slider)
        interval_slider_layout.addWidget(QLabel(self.get_text("ui.twenty_four_hours", default="24h")))
        
        # Etiqueta para mostrar el valor actual
        self.interval_value_label = QLabel(f"{self.interval_slider.value()}h")
        self.interval_value_label.setStyleSheet("font-weight: bold; color: #00bcd4;")
        interval_slider_layout.addWidget(self.interval_value_label)
        
        interval_layout.addLayout(interval_slider_layout)
        layout.addLayout(interval_layout)

        # Solo notificaciones críticas
        critical_only_layout = QVBoxLayout()
        critical_only_header = QHBoxLayout()
        self.critical_only_label = QLabel(self.get_text("ui.critical_only", default="Notify Critical Updates Only") + ":")
        critical_only_header.addWidget(self.critical_only_label)
        self.critical_only_check = QCheckBox()
        self.critical_only_check.setChecked(self.config.get("updates", {}).get("notify_critical_only", False))
        critical_only_header.addStretch()
        critical_only_header.addWidget(self.critical_only_check)
        critical_only_layout.addLayout(critical_only_header)
        
        critical_desc = QLabel(self.get_text("ui.updates_critical_only_description", default="Only show notifications for security updates or critical fixes."))
        critical_desc.setWordWrap(True)
        critical_desc.setStyleSheet("font-size: 10px; color: #888888; margin-left: 20px;")
        critical_only_layout.addWidget(critical_desc)
        layout.addLayout(critical_only_layout)

        # Crear backups automáticos
        backup_layout = QVBoxLayout()
        backup_header = QHBoxLayout()
        self.backup_label = QLabel(self.get_text("ui.auto_backup", default="Create Automatic Backups") + ":")
        backup_header.addWidget(self.backup_label)
        self.backup_check = QCheckBox()
        self.backup_check.setChecked(self.config.get("updates", {}).get("create_backups", True))
        backup_header.addStretch()
        backup_header.addWidget(self.backup_check)
        backup_layout.addLayout(backup_header)
        
        backup_desc = QLabel(self.get_text("ui.updates_backup_description", default="Automatically create a backup before each update."))
        backup_desc.setWordWrap(True)
        backup_desc.setStyleSheet("font-size: 10px; color: #888888; margin-left: 20px;")
        backup_layout.addWidget(backup_desc)
        layout.addLayout(backup_layout)

        # Botón para verificar actualizaciones manualmente
        manual_check_btn = QPushButton(self.get_text("ui.check_updates_now", default="Check Updates Now"))
        manual_check_btn.setStyleSheet("background-color: rgba(33, 150, 243, 0.3);")
        manual_check_btn.clicked.connect(self.check_updates_manually)
        layout.addWidget(manual_check_btn)

        # Estado de la última verificación
        self.last_check_label = QLabel(self.get_text("ui.last_check", default="Last check:") + " " + self.get_text("ui.never", default="Never"))
        self.last_check_label.setStyleSheet("font-size: 11px; color: #aaaaaa; margin-top: 5px;")
        self.update_last_check_display()
        layout.addWidget(self.last_check_label)

        self.scrollable_content_layout.addWidget(self.update_group)

    def setup_knowledge_base_settings(self):
        """Nueva sección para editar la base de conocimiento de forma visual"""
        self.knowledge_group = QGroupBox(self.get_text("ui.knowledge_base_section", default="Personal Knowledge Base"))
        layout = QVBoxLayout(self.knowledge_group)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 15, 8, 8)

        # Información explicativa
        info_label = QLabel(self.get_text("ui.knowledge_base_description", default="Customize how EVA knows you and behaves with you. These settings are saved in eva_knowledge_base.json"))
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 11px; color: #aaaaaa; margin-bottom: 8px;")
        layout.addWidget(info_label)

        # Perfil de usuario
        profile_frame = QFrame()
        profile_frame.setStyleSheet("background-color: rgba(40, 40, 50, 0.5); border-radius: 6px; padding: 8px;")
        profile_layout = QVBoxLayout(profile_frame)
        profile_layout.addWidget(QLabel(self.get_text("ui.user_profile", default="👤 User Profile")))
        
        # Zona horaria
        timezone_layout = QHBoxLayout()
        timezone_layout.addWidget(QLabel(self.get_text("ui.timezone", default="Timezone:")))
        self.timezone_combo = QComboBox()
        # Timezone options - these are standard timezone identifiers, no translation needed
        self.timezone_combo.addItems([
            "Europe/Madrid", "Europe/London", "America/Mexico_City", 
            "America/New_York", "America/Los_Angeles", "Asia/Tokyo", 
            "Asia/Shanghai", "Australia/Sydney"
        ])
        timezone_layout.addWidget(self.timezone_combo)
        profile_layout.addLayout(timezone_layout)
        
        # Horario de trabajo
        work_hours_layout = QHBoxLayout()
        work_hours_layout.addWidget(QLabel(self.get_text("ui.work_hours", default="Work Hours:")))
        self.work_start_time = QLineEdit()
        self.work_start_time.setPlaceholderText(self.get_text("ui.default_start_time", default="09:00"))
        self.work_start_time.setMaximumWidth(60)
        self.work_end_time = QLineEdit()
        self.work_end_time.setPlaceholderText(self.get_text("ui.default_end_time", default="18:00"))
        self.work_end_time.setMaximumWidth(60)
        work_hours_layout.addWidget(self.work_start_time)
        work_hours_layout.addWidget(QLabel(self.get_text("ui.to", default="to")))
        work_hours_layout.addWidget(self.work_end_time)
        work_hours_layout.addStretch()
        profile_layout.addLayout(work_hours_layout)
        
        layout.addWidget(profile_frame)

        # Atajos personalizados
        shortcuts_frame = QFrame()
        shortcuts_frame.setStyleSheet("background-color: rgba(40, 40, 50, 0.5); border-radius: 6px; padding: 8px;")
        shortcuts_layout = QVBoxLayout(shortcuts_frame)
        shortcuts_layout.addWidget(QLabel(self.get_text("ui.custom_shortcuts", default="⚡ Custom Shortcuts")))
        
        self.shortcuts_list = QListWidget()
        self.shortcuts_list.setMaximumHeight(100)
        self.shortcuts_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(30, 30, 40, 0.8);
                border: 1px solid rgba(77, 182, 172, 0.3);
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 4px;
                border-bottom: 1px solid rgba(77, 182, 172, 0.1);
            }
            QListWidget::item:selected {
                background-color: rgba(0, 188, 212, 0.3);
            }
        """)
        shortcuts_layout.addWidget(self.shortcuts_list)
        
        shortcuts_btn_layout = QHBoxLayout()
        add_shortcut_btn = QPushButton(self.get_text("ui.add", default="Add"))
        add_shortcut_btn.setStyleSheet("background-color: rgba(76, 175, 80, 0.3); min-width: 60px;")
        edit_shortcut_btn = QPushButton(self.get_text("ui.edit", default="Edit"))
        edit_shortcut_btn.setStyleSheet("background-color: rgba(255, 152, 0, 0.3); min-width: 60px;")
        delete_shortcut_btn = QPushButton(self.get_text("ui.remove", default="Remove"))
        delete_shortcut_btn.setStyleSheet("background-color: rgba(244, 67, 54, 0.3); min-width: 60px;")
        
        add_shortcut_btn.clicked.connect(self.add_custom_shortcut)
        edit_shortcut_btn.clicked.connect(self.edit_custom_shortcut)
        delete_shortcut_btn.clicked.connect(self.delete_custom_shortcut)
        
        shortcuts_btn_layout.addWidget(add_shortcut_btn)
        shortcuts_btn_layout.addWidget(edit_shortcut_btn)
        shortcuts_btn_layout.addWidget(delete_shortcut_btn)
        shortcuts_btn_layout.addStretch()
        shortcuts_layout.addLayout(shortcuts_btn_layout)
        
        layout.addWidget(shortcuts_frame)

        # Preferencias de comportamiento
        behavior_frame = QFrame()
        behavior_frame.setStyleSheet("background-color: rgba(40, 40, 50, 0.5); border-radius: 6px; padding: 8px;")
        behavior_layout = QVBoxLayout(behavior_frame)
        behavior_layout.addWidget(QLabel(self.get_text("ui.behavior", default="🎯 Behavior")))
        
        self.contextual_greetings_check = QCheckBox(self.get_text("ui.contextual_greetings", default="Contextual greetings (Good morning, good afternoon, etc.)"))
        self.auto_suggestions_check = QCheckBox(self.get_text("ui.auto_suggestions", default="Automatic suggestions based on frequent commands"))
        
        behavior_layout.addWidget(self.contextual_greetings_check)
        behavior_layout.addWidget(self.auto_suggestions_check)
        layout.addWidget(behavior_frame)

        # Botón para abrir editor avanzado
        advanced_btn = QPushButton(self.get_text("ui.advanced_knowledge_editor", default="📝 Advanced Knowledge Base Editor"))
        advanced_btn.setStyleSheet("background-color: rgba(156, 39, 176, 0.3);")
        advanced_btn.clicked.connect(self.open_advanced_knowledge_editor)
        layout.addWidget(advanced_btn)

        self.scrollable_content_layout.addWidget(self.knowledge_group)

    def setup_plugins_settings(self):
        """Nueva sección para configuración de plugins (Tavily API key, etc.)"""
        self.plugins_group = QGroupBox(self.get_text("ui.plugins_section", default="Plugins"))
        layout = QVBoxLayout(self.plugins_group)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 15, 8, 8)

        # Descripción
        info_label = QLabel(self.get_text("ui.plugins_description", default="Configure external services and API keys for extended functionality."))
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 11px; color: #aaaaaa; margin-bottom: 8px;")
        layout.addWidget(info_label)

        # API Key de Tavily
        tavily_frame = QFrame()
        tavily_frame.setStyleSheet("background-color: rgba(40, 40, 50, 0.5); border-radius: 6px; padding: 8px;")
        tavily_layout = QVBoxLayout(tavily_frame)

        # Título
        tavily_layout.addWidget(QLabel("🔑 Tavily Web Search"))

        # Campo de API Key
        api_key_layout = QHBoxLayout()
        self.tavily_api_key_label = QLabel(self.get_text("ui.tavily_api_key_label", default="API Key") + ":")
        api_key_layout.addWidget(self.tavily_api_key_label)
        self.tavily_api_key_input = QLineEdit()
        self.tavily_api_key_input.setPlaceholderText(self.get_text("ui.tavily_api_key_placeholder", default="Enter your Tavily API key"))
        self.tavily_api_key_input.setEchoMode(QLineEdit.Normal)
        self.tavily_api_key_input.setMinimumWidth(300)
        api_key_layout.addWidget(self.tavily_api_key_input, 1)
        tavily_layout.addLayout(api_key_layout)

        # Botón de validación y limpieza
        api_key_btn_layout = QHBoxLayout()
        self.tavily_validate_btn = QPushButton(self.get_text("ui.validate", default="Validate"))
        self.tavily_validate_btn.setStyleSheet("background-color: rgba(76, 175, 80, 0.3); min-width: 80px;")
        self.tavily_validate_btn.clicked.connect(self.validate_tavily_key)
        api_key_btn_layout.addWidget(self.tavily_validate_btn)

        self.tavily_clear_btn = QPushButton(self.get_text("ui.tavily_clear_key", default="Clear"))
        self.tavily_clear_btn.setStyleSheet("background-color: rgba(244, 67, 54, 0.3); min-width: 80px;")
        self.tavily_clear_btn.clicked.connect(self.clear_tavily_key)
        api_key_btn_layout.addWidget(self.tavily_clear_btn)

        api_key_btn_layout.addStretch()
        tavily_layout.addLayout(api_key_btn_layout)

        # Hint label
        self.tavily_hint_label = QLabel(self.get_text("ui.tavily_api_key_hint", default="Get a free API key at https://tavily.com"))
        self.tavily_hint_label.setStyleSheet("font-size: 10px; color: #888888; margin-top: 4px;")
        tavily_layout.addWidget(self.tavily_hint_label)

        # Status label
        self.tavily_status_label = QLabel("")
        self.tavily_status_label.setStyleSheet("font-size: 10px; color: #4caf50; margin-top: 4px;")
        tavily_layout.addWidget(self.tavily_status_label)

        layout.addWidget(tavily_frame)

        # Configuración de búsqueda Tavily
        search_config_frame = QFrame()
        search_config_frame.setStyleSheet("background-color: rgba(40, 40, 50, 0.5); border-radius: 6px; padding: 8px; margin-top: 4px;")
        search_config_layout = QVBoxLayout(search_config_frame)

        # Profundidad de búsqueda
        depth_layout = QHBoxLayout()
        depth_label = QLabel(self.get_text("ui.tavily_search_depth", default="Search Depth") + ":")
        depth_layout.addWidget(depth_label)
        self.tavily_depth_combo = QComboBox()
        self.tavily_depth_combo.addItem(self.get_text("ui.tavily_search_depth_basic", default="Basic"), "basic")
        self.tavily_depth_combo.addItem(self.get_text("ui.tavily_search_depth_advanced", default="Advanced"), "advanced")
        depth_layout.addWidget(self.tavily_depth_combo, 1)
        search_config_layout.addLayout(depth_layout)

        # Máximo de resultados
        results_layout = QHBoxLayout()
        results_label = QLabel(self.get_text("ui.tavily_max_results", default="Max Results") + ":")
        results_layout.addWidget(results_label)
        self.tavily_max_results_input = QLineEdit()
        self.tavily_max_results_input.setPlaceholderText("3")
        self.tavily_max_results_input.setMaximumWidth(60)
        results_layout.addWidget(self.tavily_max_results_input)
        results_layout.addStretch()
        search_config_layout.addLayout(results_layout)

        layout.addWidget(search_config_frame)

        # Info label about when search will be disabled
        disable_info = QLabel(self.get_text("ui.tavily_no_key_warning", default="Tavily web search will be disabled if no API key is provided."))
        disable_info.setWordWrap(True)
        disable_info.setStyleSheet("font-size: 10px; color: #ff9800; margin-top: 8px;")
        layout.addWidget(disable_info)

        self.scrollable_content_layout.addWidget(self.plugins_group)

    def setup_openrouter_settings(self):
        """Seccion de configuracion para OpenRouter AI"""
        self.openrouter_group = QGroupBox(self.get_text("ui.openrouter_section", default="OpenRouter AI"))
        layout = QVBoxLayout(self.openrouter_group)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 15, 8, 8)

        info_label = QLabel(self.get_text("ui.openrouter_description", default="OpenRouter provides cloud-based AI models. Configure your API key below."))
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 11px; color: #aaaaaa; margin-bottom: 8px;")
        layout.addWidget(info_label)

        # API Key
        api_key_layout = QHBoxLayout()
        self.openrouter_api_key_label = QLabel(self.get_text("ui.openrouter_api_key", default="API Key") + ":")
        api_key_layout.addWidget(self.openrouter_api_key_label)
        self.openrouter_api_key_input = QLineEdit()
        self.openrouter_api_key_input.setPlaceholderText(
            self.get_text("ui.openrouter_api_key_placeholder", default="Enter your OpenRouter API key")
        )
        self.openrouter_api_key_input.setEchoMode(QLineEdit.Password)
        self.openrouter_api_key_input.setMinimumWidth(300)
        api_key_layout.addWidget(self.openrouter_api_key_input, 1)
        layout.addLayout(api_key_layout)

        # Model selector
        model_layout = QHBoxLayout()
        self.openrouter_model_label = QLabel(self.get_text("ui.openrouter_model", default="Model") + ":")
        model_layout.addWidget(self.openrouter_model_label)
        self.openrouter_model_combo = QComboBox()
        try:
            from commands.ai_provider import OpenRouterProvider
            for m in OpenRouterProvider.OPENROUTER_MODELS:
                self.openrouter_model_combo.addItem(m, m)
        except ImportError:
            self.openrouter_model_combo.addItem("openrouter/free", "openrouter/free")
        model_layout.addWidget(self.openrouter_model_combo, 1)
        layout.addLayout(model_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.openrouter_test_btn = QPushButton(self.get_text("ui.openrouter_test", default="Test Connection"))
        self.openrouter_test_btn.setStyleSheet("background-color: rgba(76, 175, 80, 0.3); min-width: 80px;")
        self.openrouter_test_btn.clicked.connect(self.test_openrouter_connection)
        btn_layout.addWidget(self.openrouter_test_btn)

        self.openrouter_clear_btn = QPushButton(self.get_text("ui.openrouter_clear", default="Clear"))
        self.openrouter_clear_btn.setStyleSheet("background-color: rgba(244, 67, 54, 0.3); min-width: 80px;")
        self.openrouter_clear_btn.clicked.connect(self.clear_openrouter_key)
        btn_layout.addWidget(self.openrouter_clear_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Status label
        self.openrouter_status_label = QLabel("")
        self.openrouter_status_label.setStyleSheet("font-size: 10px; color: #888888; margin-top: 4px;")
        layout.addWidget(self.openrouter_status_label)

        # Hint
        hint_label = QLabel(
            self.get_text("ui.openrouter_hint", default="Get a free API key at https://openrouter.ai/keys")
        )
        hint_label.setStyleSheet("font-size: 10px; color: #888888; margin-top: 4px;")
        hint_label.setOpenExternalLinks(True)
        layout.addWidget(hint_label)

        warning_label = QLabel(
            self.get_text("ui.openrouter_no_key_warning", default="OpenRouter will be disabled if no API key is provided. Ollama will be used as fallback.")
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("font-size: 10px; color: #ff9800; margin-top: 8px;")
        layout.addWidget(warning_label)

        self.scrollable_content_layout.addWidget(self.openrouter_group)

    def load_openrouter_settings(self):
        """Carga la configuracion de OpenRouter en la interfaz"""
        try:
            or_config = self.config.get("openrouter", {})
            self.openrouter_api_key_input.setText(or_config.get("api_key", ""))

            current_model = or_config.get("model", "openrouter/free")
            for i in range(self.openrouter_model_combo.count()):
                if self.openrouter_model_combo.itemData(i) == current_model:
                    self.openrouter_model_combo.setCurrentIndex(i)
                    break

            if or_config.get("api_key", ""):
                self.openrouter_status_label.setText(
                    self.get_text("ui.openrouter_key_configured", default="API key configured")
                )
                self.openrouter_status_label.setStyleSheet("font-size: 10px; color: #4caf50; margin-top: 4px;")
            else:
                self.openrouter_status_label.setText("")

        except Exception as e:
            logger.error(f"Error loading OpenRouter settings: {str(e)}")

    def test_openrouter_connection(self):
        """Prueba la conexion con OpenRouter (no bloqueante)"""
        key = self.openrouter_api_key_input.text().strip()
        if not key:
            self.openrouter_status_label.setText(
                self.get_text("ui.openrouter_api_key_required", default="API key is required.")
            )
            self.openrouter_status_label.setStyleSheet("font-size: 10px; color: #ff5252; margin-top: 4px;")
            return

        self.openrouter_test_btn.setEnabled(False)
        self.openrouter_test_btn.setText(self.get_text("ui.openrouter_testing", default="Testing..."))
        self.openrouter_status_label.setText(
            self.get_text("ui.openrouter_testing", default="Testing connection...")
        )
        self.openrouter_status_label.setStyleSheet("font-size: 10px; color: #ff9800; margin-top: 4px;")
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

        class TestThread(QThread):
            result_ready = Signal(str, bool)

            def __init__(self, api_key):
                super().__init__()
                self.api_key = api_key

            def run(self):
                try:
                    from openai import OpenAI
                    client = OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=self.api_key,
                        default_headers={
                            "HTTP-Referer": "http://localhost:5000",
                            "X-Title": "EVA Asistente",
                        },
                        timeout=15.0,
                    )
                    response = client.chat.completions.create(
                        model="openrouter/free",
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=5,
                    )
                    if response and response.choices:
                        self.result_ready.emit(
                            "Connection successful!", True
                        )
                    else:
                        self.result_ready.emit("No response from OpenRouter", False)
                except Exception as e:
                    self.result_ready.emit(str(e), False)

        self._test_thread = TestThread(key)
        self._test_thread.result_ready.connect(self._on_openrouter_test_result)
        self._test_thread.start()

    def _on_openrouter_test_result(self, message: str, success: bool):
        self.openrouter_test_btn.setEnabled(True)
        self.openrouter_test_btn.setText(self.get_text("ui.openrouter_test", default="Test Connection"))
        if success:
            self.openrouter_status_label.setText(
                self.get_text("ui.openrouter_connection_ok", default="Connection successful!")
            )
            self.openrouter_status_label.setStyleSheet("font-size: 10px; color: #4caf50; margin-top: 4px;")
        else:
            self.openrouter_status_label.setText(
                self.get_text("ui.openrouter_connection_failed", default="Connection failed") + f": {message}"
            )
            self.openrouter_status_label.setStyleSheet("font-size: 10px; color: #ff5252; margin-top: 4px;")

    def clear_openrouter_key(self):
        """Borra la API key de OpenRouter"""
        self.openrouter_api_key_input.setText("")
        self.openrouter_status_label.setText(
            self.get_text("ui.openrouter_key_cleared", default="API key cleared")
        )
        self.openrouter_status_label.setStyleSheet("font-size: 10px; color: #ff9800; margin-top: 4px;")

    def load_plugins_settings(self):
        """Carga la configuración de plugins en la interfaz"""
        try:
            plugins = self.config.get("plugins", {})

            # API Key de Tavily
            self.tavily_api_key_input.setText(plugins.get("tavily_api_key", ""))

            # Profundidad de búsqueda
            search_depth = plugins.get("tavily_search_depth", "basic")
            for i in range(self.tavily_depth_combo.count()):
                if self.tavily_depth_combo.itemData(i) == search_depth:
                    self.tavily_depth_combo.setCurrentIndex(i)
                    break

            # Máximo de resultados
            max_results = plugins.get("tavily_max_results", 3)
            self.tavily_max_results_input.setText(str(max_results))

            # Update status
            if plugins.get("tavily_api_key", ""):
                self.tavily_status_label.setText(self.get_text("ui.tavily_key_set", default="API key configured"))
                self.tavily_status_label.setStyleSheet("font-size: 10px; color: #4caf50; margin-top: 4px;")
            else:
                self.tavily_status_label.setText("")

        except Exception as e:
            logger.error(f"Error loading plugins settings: {str(e)}")

    def validate_tavily_key(self):
        """Valida la API key de Tavily"""
        key = self.tavily_api_key_input.text().strip()
        if not key:
            self.tavily_status_label.setText(self.get_text("ui.tavily_api_key_required", default="API key is required to use Tavily web search."))
            self.tavily_status_label.setStyleSheet("font-size: 10px; color: #ff5252; margin-top: 4px;")
            return
        if len(key) < 20:
            self.tavily_status_label.setText(self.get_text("ui.tavily_api_key_invalid", default="API key must be at least 20 characters."))
            self.tavily_status_label.setStyleSheet("font-size: 10px; color: #ff5252; margin-top: 4px;")
            return
        self.tavily_status_label.setText(self.get_text("ui.tavily_key_set", default="API key configured"))
        self.tavily_status_label.setStyleSheet("font-size: 10px; color: #4caf50; margin-top: 4px;")

    def clear_tavily_key(self):
        """Borra la API key de Tavily"""
        self.tavily_api_key_input.setText("")
        self.tavily_status_label.setText(self.get_text("ui.tavily_key_cleared", default="API key cleared"))
        self.tavily_status_label.setStyleSheet("font-size: 10px; color: #ff9800; margin-top: 4px;")

    def add_custom_shortcut(self):
        """Abre el diálogo para añadir un nuevo atajo personalizado"""
        try:
            try:
                from ui.shortcut_editor_dialog import ShortcutEditorDialog
            except ImportError:
                ShortcutEditorDialog = None
            
            dialog = ShortcutEditorDialog(parent=self, language_manager=self.language_manager)
            if dialog.exec() == QDialog.Accepted:
                shortcut_data = dialog.get_shortcut_data()
                if shortcut_data:
                    # Cargar base de conocimiento actual
                    knowledge_base = self.load_knowledge_base()
                    
                    # Añadir el nuevo atajo
                    if "custom_shortcuts" not in knowledge_base:
                        knowledge_base["custom_shortcuts"] = {}
                    
                    knowledge_base["custom_shortcuts"][shortcut_data["name"].lower()] = shortcut_data["commands"]
                    
                    # Guardar cambios
                    self.save_knowledge_base(knowledge_base)
                    
                    # Actualizar la lista visual
                    self.load_shortcuts_list()
                    
                    QMessageBox.information(
                        self,
                        self.get_text("ui.shortcut_created", default="Shortcut created"),
                        self.get_text("ui.shortcut_created_message", default="The shortcut '{name}' has been created successfully.\n\nYou can use it by saying: '{name}'").format(name=shortcut_data['name'])
                    )
                    
        except Exception as e:
            logger.error(f"Error añadiendo atajo personalizado: {str(e)}")
            QMessageBox.critical(self, self.language_manager.get_text("ui.dialogs.error"), f"Error creando atajo: {str(e)}")

    def edit_custom_shortcut(self):
        """Edita el atajo seleccionado"""
        try:
            current_item = self.shortcuts_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, self.language_manager.get_text("ui.selection_required"), self.get_text("ui.select_command_edit", default="Please select a command to edit."))
                return
            
            # Extraer nombre del atajo del texto del item
            shortcut_name = current_item.text().split(" →")[0].strip()
            
            # Cargar base de conocimiento
            knowledge_base = self.load_knowledge_base()
            shortcuts = knowledge_base.get("custom_shortcuts", {})
            
            if shortcut_name.lower() not in shortcuts:
                QMessageBox.warning(self, self.language_manager.get_text("ui.dialogs.error"), "Shortcut not found.")
                return
            
            # Preparar datos para el editor
            shortcut_data = {
                "name": shortcut_name,
                "commands": shortcuts[shortcut_name.lower()]
            }
            
            try:
                from ui.shortcut_editor_dialog import ShortcutEditorDialog
            except ImportError:
                ShortcutEditorDialog = None
                
            if ShortcutEditorDialog:
                dialog = ShortcutEditorDialog(shortcut_data, parent=self, language_manager=self.language_manager)
            else:
                QMessageBox.warning(self, "Error", "Shortcut editor not available")
                return
            
            if dialog.exec() == QDialog.Accepted:
                new_data = dialog.get_shortcut_data()
                if new_data:
                    # Eliminar el atajo anterior si cambió el nombre
                    if new_data["name"].lower() != shortcut_name.lower():
                        del shortcuts[shortcut_name.lower()]
                    
                    # Actualizar con los nuevos datos
                    shortcuts[new_data["name"].lower()] = new_data["commands"]
                    
                    # Guardar cambios
                    self.save_knowledge_base(knowledge_base)
                    
                    # Actualizar lista visual
                    self.load_shortcuts_list()
                    
                    QMessageBox.information(
                        self,
                        self.get_text("ui.shortcut_updated", default="Shortcut updated"),
                        self.get_text("ui.shortcut_updated_message", default="The shortcut '{name}' has been updated successfully.").format(name=new_data['name'])
                    )
                    
        except Exception as e:
            logger.error(f"Error editando atajo: {str(e)}")
            QMessageBox.critical(self, self.language_manager.get_text("ui.dialogs.error"), f"Error editando atajo: {str(e)}")

    def delete_custom_shortcut(self):
        """Elimina el atajo seleccionado"""
        try:
            current_item = self.shortcuts_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, self.language_manager.get_text("ui.selection_required"), self.get_text("ui.select_shortcut_delete", default="Please select a shortcut to delete."))
                return
            
            # Extraer nombre del atajo
            shortcut_name = current_item.text().split(" →")[0].strip()
            
            reply = QMessageBox.question(
                self,
                self.language_manager.get_text("ui.dialogs.confirmation"),
                self.get_text("ui.confirm_delete_shortcut", default="Are you sure you want to delete the shortcut '{name}'?").format(name=shortcut_name),
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Cargar y modificar base de conocimiento
                knowledge_base = self.load_knowledge_base()
                shortcuts = knowledge_base.get("custom_shortcuts", {})
                
                if shortcut_name.lower() in shortcuts:
                    del shortcuts[shortcut_name.lower()]
                    
                    # Guardar cambios
                    self.save_knowledge_base(knowledge_base)
                    
                    # Actualizar lista visual
                    self.load_shortcuts_list()
                    
                    QMessageBox.information(
                        self,
                        self.get_text("ui.shortcut_deleted", default="Shortcut deleted"),
                        self.get_text("ui.shortcut_deleted_message", default="The shortcut '{name}' has been deleted successfully.").format(name=shortcut_name)
                    )
                    
        except Exception as e:
            logger.error(f"Error eliminando atajo: {str(e)}")
            QMessageBox.critical(self, self.language_manager.get_text("ui.dialogs.error"), f"Error eliminando atajo: {str(e)}")

    def open_advanced_knowledge_editor(self):
        """Abre un editor avanzado para la base de conocimiento completa"""
        try:
            try:
                from ui.advanced_knowledge_editor import AdvancedKnowledgeEditor
            except ImportError:
                AdvancedKnowledgeEditor = None
            
            dialog = AdvancedKnowledgeEditor(parent=self)
            if dialog.exec() == QDialog.Accepted:
                # Recargar la configuración después de los cambios
                self.load_knowledge_base_settings()
                QMessageBox.information(
                    self,
                    self.get_text("ui.knowledge_base_updated", default="Knowledge base updated"),
                    self.get_text("ui.knowledge_base_updated_message", default="Changes to the knowledge base have been saved successfully.")
                )
                
        except ImportError:
            # Si no existe el editor avanzado, mostrar mensaje informativo
            QMessageBox.information(
                self,
                self.get_text("ui.advanced_editor_title", default="Advanced Editor"),
                self.get_text("ui.advanced_editor_message") or "The advanced editor allows you to directly modify the eva_knowledge_base.json file.\n\n"
                    "File location:\n"
                    "• eva_knowledge_base.json (in EVA folder)\n\n"
                    "You can edit it with any text editor, but be careful with JSON syntax."
            )
        except Exception as e:
            logger.error(f"Error abriendo editor avanzado: {str(e)}")
            QMessageBox.critical(self, self.language_manager.get_text("ui.dialogs.error"), f"Error abriendo editor avanzado: {str(e)}")

    def load_knowledge_base(self):
        """Carga la base de conocimiento desde el archivo JSON"""
        try:
            import os
            knowledge_file = "eva_knowledge_base.json"
            
            if os.path.exists(knowledge_file):
                with open(knowledge_file, "r", encoding="utf-8") as f:
                    import json
                    return json.load(f)
            else:
                # Crear estructura básica si no existe
                return {
                    "user_profile": {
                        "name": self.config.get("user_name", "Usuario"),
                        "timezone": "Europe/Madrid",
                        "work_hours": "09:00-18:00"
                    },
                    "custom_shortcuts": {},
                    "preferences": {
                        "contextual_greetings": True,
                        "auto_suggestions": True
                    }
                }
        except Exception as e:
            logger.error(f"Error cargando base de conocimiento: {str(e)}")
            return {}

    def save_knowledge_base(self, knowledge_base):
        """Guarda la base de conocimiento en el archivo JSON y sincroniza con chat_window"""
        try:
            import json
            with open("eva_knowledge_base.json", "w", encoding="utf-8") as f:
                json.dump(knowledge_base, f, indent=4, ensure_ascii=False)
            logger.info("Base de conocimiento guardada exitosamente")
            
            # Sincronizar con la ventana de chat si existe
            if hasattr(self, 'chat_window') and self.chat_window:
                self.chat_window.knowledge_base = knowledge_base
                logger.info("Base de conocimiento sincronizada con chat_window")
                
        except Exception as e:
            logger.error(f"Error guardando base de conocimiento: {str(e)}")
            raise

    def load_shortcuts_list(self):
        """Carga la lista de atajos personalizados en la interfaz"""
        try:
            self.shortcuts_list.clear()
            knowledge_base = self.load_knowledge_base()
            shortcuts = knowledge_base.get("custom_shortcuts", {})
            
            if not shortcuts:
                from PySide6.QtWidgets import QListWidgetItem
                item = QListWidgetItem(self.get_text("ui.no_shortcuts_configured", default="No custom shortcuts configured"))
                item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
                self.shortcuts_list.addItem(item)
            else:
                for name, commands in shortcuts.items():
                    if isinstance(commands, list):
                        commands_preview = ", ".join(commands[:2])
                        if len(commands) > 2:
                            more_text = self.get_text("ui.more_commands", default="more")
                        commands_preview += f" ... (+{len(commands)-2} {more_text})"
                    else:
                        commands_preview = str(commands)
                    
                    item_text = f"{name.title()} → {commands_preview}"
                    self.shortcuts_list.addItem(item_text)
                    
        except Exception as e:
            logger.error(f"Error cargando lista de atajos: {str(e)}")

    def load_knowledge_base_settings(self):
        """Carga la configuración de la base de conocimiento en la interfaz"""
        try:
            knowledge_base = self.load_knowledge_base()
            
            # Cargar perfil de usuario
            user_profile = knowledge_base.get("user_profile", {})
            
            # Zona horaria
            timezone = user_profile.get("timezone", "Europe/Madrid")
            index = self.timezone_combo.findText(timezone)
            if index >= 0:
                self.timezone_combo.setCurrentIndex(index)
            
            # Horario de trabajo
            work_hours = user_profile.get("work_hours", "09:00-18:00")
            if "-" in work_hours:
                start_time, end_time = work_hours.split("-")
                self.work_start_time.setText(start_time.strip())
                self.work_end_time.setText(end_time.strip())
            
            # Preferencias
            preferences = knowledge_base.get("preferences", {})
            self.contextual_greetings_check.setChecked(preferences.get("contextual_greetings", True))
            self.auto_suggestions_check.setChecked(preferences.get("auto_suggestions", True))
            
            # Cargar lista de atajos
            self.load_shortcuts_list()
            
        except Exception as e:
            logger.error(f"Error cargando configuración de base de conocimiento: {str(e)}")

    def save_knowledge_base_settings(self):
        """Guarda la configuración de la base de conocimiento"""
        try:
            knowledge_base = self.load_knowledge_base()
            
            # Actualizar perfil de usuario
            if "user_profile" not in knowledge_base:
                knowledge_base["user_profile"] = {}
            
            knowledge_base["user_profile"]["timezone"] = self.timezone_combo.currentText()
            
            # Horario de trabajo
            start_time = self.work_start_time.text().strip() or "09:00"
            end_time = self.work_end_time.text().strip() or "18:00"
            knowledge_base["user_profile"]["work_hours"] = f"{start_time}-{end_time}"
            
            # Preferencias
            if "preferences" not in knowledge_base:
                knowledge_base["preferences"] = {}
            
            knowledge_base["preferences"]["contextual_greetings"] = self.contextual_greetings_check.isChecked()
            knowledge_base["preferences"]["auto_suggestions"] = self.auto_suggestions_check.isChecked()
            
            # Guardar cambios
            self.save_knowledge_base(knowledge_base)
            
        except Exception as e:
            logger.error(f"Error guardando configuración de base de conocimiento: {str(e)}")
            raise

    def on_auto_check_changed(self, state):
        """Maneja el cambio en la verificación automática en tiempo real"""
        try:
            enabled = state == Qt.Checked.value
            
            # Actualizar configuración inmediatamente
            if "updates" not in self.config:
                self.config["updates"] = {}
            self.config["updates"]["check_automatically"] = enabled
            
            # Aplicar cambios en tiempo real si EVA tiene update_manager
            if hasattr(self.chat_window, 'command_processor') and \
               hasattr(self.chat_window.command_processor, 'eva') and \
               hasattr(self.chat_window.command_processor.eva, 'update_manager'):
                
                update_manager = self.chat_window.command_processor.eva.update_manager
                update_manager.auto_check_enabled = enabled
                
                if enabled:
                    update_manager.start_periodic_checks()
                    logger.info("Verificación automática de actualizaciones ACTIVADA")
                else:
                    update_manager.stop_periodic_checks()
                    logger.info("Verificación automática de actualizaciones DESACTIVADA")
                
                # Emitir señal para notificar el cambio
                self.settings_updated.emit(self.config)
                
        except Exception as e:
            logger.error(f"Error aplicando cambio de verificación automática: {str(e)}")

    def on_interval_changed(self, value):
        """Maneja el cambio en el intervalo de verificación en tiempo real"""
        try:
            # Actualizar etiqueta del valor
            self.interval_value_label.setText(f"{value}h")
            
            # Actualizar configuración inmediatamente
            if "updates" not in self.config:
                self.config["updates"] = {}
            self.config["updates"]["check_interval_hours"] = value
            
            # Aplicar cambios en tiempo real si EVA tiene update_manager
            if hasattr(self.chat_window, 'command_processor') and \
               hasattr(self.chat_window.command_processor, 'eva') and \
               hasattr(self.chat_window.command_processor.eva, 'update_manager'):
                
                update_manager = self.chat_window.command_processor.eva.update_manager
                update_manager.check_interval_hours = value
                
                # Reiniciar el timer con el nuevo intervalo si está activo
                if update_manager.auto_check_enabled and update_manager.check_timer.isActive():
                    update_manager.stop_periodic_checks()
                    update_manager.start_periodic_checks()
                    logger.info(f"Intervalo de verificación actualizado a {value} horas")
                
                # Emitir señal para notificar el cambio
                self.settings_updated.emit(self.config)
                
        except Exception as e:
            logger.error(f"Error aplicando cambio de intervalo: {str(e)}")

    def check_updates_manually(self):
        """Verifica actualizaciones manualmente"""
        try:
            if hasattr(self.chat_window, 'command_processor') and \
               hasattr(self.chat_window.command_processor, 'eva') and \
               hasattr(self.chat_window.command_processor.eva, 'update_manager'):
                
                update_manager = self.chat_window.command_processor.eva.update_manager
                update_manager.check_for_updates(silent=False)
                
                # Actualizar display de última verificación
                self.update_last_check_display()
                
                # Mostrar mensaje de confirmación
                QMessageBox.information(
                    self,
                    self.get_text("ui.updates_check_started", default="Update Check Started"),
                    self.get_text("ui.updates_check_started_message", default="Update check has been initiated. You will receive a notification if updates are available.")
                )
                
            else:
                QMessageBox.warning(
                    self,
                    self.language_manager.get_text("ui.dialogs.error"),
                    self.get_text("ui.updates_system_unavailable", default="Updates system unavailable.")
                )
                
        except Exception as e:
            logger.error(f"Error en verificación manual: {str(e)}")
            QMessageBox.critical(
                self,
                self.language_manager.get_text("ui.dialogs.error"),
                f"Error checking updates: {str(e)}"
            )

    def update_last_check_display(self):
        """Actualiza la información de la última verificación"""
        try:
            if hasattr(self.chat_window, 'command_processor') and \
               hasattr(self.chat_window.command_processor, 'eva') and \
               hasattr(self.chat_window.command_processor.eva, 'update_manager'):
                
                update_manager = self.chat_window.command_processor.eva.update_manager
                last_check = update_manager.get_last_check_time()
                
                if last_check:
                    time_diff = datetime.now() - last_check
                    if time_diff.days > 0:
                        time_str = self.get_text("ui.ago_days", default="{days} days ago").format(days=time_diff.days)
                    elif time_diff.seconds > 3600:
                        hours = time_diff.seconds // 3600
                        time_str = self.get_text("ui.ago_hours", default="{hours} hours ago").format(hours=hours)
                    elif time_diff.seconds > 60:
                        minutes = time_diff.seconds // 60
                        time_str = self.get_text("ui.ago_minutes", default="{minutes} minutes ago").format(minutes=minutes)
                    else:
                        time_str = self.get_text("ui.ago_seconds", default="few seconds ago")
                    
                    self.last_check_label.setText(f"{self.get_text('ui.last_check', default='Last check:')} {time_str}")
                else:
                    self.last_check_label.setText(f"{self.get_text('ui.last_check', default='Last check:')} {self.get_text('ui.never', default='Never')}")
                    
        except Exception as e:
            logger.error(f"Error actualizando display de última verificación: {str(e)}")
            self.last_check_label.setText(f"{self.get_text('ui.last_check', default='Last check:')} Error")

    # Legacy TTS Management methods removed - Piper TTS doesn't need complex management

    def setup_action_buttons(self):
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 8, 0, 0)

        # Create buttons without text first
        self.save_btn = QPushButton()
        self.cancel_btn = QPushButton()
        
        # Set initial text based on current language
        self.update_button_texts()
            
        self.save_btn.setStyleSheet(
            """
            background-color: rgba(76, 175, 80, 0.4);
            min-width: 80px;
            max-width: 120px;
            padding: 8px 12px;
            font-weight: 600;
            font-size: 13px;
        """
        )
        self.save_btn.clicked.connect(self.save_settings)

        self.cancel_btn.setStyleSheet(
            """
            background-color: rgba(244, 67, 54, 0.4);
            min-width: 80px;
            max-width: 120px;
            padding: 8px 12px;
            font-weight: 600;
            font-size: 13px;
        """
        )
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        self.layout.addWidget(btn_frame)

    def update_button_texts(self):
        """Update button texts based on current language"""
        
        # Clear existing text first to prevent overlay
        self.save_btn.setText("")
        self.cancel_btn.setText("")
        
        # Process events to ensure clearing is complete
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        # Set new text based on language using translation keys
        self.save_btn.setText(self.get_text("ui.save", default="Save"))
        self.cancel_btn.setText(self.get_text("ui.cancel", default="Cancel"))
        
        # Process events again to ensure new text is displayed
        QApplication.processEvents()

    def update_voice_combo_items(self):
        """Update voice combo box items based on current language"""
        # Clear existing items
        self.voice_combo.clear()
        
        # Add only 2 voice options
        spanish_voice_text = self.get_text("ui.eva_spanish_voice", default="🇪🇸 EVA Español")
        english_voice_text = self.get_text("ui.eva_english_voice", default="🇺🇸 EVA English")
        
        self.voice_combo.addItem(spanish_voice_text, "es")
        self.voice_combo.addItem(english_voice_text, "en")
        
        # Set current selection based on config
        current_voice = self.config.get("tts", {}).get("voice_variant", "es")
        if current_voice == "en":
            self.voice_combo.setCurrentIndex(1)  # English voice
        else:
            self.voice_combo.setCurrentIndex(0)  # Spanish voice (default)

    def update_vad_combo_items(self):
        """Update VAD combo box items based on current language"""
        # Clear existing items
        self.vad_mode_combo.clear()
        
        # Add 3 VAD mode options
        conservative_text = self.get_text("ui.vad_conservative", default="🛡️ Conservative - Maximum noise filtering")
        balanced_text = self.get_text("ui.vad_balanced", default="⚖️ Balanced - Optimal for most environments")
        sensitive_text = self.get_text("ui.vad_sensitive", default="🎯 Sensitive - Detects quiet speech")
        
        self.vad_mode_combo.addItem(conservative_text, 3)  # WebRTC VAD mode 3 (most aggressive)
        self.vad_mode_combo.addItem(balanced_text, 2)      # WebRTC VAD mode 2 (balanced)
        self.vad_mode_combo.addItem(sensitive_text, 1)     # WebRTC VAD mode 1 (least aggressive)
        
        # Set current selection based on config
        current_mode = self.config.get("vad", {}).get("mode", 2)  # Default to balanced
        if current_mode == 3:
            self.vad_mode_combo.setCurrentIndex(0)  # Conservative
        elif current_mode == 1:
            self.vad_mode_combo.setCurrentIndex(2)  # Sensitive
        else:
            self.vad_mode_combo.setCurrentIndex(1)  # Balanced (default)

    def update_all_dynamic_texts(self):
        """Update ALL dynamic text elements that might not be translated"""
        try:
            # Update slider labels that might be hardcoded
            # Find and update all QLabel widgets with hardcoded text
            for widget in self.findChildren(QLabel):
                text = widget.text()
                if text == "1h":
                    widget.setText("1h")  # This is universal
                elif text == "24h":
                    widget.setText("24h")  # This is universal
                elif text == "to" and self.language_manager.current_lang == "es":
                    widget.setText("a")
                elif text == "a" and self.language_manager.current_lang == "en":
                    widget.setText("to")
                    
            # Update any other dynamic elements
            self.repaint()
        except Exception as e:
            logger.error(f"Error updating dynamic texts: {str(e)}")

    def update_all_dynamic_content(self):
        """Update ALL dynamic content when language changes"""
        try:
            # Update voice section content
            if hasattr(self, 'voice_info'):
                voice_info_text = self.get_text("ui.piper_voice_description", 
                    "EVA now uses Piper TTS with premium female voices for both Spanish and English. "
                    "These voices provide excellent quality with instant synthesis and no memory issues.")
                self.voice_info.setText(voice_info_text)
            
            # Update auto listen description
            if hasattr(self, 'auto_listen_desc'):
                auto_listen_desc_text = self.get_text("ui.auto_listen_description", default="When enabled, EVA continuously listens for voice commands. Disable to use only text chat.")
                self.auto_listen_desc.setText(auto_listen_desc_text)
            
            # Update voice details
            if hasattr(self, 'spanish_details'):
                spanish_details_text = "• " + self.get_text("ui.spanish_voice_details", default="Español: Voz femenina natural con pronunciación mexicana clara")
                self.spanish_details.setText(spanish_details_text)
            
            if hasattr(self, 'english_details'):
                english_details_text = "• " + self.get_text("ui.english_voice_details", default="English: Clear American female voice, perfect for professional communication")
                self.english_details.setText(english_details_text)
            
            # Update voice details title
            if hasattr(self, 'voice_details_title'):
                voice_details_title_text = "🎤 " + self.get_text("ui.voice_details", default="Voice Details")
                self.voice_details_title.setText(voice_details_title_text)
            
            # Update VAD section content
            for widget in self.findChildren(QLabel):
                text = widget.text()
                if "🎙️ Voice Activity Detection" in text or "🎙️ Detección de Actividad de Voz" in text:
                    widget.setText("🎙️ " + self.get_text("ui.vad_title", default="Voice Activity Detection"))
                elif "VAD filters background noise" in text or "VAD filtra el ruido de fondo" in text:
                    widget.setText(self.get_text("ui.vad_description", default="VAD filters background noise and only processes speech, reducing CPU usage by 60-80%."))
                elif "Detection Mode:" in text or "Modo de Detección:" in text:
                    widget.setText(self.get_text("ui.vad_mode", default="Detection Mode") + ":")
            
            # Update VAD test button
            for widget in self.findChildren(QPushButton):
                text = widget.text()
                if "🧪 Test VAD Configuration" in text or "🧪 Probar Configuración VAD" in text:
                    widget.setText("🧪 " + self.get_text("ui.vad_test", default="Test VAD Configuration"))
            
            # Update all other dynamic content
            self.update_all_dynamic_texts()
            
        except Exception as e:
            logger.error(f"Error updating dynamic content: {str(e)}")

    def load_stored_license(self):
        """Stub: siempre PREMIUM."""
        pass

    def validate_license(self):
        """Stub: siempre válida."""
        pass

    def remove_license(self):
        """Stub: no hay licencia que eliminar."""
        pass

    def open_gpu_config(self):
        # GPU config dialog removed - obsolete after Piper TTS migration
        # Piper TTS uses CPU only, Ollama manages GPU automatically
        pass

    # update_gpu_info method removed - obsolete after Piper TTS migration
    # Original method contained 32 lines of GPU detection and display logic
    # Piper TTS uses CPU exclusively, no GPU configuration needed

    def load_current_settings(self):
        # Load values from existing configuration
        self.auto_start_check.setChecked(self.config.get("auto_start", False))
        self.minimize_check.setChecked(self.config.get("minimize_start", True))

        # Cargar volumen con manejo seguro
        volume_value = self.config.get("tts", {}).get("volume", 0.8)
        self.volume_slider.setValue(int(volume_value * 100))
        self.volume_value_label.setText(f"{int(volume_value * 100)}%")

        # Cargar velocidad de voz
        speed_value = self.config.get("tts", {}).get("speed", 1.0)
        self.speed_slider.setValue(int(speed_value * 100))
        self.speed_value_label.setText(f"{speed_value:.1f}x")

        # Cargar configuración de escucha automática
        self.auto_listen_check.setChecked(self.config.get("auto_listen", True))

        # Cargar sensibilidad con manejo seguro
        sensitivity_value = self.config.get("sensitivity", 0.5)
        self.sensitivity_slider.setValue(int(sensitivity_value * 100))

        # Cargar nombre de usuario
        self.name_input.setText(self.chat_window.user_name)

        # Piper TTS voice configuration - default to Spanish
        current_voice = self.config.get("tts", {}).get("voice_variant", "es")
        if current_voice == "en":
            self.voice_combo.setCurrentIndex(1)  # English voice
        else:
            self.voice_combo.setCurrentIndex(0)  # Spanish voice (default)

        # Load VAD configuration
        if hasattr(self, 'vad_mode_combo'):
            vad_mode = self.config.get("vad", {}).get("mode", 2)  # Default to balanced mode
            if vad_mode == 3:
                self.vad_mode_combo.setCurrentIndex(0)  # Conservative
            elif vad_mode == 1:
                self.vad_mode_combo.setCurrentIndex(2)  # Sensitive
            else:
                self.vad_mode_combo.setCurrentIndex(1)  # Balanced (default)

        # GPU configuration removed - obsolete after Piper TTS migration

        # GPU info update removed - obsolete after Piper TTS migration

        # Language - ensure proper button states
        lang = self.config.get("language", "es")
        if lang == "es":
            self.es_button.setChecked(True)
            self.en_button.setChecked(False)
        else:
            self.es_button.setChecked(False)
            self.en_button.setChecked(True)

    def save_settings(self):
        try:
            # Save to configuration
            self.config["auto_start"] = self.auto_start_check.isChecked()
            self.config["minimize_start"] = self.minimize_check.isChecked()

            # Ensure tts section exists
            if "tts" not in self.config:
                self.config["tts"] = {}

            # Save Piper TTS configuration
            self.config["tts"]["engine"] = "piper"
            self.config["tts"]["volume"] = self.volume_slider.value() / 100
            self.config["tts"]["speed"] = self.speed_slider.value() / 100
            
            # Save selected voice variant
            selected_voice = self.voice_combo.currentData()
            self.config["tts"]["voice_variant"] = selected_voice
            
            # Set voice models based on selection
            if selected_voice == "es_castellano":
                self.config["tts"]["voice_model"] = "es_MX-claude-high"  # Mexican model with Spanish adaptation
                self.config["tts"]["language"] = "es"
                self.config["tts"]["apply_spanish_filter"] = True
            elif selected_voice == "es_neutro":
                self.config["tts"]["voice_model"] = "es_MX-claude-high"  # Mexican model natural
                self.config["tts"]["language"] = "es"
                self.config["tts"]["apply_spanish_filter"] = False
            else:  # en
                self.config["tts"]["voice_model"] = "en_US-kristin-medium"
                self.config["tts"]["language"] = "en"
                self.config["tts"]["apply_spanish_filter"] = False

            # Disable legacy TTS systems
            self.config["tts"]["use_coqui"] = False
            self.config["tts"]["use_melo"] = False
            self.config["tts"]["use_windows_voices"] = False

            self.config["auto_listen"] = self.auto_listen_check.isChecked()
            self.config["sensitivity"] = self.sensitivity_slider.value() / 100

            # Save VAD configuration
            if hasattr(self, 'vad_mode_combo'):
                if "vad" not in self.config:
                    self.config["vad"] = {}
                
                # Get selected VAD mode
                selected_vad_mode = self.vad_mode_combo.currentData()
                self.config["vad"]["enabled"] = True  # VAD is always enabled when configured
                self.config["vad"]["mode"] = selected_vad_mode
                
                # Set additional VAD parameters based on mode
                if selected_vad_mode == 3:  # Conservative
                    self.config["vad"]["frame_duration"] = 30  # ms
                    self.config["vad"]["padding_duration"] = 300  # ms
                elif selected_vad_mode == 1:  # Sensitive
                    self.config["vad"]["frame_duration"] = 10  # ms
                    self.config["vad"]["padding_duration"] = 100  # ms
                else:  # Balanced (mode 2)
                    self.config["vad"]["frame_duration"] = 20  # ms
                    self.config["vad"]["padding_duration"] = 200  # ms

            # GPU configuration removed - obsolete after Piper TTS migration

            # Save language
            lang = self.config.get("language", "es")
            if lang == "es":
                self.es_button.setChecked(True)
            else:
                self.en_button.setChecked(True)

            # Guardar nombre de usuario
            self.config["user_name"] = self.name_input.text().strip()

            # Guardar configuración de actualizaciones
            if hasattr(self, 'auto_check_updates'):
                if "updates" not in self.config:
                    self.config["updates"] = {}
                
                self.config["updates"]["check_automatically"] = self.auto_check_updates.isChecked()
                self.config["updates"]["check_interval_hours"] = self.interval_slider.value()
                self.config["updates"]["notify_critical_only"] = self.critical_only_check.isChecked()
                self.config["updates"]["create_backups"] = self.backup_check.isChecked()

            # Guardar configuración de plugins
            if "plugins" not in self.config:
                self.config["plugins"] = {}
            self.config["plugins"]["tavily_api_key"] = self.tavily_api_key_input.text().strip()

            # Guardar configuración de búsqueda Tavily
            if hasattr(self, 'tavily_depth_combo'):
                self.config["plugins"]["tavily_search_depth"] = self.tavily_depth_combo.currentData()
            if hasattr(self, 'tavily_max_results_input'):
                try:
                    max_results = int(self.tavily_max_results_input.text().strip())
                    self.config["plugins"]["tavily_max_results"] = max(1, min(10, max_results))
                except ValueError:
                    self.config["plugins"]["tavily_max_results"] = 3

            # Guardar configuración de OpenRouter
            if "openrouter" not in self.config:
                self.config["openrouter"] = {}
            or_api_key = self.openrouter_api_key_input.text().strip()
            self.config["openrouter"]["api_key"] = or_api_key
            self.config["openrouter"]["model"] = self.openrouter_model_combo.currentData()

            # Cambiar proveedor activo si se configuró API key
            if or_api_key:
                self.config["ai_provider"] = "openrouter"
            else:
                self.config["ai_provider"] = "ollama"

            # Guardar configuración de base de conocimiento
            self.save_knowledge_base_settings()

            # Save to disk via unified ConfigManager
            config_manager.save()

            logger.info("Configuration saved successfully via ConfigManager")

            # Show success message
            QMessageBox.information(
                self,
                self.get_text("ui.settings_updated", default="Settings Updated"),
                self.get_text("ui.piper_settings_saved", 
                    "Piper TTS settings have been saved successfully. "
                    "EVA will now use premium female voices for both Spanish and English."),
            )

            self.settings_updated.emit(self.config)
            self.accept()

        except Exception as e:
            logger.error(f"Error saving Piper TTS configuration: {str(e)}")
            QMessageBox.critical(
                self, self.language_manager.get_text("ui.dialogs.error"), 
                self.get_text("ui.could_not_save_config", default="Could not save Piper TTS configuration") + f": {str(e)}"
            )

    def open_store(self):
        webbrowser.open("https://tu-sitio.com/comprar-eva")

    def open_custom_commands(self):
        dialog = CustomCommandsDialog(self.config, self.language_manager, self)
        if dialog.exec() == QDialog.Accepted:
            self.config = dialog.config
            logger.info("Personalización avanzada guardada")
            self.settings_updated.emit(self.config)
