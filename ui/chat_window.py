import logging
import os
from datetime import datetime

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QThread, QTimer, Signal
from PySide6.QtGui import (QFont, QTextCursor, QPainter, QPainterPath)
from PySide6.QtWidgets import (QComboBox, QFileDialog, QFrame,
                                QHBoxLayout, QLabel,
                                QLineEdit, QPushButton,
                                QScrollArea, QStatusBar, QTextBrowser,
                                QVBoxLayout, QWidget)

from core.config_manager_unified import config_manager
from ui.chat_controller import ChatController

try:
    from ui.custom_commands_dialog import CustomCommandsDialog
except ImportError:
    CustomCommandsDialog = None

try:
    from ui.settings_window import SettingsWindow
except ImportError:
    SettingsWindow = None

logger = logging.getLogger("EVA")


class ChatWindow(QWidget):
    """Chat window UI. Business logic is delegated to ChatController."""

    language_changed = Signal(str)
    update_message_signal = Signal(str, bool)

    def __init__(self, config, session_manager, language_manager):
        super().__init__()
        self.eva_title_label = None
        self.settings_button = None
        self.chat_history = None
        self.message_input = None
        self.send_button = None
        self.status_bar = None
        self.lang_combo = None
        self.time_container = None
        self.time_label = None
        self.voice_indicator = None
        self.premium_btn = None
        self.timer = None
        self.mute_button = None

        self.shadow = None
        self.animation = None
        self.drag_start_position = None
        self.config = config
        self.session_manager = session_manager
        self.language_manager = language_manager
        self.setWindowTitle(self.language_manager.get_text("ui.window_title"))
        logger.info("Constructor EVAChatWindow iniciado")

        self.is_painting = False
        self.valid_paint_state = False
        self.pending_updates = False

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)

        self.supported_file_types = ['.pdf', '.txt', '.md', '.csv', '.json', '.docx', '.odt']

        self.update_message_signal.connect(self.add_message)

        # Controller delegates business logic
        self.controller = ChatController(config, session_manager, language_manager, self)
        self.controller.message_received.connect(self.add_message)
        self.controller.language_applied.connect(self._on_language_applied)

        # Backward compat aliases
        self.command_processor = None
        self.is_muted = False

        logger.info("Iniciando UI...")
        self.init_ui()
        logger.info("UI inicializada correctamente")

    def isValid(self):
        return (self.width() > 0 and self.height() > 0 and self.valid_paint_state and
                self.testAttribute(Qt.WA_WState_Created))

    @property
    def speech_synthesizer(self):
        return self.controller.speech_synthesizer

    @property
    def voice_engine(self):
        return self.controller.voice_engine

    # --- Delegated properties for backward compat ---

    @property
    def user_name(self):
        return self.controller.user_name

    @user_name.setter
    def user_name(self, value):
        self.controller.user_name = value

    @property
    def knowledge_base(self):
        return self.controller.knowledge_base

    @knowledge_base.setter
    def knowledge_base(self, value):
        self.controller.knowledge_base = value

    @property
    def is_muted(self):
        return self.controller.is_muted

    @is_muted.setter
    def is_muted(self, value):
        self.controller.is_muted = value

    @staticmethod
    def load_knowledge_base():
        return ChatController._load_knowledge_base(ChatController)

    def save_knowledge_base(self):
        self.controller.save_knowledge_base()

    def _migrate_old_knowledge_base(self):
        self.controller._migrate_old_knowledge_base()

    def _log_session_start(self):
        self.controller._log_session_start()

    def log_command_usage(self, command_text):
        self.controller.log_command_usage(command_text)

    def update_context_memory(self, question=None, response=None, topic=None, document=None):
        self.controller.update_context_memory(question, response, topic, document)

    def add_custom_shortcut(self, shortcut_name, commands):
        return self.controller.add_custom_shortcut(shortcut_name, commands)

    def execute_custom_shortcut(self, shortcut_name):
        return self.controller.execute_custom_shortcut(shortcut_name)

    def get_contextual_greeting(self):
        return self.controller.get_contextual_greeting()

    def get_command_suggestions(self):
        return self.controller.get_command_suggestions()

    def get_conversation_context_for_ollama(self, current_question=None):
        return self.controller.get_conversation_context_for_ollama(current_question)

    def update_user_name(self, new_name):
        self.controller.update_user_name(new_name)
        welcome_message = self.language_manager.get_text("responses.welcome_message").format(user=new_name)
        self.chat_history.setHtml(
            f"<div style='margin-bottom:15px;'><span style='color:#00bcd4; font-weight:600;'>{self.language_manager.get_text('responses.eva')} [{datetime.now().strftime('%H:%M')}]:</span> <span style='color:#e0f7fa;'>{welcome_message}</span></div>"
        )

    def _on_language_applied(self, lang):
        self.update_ui_texts()
        self.repaint()
        self.language_changed.emit(lang)
        msg = self.language_manager.get_text("ui.notifications.language_changed") or "Language changed successfully"
        self.add_message(msg, is_user=False)

    def add_message(self, text, is_user=True):
        """Añade un mensaje al chat. Thread-safe: fuerza ejecución en hilo principal."""
        try:
            # FIX THREAD-SAFE: Si no estamos en el hilo principal, reprogramar
            if QThread.currentThread() != self.thread():
                QTimer.singleShot(0, lambda: self.add_message(text, is_user))
                return

            timestamp = datetime.now().strftime("%H:%M")
            if is_user:
                formatted = f"<div style='margin-bottom: 10px;'><span style='color:#a7ffeb; font-weight:600;'>{self.language_manager.get_text('responses.you')} [{timestamp}]:</span> <span style='color:#e0f7fa;'>{text}</span></div>"
            else:
                formatted = f"<div style='margin-bottom: 15px;'><span style='color:#00bcd4; font-weight:600;'>{self.language_manager.get_text('responses.eva')} [{timestamp}]:</span> <span style='color:#e0f7fa;'>{text}</span></div>"
                logger.debug("🎵 TTS activation handled by command processor - skipping duplicate")
            self.chat_history.append(formatted)
            cursor = self.chat_history.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.chat_history.setTextCursor(cursor)
            self.chat_history.ensureCursorVisible()
        except Exception as e:
            logger.error(f"Error añadiendo mensaje: {str(e)}")

    def safe_add_message(self, message, is_user=False):
        if hasattr(self, 'update_message_signal'):
            self.update_message_signal.emit(message, is_user)
        else:
            try:
                self.add_message(message, is_user)
            except Exception as e:
                logger.warning(f"Error adding message directly: {e}")
                QTimer.singleShot(0, lambda: self.add_message(message, is_user))

    def replace_last_message(self, text, is_user=True):
        try:
            cursor = self.chat_history.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deletePreviousChar()
            self.add_message(text, is_user)
        except Exception as e:
            logger.error(f"Error reemplazando mensaje: {str(e)}")
            self.add_message(text, is_user)

    def load_config(self):
        try:
            if "window_position" in self.config:
                x, y = self.config["window_position"]
                if x < -1000 or y < -1000:
                    logger.warning(f"Posición inválida: {x}, {y}, usando valores por defecto")
                else:
                    self.move(x, y)
            if "window_size" in self.config:
                width, height = self.config["window_size"]
                if width < 200 or height < 150:
                    logger.warning(f"Tamaño inválido: {width}x{height}, usando valores por defecto")
                    self.resize(500, 400)
                else:
                    self.resize(width, height)
            else:
                self.resize(500, 400)
            if "font_size" in self.config:
                font_size = self.config["font_size"]
                if font_size < 8 or font_size > 24:
                    logger.warning(f"Tamaño de fuente inválido: {font_size}, usando 12")
                    font_size = 12
                font = QFont("Segoe UI", font_size)
                self.chat_history.setFont(font)
            logger.info("Configuración de ventana cargada")
        except Exception as e:
            logger.error(f"Error cargando configuración: {str(e)}")
            self.resize(500, 400)

    def save_config(self):
        if self.isVisible():
            self.config["window_position"] = [self.x(), self.y()]
            self.config["window_size"] = [self.width(), self.height()]
            current_font_size = self.chat_history.font().pointSize()
            if current_font_size > 0 and 8 <= current_font_size <= 72:
                self.config["font_size"] = current_font_size
            else:
                self.config["font_size"] = self.config.get("font_size", 12)
                logger.warning(f"Font size inválido detectado ({current_font_size}), manteniendo valor actual")
            config_manager.save()
            logger.info("Configuración de ventana guardada")

    def init_ui(self):
        logger.info("Configurando UI básica...")
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
            | Qt.WindowStaysOnTopHint
        )
        self.setFocusPolicy(Qt.StrongFocus)

        try:
            from core.dynamic_path_resolver import dynamic_path_resolver
        except ImportError:
            dynamic_path_resolver = None
        icon_path = dynamic_path_resolver.get_icon_path("ico")
        if os.path.exists(icon_path):
            from PySide6.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))
        else:
            logger.warning("Icono de ventana no encontrado en: " + icon_path)

        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAttribute(Qt.WA_NoSystemBackground, False)

        # Estilo premium (corregido, sin propiedades CSS no soportadas)
        # Inline stylesheet removed – styles are now loaded from styles.qss centrally

        main_frame = QFrame()
        main_frame.setObjectName("mainFrame")
        main_frame.setStyleSheet("background-color: transparent; border-radius: 12px; border: 1px solid rgba(100, 100, 120, 0.2);")

        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        title_bar = QWidget()
        title_bar.setObjectName("titleBar")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 5, 10, 5)
        title_bar_layout.setSpacing(10)

        self.eva_title_label = QLabel(self.language_manager.get_text("ui.title"))
        self.eva_title_label.setObjectName("EvaTitle")
        self.eva_title_label.setStyleSheet("font-size: 18px; font-weight: 600; color: #bb86fc; padding: 5px;")
        title_bar_layout.addWidget(self.eva_title_label)

        title_bar_layout.addStretch()

        # Botón de voz
        self.voice_toggle_button = QPushButton()
        self.voice_toggle_button.setFixedSize(36, 36)
        self.voice_toggle_button.setCheckable(True)
        self.voice_toggle_button.setChecked(self.config.get("auto_listen", False))

        try:
            from PySide6.QtGui import QIcon, QPixmap
            svg_icon_path = os.path.join("resources", "icons", "microphone.svg")
            png_icon_path = os.path.join("resources", "microphone.png")
            if os.path.exists(svg_icon_path):
                icon = QIcon(svg_icon_path)
                self.voice_toggle_button.setIcon(icon)
                self.voice_toggle_button.setIconSize(self.voice_toggle_button.size())
                logger.info(f"✓ Icono SVG de micrófono cargado: {svg_icon_path}")
            elif os.path.exists(png_icon_path):
                pixmap = QPixmap(png_icon_path)
                scaled_pixmap = pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon = QIcon(scaled_pixmap)
                self.voice_toggle_button.setIcon(icon)
                self.voice_toggle_button.setIconSize(scaled_pixmap.size())
                logger.info(f"✓ Icono PNG de micrófono cargado: {png_icon_path}")
            else:
                self.voice_toggle_button.setText("🎙️")
                logger.warning("⚠️ Iconos no encontrados, usando emoji")
        except Exception as e:
            self.voice_toggle_button.setText("🎙️")
            logger.error(f"❌ Error cargando icono: {str(e)}")

        if self.config.get("auto_listen", False):
            initial_style = """
                QPushButton {
                    background-color: rgba(102, 255, 178, 0.3);
                    border: 1px solid rgba(102, 255, 178, 0.5);
                    font-weight: 600;
                    border-radius: 6px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: rgba(102, 255, 178, 0.4);
                    border: 1px solid rgba(102, 255, 178, 0.7);
                }
                QPushButton:pressed {
                    background-color: rgba(102, 255, 178, 0.5);
                    border: 1px solid rgba(102, 255, 178, 0.8);
                }
            """
        else:
            initial_style = """
                QPushButton {
                    background-color: rgba(244, 67, 54, 0.3);
                    border: 1px solid rgba(244, 67, 54, 0.5);
                    font-weight: 600;
                    border-radius: 6px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: rgba(244, 67, 54, 0.4);
                    border: 1px solid rgba(244, 67, 54, 0.7);
                }
                QPushButton:pressed {
                    background-color: rgba(244, 67, 54, 0.5);
                    border: 1px solid rgba(244, 67, 54, 0.8);
                }
            """
        self.voice_toggle_button.setStyleSheet(initial_style)
        self.voice_toggle_button.clicked.connect(self.toggle_voice_listening)
        self.voice_toggle_button.setToolTip(self.language_manager.get_text("ui.voice_toggle_tooltip", default="Activar/Desactivar reconocimiento de voz"))
        title_bar_layout.addWidget(self.voice_toggle_button)

        self.settings_button = QPushButton(self.language_manager.get_text("ui.settings"))
        self.settings_button.setFixedHeight(36)
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(63, 81, 181, 0.2);
                border: 1px solid rgba(63, 81, 181, 0.4);
                font-weight: 600;
                font-size: 12px;
                border-radius: 6px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: rgba(63, 81, 181, 0.3);
                border: 1px solid rgba(63, 81, 181, 0.6);
            }
        """)
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setToolTip(self.language_manager.get_text("ui.settings"))
        title_bar_layout.addWidget(self.settings_button)

        # Mini mode button
        self.mini_mode_button = QPushButton("⊟")
        self.mini_mode_button.setFixedSize(36, 36)
        self.mini_mode_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 188, 212, 0.15);
                border: 1px solid rgba(0, 188, 212, 0.3);
                font-weight: 600;
                font-size: 14px;
                border-radius: 6px;
                padding: 4px;
                color: #4db6ac;
            }
            QPushButton:hover {
                background-color: rgba(0, 188, 212, 0.25);
                border: 1px solid rgba(0, 188, 212, 0.5);
            }
        """)
        self.mini_mode_button.clicked.connect(self.toggle_mini_mode)
        self.mini_mode_button.setToolTip("Modo mini (barra compacta)")
        title_bar_layout.addWidget(self.mini_mode_button)

        main_layout.addWidget(title_bar)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("border: none; background: transparent;")

        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)

        self.chat_history = QTextBrowser()
        self.chat_history.setObjectName("chatHistory")
        self.chat_history.setReadOnly(True)
        self.chat_history.setOpenExternalLinks(True)
        self.chat_history.setStyleSheet("""
            QTextBrowser {
                background-color: rgba(25, 25, 35, 0.6);
                border: none;
                font-family: 'Segoe UI', 'Open Sans', sans-serif;
                font-size: 14px;
                color: #e0f7fa;
                padding: 10px;
            }
            QTextBrowser a {
                color: #4fc3f7;
                text-decoration: none;
                font-weight: 500;
            }
            QTextBrowser a:hover {
                color: #81d4fa;
                text-decoration: underline;
            }
        """)

        contextual_greeting = self.get_contextual_greeting()
        self.chat_history.setHtml(
            f"<div style='margin-bottom:15px;'><span style='color:#00bcd4; font-weight:600;'>{self.language_manager.get_text('responses.eva')} [{datetime.now().strftime('%H:%M')}]:</span> <span style='color:#e0f7fa;'>{contextual_greeting}</span></div>"
        )
        chat_layout.addWidget(self.chat_history)

        QTimer.singleShot(100, self._add_file_info)

        scroll_area.setWidget(chat_container)
        main_layout.addWidget(scroll_area, 1)

        input_frame = QFrame()
        input_frame.setStyleSheet("background-color: rgba(30, 30, 40, 0.6); border-radius: 8px; padding: 10px;")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(5, 5, 5, 5)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText(self.language_manager.get_text("ui.type_message"))
        self.message_input.setFixedHeight(40)
        self.message_input.setStyleSheet("font-size: 14px;")
        self.message_input.returnPressed.connect(self.send_message)
        self.message_input.setFocusPolicy(Qt.StrongFocus)

        input_layout.addWidget(self.message_input, 1)

        self.file_button = QPushButton("📁")
        self.file_button.setFixedSize(40, 40)
        self.file_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(156, 39, 176, 0.3);
                border: 1px solid rgba(156, 39, 176, 0.5);
                font-weight: 600;
                font-size: 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(156, 39, 176, 0.4);
                border: 1px solid rgba(156, 39, 176, 0.7);
            }
        """)
        self.file_button.clicked.connect(self.select_and_process_file)
        self.file_button.setToolTip("Seleccionar archivo para resumir (PDF, TXT, MD, CSV, JSON, DOCX, ODT)")
        input_layout.addWidget(self.file_button)


        self.send_button = QPushButton(self.language_manager.get_text("ui.send"))
        self.send_button.setFixedHeight(40)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 188, 212, 0.3);
                border: 1px solid rgba(0, 188, 212, 0.5);
                min-width: 80px;
                font-weight: 600;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(0, 188, 212, 0.4);
                border: 1px solid rgba(0, 188, 212, 0.7);
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        self.mute_button = QPushButton("🔊")
        self.mute_button.setFixedSize(40, 40)
        self.mute_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(76, 175, 80, 0.3);
                border: 1px solid rgba(76, 175, 80, 0.5);
                font-weight: 600;
                font-size: 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(76, 175, 80, 0.4);
                border: 1px solid rgba(76, 175, 80, 0.7);
            }
        """)
        self.mute_button.clicked.connect(self.toggle_mute)
        self.mute_button.setToolTip("Silenciar/Activar respuestas de EVA")
        input_layout.addWidget(self.mute_button)

        main_layout.addWidget(input_frame)

        self.status_bar = QStatusBar()
        self.status_bar.setSizeGripEnabled(False)
        self.status_bar.setObjectName("statusBar")

        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)

        lang_container = QWidget()
        lang_layout = QHBoxLayout(lang_container)
        lang_layout.setContentsMargins(0, 0, 0, 0)
        lang_label = QLabel(self.language_manager.get_text("ui.language") + ":")
        lang_layout.addWidget(lang_label)

        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Español", "es")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        self.lang_combo.setStyleSheet("min-width: 100px;")
        lang_layout.addWidget(self.lang_combo, 1)
        status_layout.addWidget(lang_container)

        self.time_container = QWidget()
        time_layout = QHBoxLayout(self.time_container)
        time_layout.setContentsMargins(0, 0, 0, 0)
        self.time_label = QLabel()
        self.time_label.setStyleSheet("font-weight: 600;")
        time_layout.addWidget(self.time_label)
        status_layout.addWidget(self.time_container)

        status_layout.addStretch()

        self.voice_indicator = QLabel(self.language_manager.get_text("ui.speaking"))
        self.voice_indicator.setStyleSheet("color: #ff4081; font-weight: bold; padding: 0 10px; font-size: 12px;")
        self.voice_indicator.setVisible(False)
        status_layout.addWidget(self.voice_indicator)

        self.premium_btn = QPushButton("🤖 EVA")
        self.premium_btn.setObjectName("evaBtn")
        self.premium_btn.setMinimumWidth(120)
        self.premium_btn.setMaximumWidth(150)
        self.premium_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9c27b0, stop:1 #673ab7);
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ab47bc, stop:1 #7e57c2);
            }
        """)
        self.premium_btn.clicked.connect(self.show_eva_info)
        status_layout.addWidget(self.premium_btn)

        self.status_bar.addWidget(status_container, 1)
        main_layout.addWidget(self.status_bar)

        self.update_time_display()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_display)
        self.timer.start(1000)

        window_layout = QVBoxLayout(self)
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.addWidget(main_frame)

        # Tab order for keyboard navigation
        self.setTabOrder(self.message_input, self.file_button)
        self.setTabOrder(self.file_button, self.send_button)
        self.setTabOrder(self.send_button, self.mute_button)
        self.setTabOrder(self.mute_button, self.voice_toggle_button)
        self.setTabOrder(self.voice_toggle_button, self.settings_button)
        self.setTabOrder(self.settings_button, self.mini_mode_button)

        self.load_config()
        self.update_ui_texts()
        self.sync_voice_button_state()
        self.fade_in()

    def update_voice_indicator(self, speaking):
        if speaking:
            self.voice_indicator.setText(self.language_manager.get_text("ui.speaking"))
            self.voice_indicator.setVisible(True)
        else:
            self.voice_indicator.setVisible(False)

    def fade_in(self):
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()

    def change_language(self):
        try:
            lang = self.lang_combo.currentData()
            if not self.controller.change_language(lang):
                return
            self.update_ui_texts()
            self.repaint()
            self.update()
            self.language_changed.emit(lang)
            msg = self.language_manager.get_text("ui.notifications.language_changed") or "Language changed successfully"
            self.add_message(msg, is_user=False)
        except Exception as e:
            logger.error(f"Error changing language: {str(e)}")

    def update_ui_texts(self):
        try:
            current_lang = self.language_manager.current_lang
            logger.info(f"🌐 Updating chat window UI texts to: {current_lang}")
            self.setWindowTitle("EVA - Enhancement Assistant Voice")
            if hasattr(self, 'eva_title_label') and self.eva_title_label:
                self.eva_title_label.setText("EVA - Enhancement Assistant Voice")
            if hasattr(self, 'message_input') and self.message_input:
                self.message_input.setPlaceholderText(
                    self.language_manager.get_text("ui.type_message") or "Type your message here..."
                )
            if hasattr(self, 'send_button') and self.send_button:
                self.send_button.setText(self.language_manager.get_text("ui.send") or "Send")
            if hasattr(self, 'lang_combo') and self.lang_combo:
                self.lang_combo.setItemText(0, self.language_manager.get_text("ui.spanish") or "Español")
                self.lang_combo.setItemText(1, self.language_manager.get_text("ui.english") or "English")
            if hasattr(self, 'settings_button') and self.settings_button:
                self.settings_button.setText(self.language_manager.get_text("ui.settings") or "Settings")
                self.settings_button.setToolTip(self.language_manager.get_text("ui.settings") or "Settings")
            if hasattr(self, 'voice_indicator') and self.voice_indicator:
                self.voice_indicator.setText(self.language_manager.get_text("ui.speaking") or "Speaking...")
            if hasattr(self, 'voice_toggle_button') and self.voice_toggle_button:
                if current_lang == "es":
                    tooltip = "Activar/Desactivar reconocimiento de voz"
                else:
                    tooltip = "Enable/Disable voice recognition"
                self.voice_toggle_button.setToolTip(tooltip)
            if hasattr(self, 'mini_mode_button') and self.mini_mode_button:
                if current_lang == "es":
                    self.mini_mode_button.setToolTip("Modo mini (barra compacta)")
                else:
                    self.mini_mode_button.setToolTip("Mini mode (compact bar)")
            if hasattr(self, 'mute_button') and self.mute_button:
                if self.is_muted:
                    self.mute_button.setToolTip(self.language_manager.get_text("ui.notifications.mute_tooltip_on", default="Voice muted - Click to activate"))
                else:
                    self.mute_button.setToolTip(self.language_manager.get_text("ui.notifications.mute_tooltip_off", default="Mute/Activate EVA voice"))
            if hasattr(self, 'file_button') and self.file_button:
                if current_lang == "es":
                    tooltip = "Seleccionar archivo para resumir (PDF, TXT, MD, CSV, JSON, DOCX, ODT)"
                else:
                    tooltip = "Select file to summarize (PDF, TXT, MD, CSV, JSON, DOCX, ODT)"
                self.file_button.setToolTip(tooltip)
            if hasattr(self, 'status_bar') and self.status_bar:
                for widget in self.status_bar.findChildren(QLabel):
                    text = widget.text()
                    if "Language" in text or "Idioma" in text:
                        widget.setText(self.language_manager.get_text("ui.language", default="Language") + ":")
                        break
            if hasattr(self, 'lang_combo') and self.lang_combo:
                self.lang_combo.blockSignals(True)
                index = self.lang_combo.findData(current_lang)
                if index >= 0:
                    self.lang_combo.setCurrentIndex(index)
                self.lang_combo.blockSignals(False)
            if hasattr(self, 'chat_history') and self.chat_history:
                contextual_greeting = self.get_contextual_greeting()
                eva_label = self.language_manager.get_text('responses.eva', default='EVA')
                self.chat_history.setHtml(
                    f"<div style='margin-bottom:15px;'><span style='color:#00bcd4; font-weight:600;'>{eva_label} [{datetime.now().strftime('%H:%M')}]:</span> <span style='color:#e0f7fa;'>{contextual_greeting}</span></div>"
                )
            self.repaint()
            logger.info(f"🌐 Chat window UI texts successfully updated to: {current_lang}")
        except Exception as e:
            logger.error(f"Error updating UI texts: {str(e)}")
            import traceback
            traceback.print_exc()

    def show_eva_info(self):
        try:
            from PySide6.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setWindowTitle("EVA - Asistente Personal")
            msg.setText("EVA - Asistente Personal\n\nTodas las funciones disponibles sin restricciones.")
            msg.exec()
        except Exception as e:
            import logging
            logging.getLogger('EVA').error(f"Error mostrando info EVA: {e}")

    def update_time_display(self):
        try:
            if hasattr(self, 'premium_btn') and self.premium_btn:
                self.premium_btn.setText("🤖 EVA")
                self.premium_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #1a73e8, stop:1 #0d47a1);
                        font-weight: 600;
                        border-radius: 8px;
                        padding: 8px 16px;
                        color: #ffffff;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #42a5f5, stop:1 #1565c0);
                    }
                """)
            if hasattr(self, 'time_label') and self.time_label:
                self.time_label.setText('<span style="color:#1a73e8; font-weight:bold;">EVA Activo</span>')
        except Exception as e:
            import logging
            logging.getLogger('EVA').error(f"Error en update_time_display: {str(e)}")
            try:
                if hasattr(self, 'time_label') and self.time_label:
                    self.time_label.setText("<span style='color:#666; font-weight:bold;'>Estado: Error</span>")
            except Exception:
                pass

    def open_settings(self):
        try:
            settings_dialog = SettingsWindow(self.config, self.language_manager, self)
            settings_dialog.finished.connect(
                lambda result: self.handle_settings_result(result, settings_dialog)
            )
            settings_dialog.exec()
        except Exception as e:
            logger.error(f"Error en open_settings: {str(e)}")
            self.add_message(f"{self.language_manager.get_text('responses.error')}: {str(e)}", is_user=False)

    def open_custom_commands(self):
        if self.controller.open_custom_commands():
            self.add_message(self.language_manager.get_text("responses.commands_updated"), is_user=False)
        else:
            self.add_message(self.language_manager.get_text("responses.commands_error"), is_user=False)

    def handle_settings_result(self, result, settings_dialog):
        if self.controller.handle_settings_result(result, settings_dialog):
            self.update_ui_texts()
            if "user_name" in settings_dialog.config:
                self.update_user_name(settings_dialog.config["user_name"])
            self.add_message(self.language_manager.get_text("responses.settings_updated"), is_user=False)

    def toggle_voice_listening(self):
        if not hasattr(self, 'voice_toggle_button'):
            return
        new_state = self.voice_toggle_button.isChecked()
        if not self.controller.toggle_voice_listening(new_state):
            self.voice_toggle_button.setChecked(not new_state)
            error_msg = "❌ Error: Motor de voz no disponible" if self.language_manager.current_lang == "es" else "❌ Error: Voice engine not available"
            self.add_message(error_msg, is_user=False)
            return
        if new_state:
            self.voice_toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(102, 255, 178, 0.3);
                    border: 1px solid rgba(102, 255, 178, 0.5);
                    font-weight: 600; border-radius: 6px; padding: 5px;
                }
                QPushButton:hover { background-color: rgba(102, 255, 178, 0.4);
                    border: 1px solid rgba(102, 255, 178, 0.7); }
            """)
            msg = "🎤 Reconocimiento de voz ACTIVADO - Ya puedes hablar" if self.language_manager.current_lang == "es" else "🎤 Voice recognition ENABLED - You can now speak"
            self.add_message(msg, is_user=False)
        else:
            self.voice_toggle_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(244, 67, 54, 0.3);
                    border: 1px solid rgba(244, 67, 54, 0.5);
                    font-weight: 600; border-radius: 6px; padding: 5px;
                }
                QPushButton:hover { background-color: rgba(244, 67, 54, 0.4);
                    border: 1px solid rgba(244, 67, 54, 0.7); }
            """)
            msg = "🎤 Reconocimiento de voz DESACTIVADO - Solo chat de texto" if self.language_manager.current_lang == "es" else "🎤 Voice recognition DISABLED - Text chat only"
            self.add_message(msg, is_user=False)
        # Sync mini bar voice state
        eva = getattr(getattr(self, 'command_processor', None), 'eva', None)
        if eva and getattr(eva, 'mini_bar', None):
            eva.mini_bar.sync_voice_state()

    def sync_voice_button_state(self):
        try:
            if not hasattr(self, 'voice_toggle_button'):
                return
            voice_engine = getattr(
                getattr(getattr(self, 'command_processor', None), 'eva', None),
                'voice_engine', None
            )
            if voice_engine is not None:
                current_state = voice_engine.is_listening
            else:
                current_state = self.config.get("auto_listen", False)
            self.voice_toggle_button.blockSignals(True)
            self.voice_toggle_button.setChecked(current_state)
            self.voice_toggle_button.blockSignals(False)
            if current_state:
                self.voice_toggle_button.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(102, 255, 178, 0.3);
                        border: 1px solid rgba(102, 255, 178, 0.5);
                        font-weight: 600;
                        border-radius: 6px;
                        padding: 5px;
                    }
                    QPushButton:hover {
                        background-color: rgba(102, 255, 178, 0.4);
                        border: 1px solid rgba(102, 255, 178, 0.7);
                    }
                    QPushButton:pressed {
                        background-color: rgba(102, 255, 178, 0.5);
                        border: 1px solid rgba(102, 255, 178, 0.8);
                    }
                """)
            else:
                self.voice_toggle_button.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(244, 67, 54, 0.3);
                        border: 1px solid rgba(244, 67, 54, 0.5);
                        font-weight: 600;
                        border-radius: 6px;
                        padding: 5px;
                    }
                    QPushButton:hover {
                        background-color: rgba(244, 67, 54, 0.4);
                        border: 1px solid rgba(244, 67, 54, 0.7);
                    }
                    QPushButton:pressed {
                        background-color: rgba(244, 67, 54, 0.5);
                        border: 1px solid rgba(244, 67, 54, 0.8);
                    }
                """)
            logger.info(f"🎤 Botón de voz sincronizado: {current_state}")
        except Exception as e:
            logger.error(f"Error sincronizando botón de voz: {str(e)}")

    def toggle_mute(self):
        is_muted = self.controller.toggle_mute()
        if is_muted:
            self.mute_button.setText("🔇")
            self.mute_button.setStyleSheet("""
                QPushButton { background-color: rgba(244, 67, 54, 0.3);
                    border: 1px solid rgba(244, 67, 54, 0.5);
                    font-weight: 600; font-size: 16px; border-radius: 6px; }
                QPushButton:hover { background-color: rgba(244, 67, 54, 0.4);
                    border: 1px solid rgba(244, 67, 54, 0.7); }
            """)
            self.mute_button.setToolTip(self.language_manager.get_text("ui.notifications.mute_tooltip_on"))
            self.add_message(self.language_manager.get_text("ui.notifications.voice_muted"), is_user=False)
        else:
            self.mute_button.setText("🔊")
            self.mute_button.setStyleSheet("""
                QPushButton { background-color: rgba(76, 175, 80, 0.3);
                    border: 1px solid rgba(76, 175, 80, 0.5);
                    font-weight: 600; font-size: 16px; border-radius: 6px; }
                QPushButton:hover { background-color: rgba(76, 175, 80, 0.4);
                    border: 1px solid rgba(76, 175, 80, 0.7); }
            """)
            self.mute_button.setToolTip(self.language_manager.get_text("ui.notifications.mute_tooltip_off"))
            self.add_message(self.language_manager.get_text("ui.notifications.voice_unmuted"), is_user=False)



    def select_and_process_file(self):
        try:
            file_filters = [
                "Todos los archivos soportados (*.pdf *.txt *.md *.csv *.json *.docx *.odt)",
                "Documentos PDF (*.pdf)", "Archivos de texto (*.txt *.md)",
                "Documentos Word (*.docx)", "Documentos OpenDocument (*.odt)",
                "Archivos de datos (*.csv *.json)", "Todos los archivos (*.*)",
            ]
            file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo para resumir", "", ";;".join(file_filters))
            if file_path:
                if not os.path.exists(file_path):
                    self.add_message("❌ Error: El archivo seleccionado no existe", is_user=False)
                    return
                ext = os.path.splitext(file_path)[1].lower()
                if ext not in self.supported_file_types:
                    self.add_message(f"❌ Formato no soportado: {ext}", is_user=False)
                    return
                self.add_message(f"📄 Archivo seleccionado: {os.path.basename(file_path)}", is_user=True)
                if not self.controller.process_selected_file(file_path):
                    self.add_message("❌ Error: Procesador de documentos no disponible", is_user=False)
        except Exception as e:
            logger.error(f"Error seleccionando archivo: {str(e)}")
            self.add_message(f"❌ Error seleccionando archivo: {str(e)}", is_user=False)

    def send_message(self):
        text = self.message_input.text().strip()
        if not text:
            return
        self.message_input.clear()
        self.controller.send_message(text)

    def show(self):
        super().show()
        self.fade_in()
        logger.info("Ventana mostrada")

    def showEvent(self, event):
        try:
            self.valid_paint_state = True
            self.pending_updates = False
            super().showEvent(event)
            QTimer.singleShot(50, self.safe_update)
            logger.info("Ventana mostrada")
        except Exception as e:
            logger.error(f"Error en showEvent: {str(e)}")

    def hideEvent(self, event):
        try:
            self.valid_paint_state = False
            super().hideEvent(event)
        except Exception as e:
            logger.error(f"Error en hideEvent: {str(e)}")

    def safe_update(self):
        try:
            if self.isVisible() and self.valid_paint_state:
                self.update()
                self.pending_updates = False
            else:
                self.pending_updates = True
        except Exception as e:
            logger.error(f"Error en safe_update: {str(e)}")

    def paintEvent(self, event):
        if not self.isVisible() or not self.valid_paint_state or self.is_painting:
            event.ignore()
            return
        try:
            self.is_painting = True
            painter = QPainter(self)
            if not painter.isActive():
                logger.warning("Painter no está activo, omitiendo pintura")
                return
            super().paintEvent(event)
            if hasattr(self, 'border_radius'):
                path = QPainterPath()
                path.addRoundedRect(self.rect(), self.border_radius, self.border_radius)
                painter.setClipPath(path)
            painter.end()
        except RuntimeError as e:
            if "wrapped C/C++ object" in str(e):
                logger.warning("Intento de pintura en objeto ya destruido")
            else:
                logger.error(f"Error en paintEvent: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado en paintEvent: {str(e)}")
        finally:
            self.is_painting = False

    def _add_file_info(self):
        try:
            if hasattr(self, 'language_manager') and self.language_manager:
                current_lang = getattr(self.language_manager, 'current_lang', 'es')
            else:
                current_lang = self.config.get('language', 'es')
            if current_lang == 'en':
                file_info = "📁 Document processing system activated. Use the 📁 button to select PDF, TXT, MD, CSV, JSON, DOCX, ODT files and automatically summarize them."
                system_label = "SYSTEM"
            else:
                file_info = "📁 Sistema de procesamiento de documentos activado. Usa el botón 📁 para seleccionar archivos PDF, TXT, MD, CSV, JSON, DOCX, ODT y resumirlos automáticamente."
                system_label = "SISTEMA"
            self.chat_history.append(
                f"<div style='margin-bottom:10px;'><span style='color:#4CAF50; font-weight:600;'>{system_label} [{datetime.now().strftime('%H:%M')}]:</span> <span style='color:#e0f7fa; font-size:12px;'>{file_info}</span></div>"
            )
            logger.info("Mensaje de procesamiento de archivos agregado al chat")
        except Exception as e:
            logger.error(f"Error agregando mensaje de archivos: {str(e)}")

    def toggle_mini_mode(self):
        """Toggle between full chat window and mini bar mode."""
        eva = getattr(getattr(self, 'command_processor', None), 'eva', None)
        if not eva:
            return
        mini = getattr(eva, 'mini_bar', None)
        if not mini:
            logger.warning("Mini bar not available")
            return
        self.config["use_mini_mode"] = True
        config_manager.save()
        self.hide()
        mini.show()
        mini.activateWindow()
        mini.raise_()
        QTimer.singleShot(100, mini.message_input.setFocus)

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            if self.isVisible():
                self.hide()
            event.accept()
        elif key == Qt.Key_Up and self.message_input.hasFocus():
            # Navigate up through chat history
            cursor = self.chat_history.textCursor()
            cursor.movePosition(QTextCursor.Up)
            self.chat_history.setTextCursor(cursor)
            event.accept()
        elif key == Qt.Key_Down and self.message_input.hasFocus():
            cursor = self.chat_history.textCursor()
            cursor.movePosition(QTextCursor.Down)
            self.chat_history.setTextCursor(cursor)
            event.accept()
        else:
            super().keyPressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        QTimer.singleShot(0, self.message_input.setFocus)

    def closeEvent(self, event):
        self.valid_paint_state = False
        self.save_config()
        event.accept()