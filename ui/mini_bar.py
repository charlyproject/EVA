import logging
import os

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPainterPath
from PySide6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from core.config_manager_unified import config_manager

logger = logging.getLogger("EVA")


class MiniBar(QWidget):
    """Compact always-on-top bar with input + mic button."""

    def __init__(self, config, language_manager, chat_window=None, command_processor=None):
        super().__init__()
        self.config = config
        self.language_manager = language_manager
        self.chat_window = chat_window
        self.command_processor = command_processor
        self._drag_pos = None
        self._is_collapsed = False

        self.setWindowTitle("EVA Mini")
        self.setObjectName("miniBar")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating, False)

        self.setWindowFlags(
            Qt.Window
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )

        self._build_ui()
        self._load_position()

    def _build_ui(self):
        self.setFixedHeight(56)
        self.setMinimumWidth(360)
        self.setMaximumWidth(480)

        container = QFrame()
        container.setObjectName("miniBarContainer")
        container.setStyleSheet("""
            #miniBarContainer {
                background-color: rgba(25, 25, 40, 0.95);
                border: 1px solid rgba(77, 182, 172, 0.5);
                border-radius: 8px;
            }
        """)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self.drag_handle = QLabel("⠿")
        self.drag_handle.setFixedWidth(24)
        self.drag_handle.setAlignment(Qt.AlignCenter)
        self.drag_handle.setStyleSheet("color: #4db6ac; font-size: 18px; padding: 0;")
        layout.addWidget(self.drag_handle)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText(
            self.language_manager.get_text("ui.type_message") or "Type here..."
        )
        self.message_input.setFixedHeight(36)
        self.message_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(30, 30, 45, 0.8);
                border: 1px solid rgba(77, 182, 172, 0.4);
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                color: #e0f7fa;
            }
            QLineEdit:focus {
                border: 1px solid #00bcd4;
            }
        """)
        self.message_input.returnPressed.connect(self._send_message)
        layout.addWidget(self.message_input, 1)

        self.expand_button = QPushButton("⤢")
        self.expand_button.setFixedSize(28, 34)
        self.expand_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #4db6ac;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover { color: #00bcd4; }
        """)
        self.expand_button.clicked.connect(self._expand_to_full)
        self.expand_button.setToolTip("Expand to full window")
        layout.addWidget(self.expand_button)

        # --- Collapse / Minimize button ---
        self.collapse_button = QPushButton("▬")
        self.collapse_button.setFixedSize(24, 34)
        self.collapse_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #ffb74d;
                font-size: 13px;
            }
            QPushButton:hover { color: #ffa726; }
        """)
        self.collapse_button.clicked.connect(self._toggle_collapse)
        self.collapse_button.setToolTip("Minimize bar")
        layout.addWidget(self.collapse_button)

        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(24, 34)
        self.close_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #ef5350;
                font-size: 14px;
            }
            QPushButton:hover { color: #ff1744; }
        """)
        self.close_button.clicked.connect(self._minimize_bar)
        self.close_button.setToolTip("Minimize to tray")
        layout.addWidget(self.close_button)

        self.voice_button = QPushButton()
        self.voice_button.setFixedSize(34, 34)
        self.voice_button.setCheckable(True)
        self.voice_button.setChecked(self.config.get("auto_listen", False))
        self._update_voice_style(self.config.get("auto_listen", False))
        self.voice_button.clicked.connect(self._toggle_voice)
        self._try_load_mic_icon()
        self.voice_button.setToolTip(self.language_manager.get_text("ui.voice_toggle_tooltip", default="Toggle voice"))
        layout.addWidget(self.voice_button)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(4, 4, 4, 4)
        outer.addWidget(container)

    def _try_load_mic_icon(self):
        try:
            svg = os.path.join("resources", "icons", "microphone.svg")
            png = os.path.join("resources", "microphone.png")
            if os.path.exists(svg):
                self.voice_button.setIcon(QIcon(svg))
                self.voice_button.setIconSize(self.voice_button.size())
            elif os.path.exists(png):
                pm = QPixmap(png).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.voice_button.setIcon(QIcon(pm))
                self.voice_button.setIconSize(pm.size())
            else:
                self.voice_button.setText("🎤")
        except Exception:
            self.voice_button.setText("🎤")

    def _update_voice_style(self, active):
        if active:
            self.voice_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(102, 255, 178, 0.3);
                    border: 1px solid rgba(102, 255, 178, 0.5);
                    border-radius: 6px;
                }
                QPushButton:hover { background-color: rgba(102, 255, 178, 0.4); }
            """)
        else:
            self.voice_button.setStyleSheet("""
                QPushButton {
                    background-color: rgba(244, 67, 54, 0.3);
                    border: 1px solid rgba(244, 67, 54, 0.5);
                    border-radius: 6px;
                }
                QPushButton:hover { background-color: rgba(244, 67, 54, 0.4); }
            """)

    def _toggle_voice(self):
        new_state = self.voice_button.isChecked()
        if not hasattr(self, 'command_processor') or not self.command_processor:
            self.voice_button.setChecked(not new_state)
            return
        eva = getattr(self.command_processor, 'eva', None)
        if eva and hasattr(eva, 'voice_engine') and eva.voice_engine:
            try:
                if new_state:
                    eva.voice_engine.start()
                else:
                    eva.voice_engine.stop()
                self.config["auto_listen"] = new_state
                config_manager.save()
            except Exception as e:
                logger.error(f"MiniBar voice toggle error: {e}")
                self.voice_button.setChecked(not new_state)
                return
        else:
            self.voice_button.setChecked(not new_state)
            return
        self._update_voice_style(new_state)
        if self.chat_window and hasattr(self.chat_window, 'sync_voice_button_state'):
            self.chat_window.sync_voice_button_state()

    def _send_message(self):
        text = self.message_input.text().strip()
        if not text:
            return
        self.message_input.clear()
        if self.command_processor and self.chat_window:
            self.chat_window.add_message(text, is_user=True)
            self.command_processor.process_command(text, self.chat_window)
        elif self.chat_window:
            self.chat_window.add_message(text, is_user=True)

    def _expand_to_full(self):
        if self.chat_window:
            self.config["use_mini_mode"] = False
            config_manager.save()
            self.chat_window.show()
            self.chat_window.activateWindow()
            self.chat_window.raise_()
            QTimer.singleShot(100, lambda: self.chat_window.message_input.setFocus() if hasattr(self.chat_window, 'message_input') else None)
            self.hide()

    def _minimize_bar(self):
        self.hide()

    def _toggle_collapse(self):
        """Collapse the bar to a tiny pill or restore it."""
        if self._is_collapsed:
            self._restore_bar()
        else:
            self._collapse_bar()

    def _collapse_bar(self):
        """Shrink bar to a small pill showing only drag handle + restore button."""
        self._is_collapsed = True
        # Hide all widgets except drag handle
        self.message_input.hide()
        self.expand_button.hide()
        self.voice_button.hide()
        self.close_button.hide()
        # Change collapse button to restore icon
        self.collapse_button.setText("◻")
        self.collapse_button.setToolTip("Restore bar")
        # Shrink width
        self._pre_collapse_width = self.width()
        self.setMinimumWidth(80)
        self.setMaximumWidth(80)
        self.resize(80, 56)

    def _restore_bar(self):
        """Restore the bar to full size."""
        self._is_collapsed = False
        # Restore width limits
        self.setMinimumWidth(480)
        self.setMaximumWidth(1000)
        w = getattr(self, '_pre_collapse_width', 480)
        self.resize(w, 56)
        # Show all widgets
        self.message_input.show()
        self.expand_button.show()
        self.voice_button.show()
        self.close_button.show()
        # Restore collapse button
        self.collapse_button.setText("▬")
        self.collapse_button.setToolTip("Minimize bar")
        QTimer.singleShot(50, self.message_input.setFocus)

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.raise_()
            self.message_input.setFocus()

    def _load_position(self):
        pos = self.config.get("mini_bar_position", None)
        if pos and len(pos) == 2:
            self.move(pos[0], pos[1])
        else:
            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.availableGeometry()
                self.move(geo.width() - 420, geo.height() - 80)

    def save_position(self):
        if self.isVisible():
            self.config["mini_bar_position"] = [self.x(), self.y()]
            config_manager.save()

    def showEvent(self, event):
        super().showEvent(event)
        self.sync_voice_state()
        QTimer.singleShot(50, self.message_input.setFocus)

    def hideEvent(self, event):
        self.save_position()
        super().hideEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not painter.isActive():
            return
        path = QPainterPath()
        path.addRoundedRect(self.rect(), 10, 10)
        painter.setClipPath(path)
        super().paintEvent(event)
        painter.end()

    def sync_voice_state(self):
        if not hasattr(self, 'voice_button'):
            return
        eva = getattr(getattr(self, 'command_processor', None), 'eva', None)
        if eva and hasattr(eva, 'voice_engine') and eva.voice_engine:
            state = eva.voice_engine.is_listening
        else:
            state = self.config.get("auto_listen", False)
        self.voice_button.blockSignals(True)
        self.voice_button.setChecked(state)
        self.voice_button.blockSignals(False)
        self._update_voice_style(state)
