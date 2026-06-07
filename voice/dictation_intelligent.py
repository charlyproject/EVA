"""
Enhanced Voice Assistant - Intelligent Dictation Module
Professional dictation feature with real-time speech recognition, grammar correction, and GUI interface.

Features:
- Real-time speech recognition using EVA's existing Vosk integration
- Streaming microphone input with stop commands and timeout
- Automatic grammar and spelling correction using language_tool_python
- Minimal PySide6 GUI for text preview and editing
- Voice/GUI commands for paste, save, or cancel operations
- Integration with EVA's TTS system for vocal feedback
- Support for Spanish and English with language detection
- Robust error handling and fully offline operation
- Memory-efficient streaming transcription
- Safe clipboard handling with restoration

Author: EVA Assistant Team
Version: 1.0
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any

import pyaudio
import pyperclip
from PySide6.QtCore import QObject, Signal, QTimer, Qt, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QProgressBar, QMessageBox, QApplication
)
from PySide6.QtGui import QFont, QKeySequence, QShortcut

from core.audio_lock import audio_lock
from vosk import KaldiRecognizer, Model

# Import language_tool_python for grammar correction
try:
    import language_tool_python
    LANGUAGE_TOOL_AVAILABLE = True
except ImportError:
    LANGUAGE_TOOL_AVAILABLE = False
    logging.warning("language_tool_python not available. Install with: pip install language-tool-python")

# Import hotkey system
try:
    from .dictation_hotkey import setup_dictation_hotkey, stop_dictation_hotkey, is_hotkey_available
    HOTKEY_AVAILABLE = True
except ImportError:
    HOTKEY_AVAILABLE = False
    logging.warning("Hotkey system not available")

logger = logging.getLogger("EVA")


class DictationWorker(QThread):
    """Worker thread for handling speech recognition and processing"""
    
    # Signals for communication with main thread
    text_recognized = Signal(str)
    status_changed = Signal(str)
    error_occurred = Signal(str)
    recording_finished = Signal()
    
    def __init__(self, model_path: str, language: str = "es", timeout: int = 30):
        super().__init__()
        self.model_path = model_path
        self.language = language
        self.timeout = timeout
        self.is_recording = False
        self.should_stop = False
        
        # Audio configuration
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.audio = None
        self.stream = None
        self.model = None
        self.recognizer = None
        
        # Accumulated text
        self.accumulated_text = ""
        
    def run(self):
        """Main worker thread execution"""
        try:
            self._initialize_audio()
            self._initialize_vosk()
            self._start_recording()
        except Exception as e:
            logger.error(f"Error in dictation worker: {str(e)}")
            self.error_occurred.emit(f"Error en reconocimiento: {str(e)}")
        finally:
            self._cleanup()
    
    def _initialize_audio(self):
        """Initialize PyAudio for microphone input"""
        try:
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            logger.info("Audio initialized successfully")
        except Exception as e:
            raise Exception(f"Error inicializando audio: {str(e)}")
    
    def _initialize_vosk(self):
        """Initialize Vosk model for speech recognition"""
        try:
            if not os.path.exists(self.model_path):
                raise Exception(f"Modelo Vosk no encontrado: {self.model_path}")
            
            self.model = Model(self.model_path)
            self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
            logger.info(f"Vosk model loaded: {self.model_path}")
        except Exception as e:
            raise Exception(f"Error cargando modelo Vosk: {str(e)}")
    
    def _start_recording(self):
        """Start recording and processing audio stream"""
        self.is_recording = True
        self.status_changed.emit("Escuchando... (di 'parar dictado' para finalizar)")
        
        start_time = time.time()
        silence_start = None
        
        # Adaptive silence detection
        base_silence_threshold = 3.0
        silence_threshold = base_silence_threshold
        speech_detected_count = 0
        last_speech_time = start_time
        
        try:
            while self.is_recording and not self.should_stop:
                # Check timeout
                if time.time() - start_time > self.timeout:
                    self.status_changed.emit("Tiempo límite alcanzado")
                    break
                
                # Read audio data
                try:
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                except Exception as e:
                    logger.warning(f"Audio read error: {str(e)}")
                    continue
                
                # Process audio with Vosk
                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").strip()
                    confidence = result.get("confidence", 0.0)  # Get confidence score
                    
                    if text:
                        # Check for stop commands
                        if self._is_stop_command(text):
                            self.status_changed.emit("Comando de parada detectado")
                            break
                        
                        # Check for voice commands during dictation
                        is_command, command_type, remaining_text = self._is_voice_command(text)
                        
                        if is_command:
                            # Process voice command
                            self.text_recognized.emit(f"COMMAND:{command_type}")
                            # Add remaining text if any
                            if remaining_text:
                                self.accumulated_text += remaining_text + " "
                                self.text_recognized.emit(f"CONFIDENCE:{confidence}:{remaining_text}")
                        else:
                            # Add recognized text with confidence
                            self.accumulated_text += text + " "
                            self.text_recognized.emit(f"CONFIDENCE:{confidence}:{text}")
                        
                        # Update adaptive silence detection
                        speech_detected_count += 1
                        last_speech_time = time.time()
                        silence_start = None  # Reset silence timer
                        
                        # Adjust silence threshold based on speech pattern
                        if speech_detected_count > 5:  # After some speech detected
                            # If user speaks frequently, reduce silence threshold
                            avg_speech_interval = (time.time() - start_time) / speech_detected_count
                            if avg_speech_interval < 2.0:  # Fast speaker
                                silence_threshold = 2.0
                            elif avg_speech_interval > 5.0:  # Slow speaker
                                silence_threshold = 5.0
                            else:
                                silence_threshold = base_silence_threshold
                    else:
                        # Track silence for auto-stop
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > silence_threshold:
                            if self.accumulated_text.strip():  # Only stop if we have some text
                                self.status_changed.emit("Pausa detectada - finalizando dictado")
                                break
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Error during recording: {str(e)}")
            self.error_occurred.emit(f"Error durante grabación: {str(e)}")
        
        finally:
            self.is_recording = False
            self.recording_finished.emit()
    
    def _is_stop_command(self, text: str) -> bool:
        """Check if the recognized text contains a stop command"""
        stop_commands = [
            # Spanish
            "parar dictado", "para dictado", "detener dictado", "finalizar dictado",
            "stop dictado", "terminar dictado", "acabar dictado",
            # English
            "stop dictation", "end dictation", "finish dictation", "quit dictation"
        ]
        
        text_lower = text.lower().strip()
        return any(cmd in text_lower for cmd in stop_commands)
    
    def _is_voice_command(self, text: str) -> tuple[bool, str, str]:
        """
        Check if the recognized text contains a voice command during dictation
        
        Returns:
            tuple: (is_command, command_type, processed_text)
        """
        text_lower = text.lower().strip()
        
        # Comandos de formato
        line_commands = [
            "nueva línea", "nueva linea", "new line", "salto de línea", "salto de linea"
        ]
        paragraph_commands = [
            "nuevo párrafo", "nuevo parrafo", "new paragraph", "párrafo nuevo", "parrafo nuevo"
        ]
        delete_commands = [
            "borrar última palabra", "borrar ultima palabra", "delete last word",
            "eliminar última palabra", "eliminar ultima palabra"
        ]
        punctuation_commands = {
            "punto": ".",
            "coma": ",",
            "punto y coma": ";",
            "dos puntos": ":",
            "signo de pregunta": "?",
            "signo de exclamación": "!",
            "question mark": "?",
            "exclamation mark": "!",
            "period": ".",
            "comma": ","
        }
        
        # Verificar comandos de línea
        for cmd in line_commands:
            if cmd in text_lower:
                return True, "new_line", text_lower.replace(cmd, "").strip()
        
        # Verificar comandos de párrafo
        for cmd in paragraph_commands:
            if cmd in text_lower:
                return True, "new_paragraph", text_lower.replace(cmd, "").strip()
        
        # Verificar comandos de borrado
        for cmd in delete_commands:
            if cmd in text_lower:
                return True, "delete_last_word", text_lower.replace(cmd, "").strip()
        
        # Verificar comandos de puntuación
        for cmd, punctuation in punctuation_commands.items():
            if cmd in text_lower:
                remaining_text = text_lower.replace(cmd, "").strip()
                return True, f"add_punctuation:{punctuation}", remaining_text
        
        return False, "", text
    
    def stop_recording(self):
        """Stop the recording process"""
        self.should_stop = True
        self.is_recording = False
    
    def _cleanup(self):
        """Clean up audio resources"""
        try:
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
            if self.audio:
                self.audio.terminate()
        except Exception as e:
            logger.warning(f"Cleanup error: {str(e)}")


class GrammarCorrector:
    """Grammar and spelling correction using language_tool_python"""
    
    def __init__(self, language: str = "es"):
        self.language = language
        self.tool = None
        self._initialize_tool()
    
    def _initialize_tool(self):
        """Initialize language tool for grammar correction"""
        if not LANGUAGE_TOOL_AVAILABLE:
            logger.warning("Language tool not available - grammar correction disabled")
            return
        
        try:
            # Map language codes
            lang_map = {
                "es": "es",
                "en": "en-US"
            }
            
            lang_code = lang_map.get(self.language, "es")
            self.tool = language_tool_python.LanguageTool(lang_code)
            logger.info(f"Grammar correction initialized for {lang_code}")
            
        except Exception as e:
            logger.error(f"Error initializing grammar tool: {str(e)}")
            if "java" in str(e).lower():
                logger.warning("Java not detected - grammar correction will be disabled")
                logger.info("To enable grammar correction, install Java from: https://www.java.com/download/")
            self.tool = None
    
    def correct_text(self, text: str) -> str:
        """Correct grammar and spelling in the given text"""
        if not self.tool or not text.strip():
            return text
        
        try:
            # Get corrections
            matches = self.tool.check(text)
            
            # Apply corrections in reverse order to maintain positions
            corrected_text = text
            for match in reversed(matches):
                if match.replacements:
                    # Use the first suggested replacement
                    replacement = match.replacements[0]
                    start = match.offset
                    end = match.offset + match.errorLength
                    corrected_text = corrected_text[:start] + replacement + corrected_text[end:]
            
            return corrected_text
            
        except Exception as e:
            logger.error(f"Error correcting text: {str(e)}")
            return text
    
    def close(self):
        """Close the language tool"""
        if self.tool:
            try:
                self.tool.close()
            except Exception:
                pass


class DictationGUI(QWidget):
    """Minimal GUI for dictation preview and control"""
    
    # Signals
    paste_requested = Signal(str)
    save_requested = Signal(str)
    cancel_requested = Signal()
    
    def __init__(self, language: str = "es"):
        super().__init__()
        self.language = language
        self.original_clipboard = ""
        self.setup_ui()
        self.setup_shortcuts()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("EVA - Dictado Inteligente")
        self.setGeometry(100, 100, 600, 400)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel("Iniciando dictado...")
        self.status_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.status_label)
        
        # Audio level indicator
        self.audio_level_bar = QProgressBar()
        self.audio_level_bar.setMaximum(100)
        self.audio_level_bar.setValue(0)
        self.audio_level_bar.setTextVisible(False)
        self.audio_level_bar.setMaximumHeight(10)
        self.audio_level_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid grey;
                border-radius: 5px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 4px;
            }
        """)
        layout.addWidget(QLabel("Nivel de audio:"))
        layout.addWidget(self.audio_level_bar)
        
        # Word count label
        self.word_count_label = QLabel("Palabras: 0 | Caracteres: 0")
        self.word_count_label.setFont(QFont("Arial", 8))
        self.word_count_label.setStyleSheet("color: gray;")
        layout.addWidget(self.word_count_label)
        
        # Text preview area
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Arial", 12))
        self.text_edit.setPlaceholderText("El texto dictado aparecerá aquí...")
        layout.addWidget(self.text_edit)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Paste button
        self.paste_button = QPushButton("📋 Pegar (Ctrl+V)")
        self.paste_button.clicked.connect(self.on_paste_clicked)
        self.paste_button.setEnabled(False)
        button_layout.addWidget(self.paste_button)
        
        # Save button
        self.save_button = QPushButton("💾 Guardar (Ctrl+S)")
        self.save_button.clicked.connect(self.on_save_clicked)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)
        
        # Cancel button
        self.cancel_button = QPushButton("❌ Cancelar (Esc)")
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Info label with commands
        info_text = ("Comandos de voz: 'nueva línea', 'nuevo párrafo', 'punto', 'coma', 'borrar última palabra'\n"
                    "Tip: Puedes editar el texto antes de pegar o guardar")
        self.info_label = QLabel(info_text)
        self.info_label.setFont(QFont("Arial", 8))
        self.info_label.setStyleSheet("color: gray;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # State tracking
        self.is_paused = False
        
        self.setLayout(layout)
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts"""
        # Paste shortcut
        paste_shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
        paste_shortcut.activated.connect(self.on_paste_clicked)
        
        # Save shortcut
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.on_save_clicked)
        
        # Cancel shortcut
        cancel_shortcut = QShortcut(QKeySequence("Escape"), self)
        cancel_shortcut.activated.connect(self.on_cancel_clicked)
    
    def update_status(self, status: str):
        """Update the status label"""
        self.status_label.setText(status)
    
    def append_text(self, text: str):
        """Append recognized text to the preview"""
        current_text = self.text_edit.toPlainText()
        if current_text:
            self.text_edit.setPlainText(current_text + " " + text)
        else:
            self.text_edit.setPlainText(text)
        
        # Enable buttons when we have text
        self.paste_button.setEnabled(True)
        self.save_button.setEnabled(True)
        
        # Update word count
        self.update_word_count()
    
    def append_text_with_confidence(self, text: str, confidence: float):
        """Append recognized text with confidence styling"""
        from PySide6.QtGui import QTextCharFormat, QColor
        
        cursor = self.text_edit.textCursor()
        cursor.movePosition(cursor.End)
        
        # Create format based on confidence
        format = QTextCharFormat()
        if confidence < 0.3:
            # Low confidence - red background
            format.setBackground(QColor(255, 200, 200))
            format.setToolTip(f"Baja confianza: {confidence:.2f}")
        elif confidence < 0.6:
            # Medium confidence - yellow background
            format.setBackground(QColor(255, 255, 200))
            format.setToolTip(f"Confianza media: {confidence:.2f}")
        else:
            # High confidence - normal
            format.setBackground(QColor(255, 255, 255))
            format.setToolTip(f"Alta confianza: {confidence:.2f}")
        
        # Add space if needed
        current_text = self.text_edit.toPlainText()
        if current_text and not current_text.endswith(" "):
            cursor.insertText(" ")
        
        # Insert text with formatting
        cursor.insertText(text, format)
        
        # Enable buttons when we have text
        self.paste_button.setEnabled(True)
        self.save_button.setEnabled(True)
        
        # Update word count
        self.update_word_count()
    
    def set_corrected_text(self, text: str):
        """Set the corrected text in the preview"""
        self.text_edit.setPlainText(text)
        self.paste_button.setEnabled(bool(text.strip()))
        self.save_button.setEnabled(bool(text.strip()))
    
    def get_text(self) -> str:
        """Get the current text from the preview"""
        return self.text_edit.toPlainText()
    
    def on_paste_clicked(self):
        """Handle paste button click"""
        text = self.get_text().strip()
        if text:
            self.paste_requested.emit(text)
    
    def on_save_clicked(self):
        """Handle save button click"""
        text = self.get_text().strip()
        if text:
            self.save_requested.emit(text)
    
    def on_pause_clicked(self):
        """Handle pause/resume button click"""
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.setText("▶️ Reanudar")
            self.update_status("Dictado pausado - presiona Reanudar para continuar")
        else:
            self.pause_button.setText("⏸️ Pausar")
            self.update_status("Dictado reanudado - continúa hablando")
    
    def on_cancel_clicked(self):
        """Handle cancel button click"""
        self.cancel_requested.emit()
    
    def update_word_count(self):
        """Update word and character count"""
        text = self.get_text()
        word_count = len(text.split()) if text.strip() else 0
        char_count = len(text)
        self.word_count_label.setText(f"Palabras: {word_count} | Caracteres: {char_count}")
    
    def update_audio_level(self, level: int):
        """Update audio level indicator (0-100)"""
        self.audio_level_bar.setValue(min(100, max(0, level)))
    
    def show_error(self, message: str):
        """Show error message"""
        QMessageBox.critical(self, "Error", message)
    
    def show_success(self, message: str):
        """Show success message"""
        QMessageBox.information(self, "Éxito", message)
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.cancel_requested.emit()
        event.accept()


class IntelligentDictation(QObject):
    """Main dictation controller class"""
    
    def __init__(self, config: Dict[str, Any], eva_instance=None):
        super().__init__()
        self.config = config
        self.eva = eva_instance
        self.language = config.get("language", "es")
        
        # Components
        self.worker = None
        self.gui = None
        self.corrector = None
        
        # State
        self.is_active = False
        self.original_clipboard = ""
        
        # Dictation history and recovery
        self.dictation_history = []
        self.auto_save_timer = None
        self.current_draft_file = None
        
        # Global hotkey setup
        self.hotkey_enabled = config.get("dictation", {}).get("global_hotkey", True)
        self.hotkey_combination = config.get("dictation", {}).get("hotkey", "ctrl+shift+d")
        
        # Get model path from EVA's voice engine
        self.model_path = self._get_model_path()
        
        # Setup global hotkey if enabled
        if self.hotkey_enabled and HOTKEY_AVAILABLE:
            self._setup_global_hotkey()
        
    def _get_model_path(self) -> str:
        """Get the appropriate Vosk model path based on language"""
        base_path = "models/vosk"
        
        model_paths = {
            "es": os.path.join(base_path, "vosk-model-small-es-0.42"),
            "en": os.path.join(base_path, "vosk-model-small-en-us-0.15")
        }
        
        model_path = model_paths.get(self.language, model_paths["es"])
        
        # Verify model exists
        if not os.path.exists(model_path):
            # Try alternative paths or use EVA's existing model detection
            if self.eva and hasattr(self.eva, 'voice_engine'):
                try:
                    return self.eva.voice_engine.model_path
                except Exception:
                    pass
            
            # Fallback to first available model
            for lang, path in model_paths.items():
                if os.path.exists(path):
                    logger.warning(f"Using {lang} model as fallback: {path}")
                    return path
            
            raise Exception("No se encontró ningún modelo Vosk disponible")
        
        return model_path
    
    def start_dictation(self) -> bool:
        """
        Start the intelligent dictation process
        
        Returns:
            bool: True if dictation started successfully, False otherwise
        """
        if self.is_active:
            logger.warning("Dictation already active")
            return False

        # Intentar adquirir AudioLock (evita conflicto con VoiceEngine)
        if not audio_lock.acquire("dictation"):
            logger.warning("AudioLock en uso - no se puede iniciar dictado")
            if self.gui:
                self.gui.show_error("El micrófono está en uso. Detén la escucha de voz antes de dictar.")
            return False

        # Pausar procesamiento de comandos de voz mientras dure el dictado
        if (self.eva and
            hasattr(self.eva, 'voice_engine') and
            hasattr(self.eva.voice_engine, 'pause_command_processing')):
            self.eva.voice_engine.pause_command_processing = True
            logger.info("Procesamiento de comandos pausado durante dictado")

        try:
            # Save original clipboard content
            self._save_clipboard()
            
            # Initialize grammar corrector
            self.corrector = GrammarCorrector(self.language)
            
            # Create and show GUI
            self.gui = DictationGUI(self.language)
            self.gui.paste_requested.connect(self._handle_paste)
            self.gui.save_requested.connect(self._handle_save)
            self.gui.cancel_requested.connect(self._handle_cancel)
            
            # Load any existing draft
            self._load_last_draft()
            
            self.gui.show()
            
            # Start auto-save timer
            self._start_auto_save()
            
            # Create and start worker thread
            self.worker = DictationWorker(self.model_path, self.language)
            self.worker.text_recognized.connect(self._on_text_recognized)
            self.worker.status_changed.connect(self._on_status_changed)
            self.worker.error_occurred.connect(self._on_error)
            self.worker.recording_finished.connect(self._on_recording_finished)
            self.worker.start()
            
            self.is_active = True
            
            # Provide vocal feedback if TTS is available
            self._speak("Dictado iniciado. Comienza a hablar.")
            
            logger.info("Intelligent dictation started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting dictation: {str(e)}")
            self._cleanup()
            if self.gui:
                self.gui.show_error(f"Error iniciando dictado: {str(e)}")
            return False
    
    def stop_dictation(self):
        """Stop the dictation process"""
        if not self.is_active:
            return
        
        try:
            if self.worker:
                self.worker.stop_recording()
                self.worker.wait(5000)  # Wait up to 5 seconds
            
            self._cleanup()
            logger.info("Dictation stopped")
            
        except Exception as e:
            logger.error(f"Error stopping dictation: {str(e)}")
    
    def _save_clipboard(self):
        """Save current clipboard content"""
        try:
            self.original_clipboard = pyperclip.paste()
        except Exception as e:
            logger.warning(f"Could not save clipboard: {str(e)}")
            self.original_clipboard = ""
    
    def _restore_clipboard(self):
        """Restore original clipboard content"""
        try:
            if self.original_clipboard:
                pyperclip.copy(self.original_clipboard)
        except Exception as e:
            logger.warning(f"Could not restore clipboard: {str(e)}")
    
    def _on_text_recognized(self, text: str):
        """Handle recognized text from worker"""
        if self.gui:
            # Check if it's a voice command
            if text.startswith("COMMAND:"):
                command_type = text.replace("COMMAND:", "")
                self._process_voice_command(command_type)
            elif text.startswith("CONFIDENCE:"):
                # Parse confidence and text
                parts = text.split(":", 2)
                if len(parts) == 3:
                    confidence = float(parts[1])
                    actual_text = parts[2]
                    self.gui.append_text_with_confidence(actual_text, confidence)
                else:
                    self.gui.append_text(text)
            else:
                self.gui.append_text(text)
    
    def _process_voice_command(self, command_type: str):
        """Process voice commands during dictation"""
        if not self.gui:
            return
        
        current_text = self.gui.get_text()
        
        if command_type == "new_line":
            self.gui.text_edit.setPlainText(current_text + "\n")
            self._speak("Nueva línea")
            
        elif command_type == "new_paragraph":
            self.gui.text_edit.setPlainText(current_text + "\n\n")
            self._speak("Nuevo párrafo")
            
        elif command_type == "delete_last_word":
            words = current_text.strip().split()
            if words:
                words.pop()  # Remove last word
                new_text = " ".join(words)
                if new_text:
                    new_text += " "  # Add space for next word
                self.gui.text_edit.setPlainText(new_text)
                self._speak("Palabra borrada")
            else:
                self._speak("No hay palabras para borrar")
                
        elif command_type.startswith("add_punctuation:"):
            punctuation = command_type.split(":", 1)[1]
            # Remove trailing space and add punctuation
            trimmed_text = current_text.rstrip()
            self.gui.text_edit.setPlainText(trimmed_text + punctuation + " ")
            self._speak("Puntuación agregada")
    
    def _on_status_changed(self, status: str):
        """Handle status updates from worker"""
        if self.gui:
            self.gui.update_status(status)
    
    def _on_error(self, error: str):
        """Handle errors from worker"""
        logger.error(f"Dictation error: {error}")
        if self.gui:
            self.gui.show_error(error)
        self._cleanup()
    
    def _on_recording_finished(self):
        """Handle recording completion"""
        if not self.gui:
            return
        
        # Get accumulated text
        raw_text = self.gui.get_text().strip()
        
        if not raw_text:
            self.gui.update_status("No se detectó texto. Puedes intentar de nuevo.")
            self._speak("No se detectó texto en el dictado.")
            return
        
        # Apply grammar correction
        self.gui.update_status("Corrigiendo gramática y ortografía...")
        
        try:
            corrected_text = self.corrector.correct_text(raw_text)
            self.gui.set_corrected_text(corrected_text)
            
            # Show completion status
            word_count = len(corrected_text.split())
            self.gui.update_status(f"Dictado completado - {word_count} palabras. Elige una acción.")
            
            # Provide vocal feedback
            self._speak(f"Dictado completado con {word_count} palabras. Puedes pegar, guardar o cancelar.")
            
        except Exception as e:
            logger.error(f"Error in text correction: {str(e)}")
            self.gui.set_corrected_text(raw_text)
            self.gui.update_status("Dictado completado (sin corrección). Elige una acción.")
            self._speak("Dictado completado. Puedes pegar, guardar o cancelar.")
    
    def _handle_paste(self, text: str):
        """Handle paste request"""
        try:
            # Copy text to clipboard
            pyperclip.copy(text)
            
            # Simulate Ctrl+V to paste
            import pyautogui
            time.sleep(0.5)  # Small delay to ensure clipboard is ready
            pyautogui.hotkey('ctrl', 'v')
            
            # Provide feedback
            self._speak("Texto pegado correctamente.")
            if self.gui:
                self.gui.show_success("Texto pegado en la aplicación activa")
            
            # Restore original clipboard after a delay
            QTimer.singleShot(2000, self._restore_clipboard)
            
            # Close dictation
            self._cleanup()
            
        except Exception as e:
            logger.error(f"Error pasting text: {str(e)}")
            if self.gui:
                self.gui.show_error(f"Error pegando texto: {str(e)}")
    
    def _handle_save(self, text: str):
        """Handle save request"""
        try:
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dictado_{timestamp}.txt"
            
            # Save to user's Documents folder or current directory
            documents_path = os.path.expanduser("~/Documents")
            if os.path.exists(documents_path):
                filepath = os.path.join(documents_path, filename)
            else:
                filepath = filename
            
            # Write text to file (append mode as requested)
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(f"\n--- Dictado {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
                f.write(text)
                f.write("\n" + "="*50 + "\n")
            
            # Save to history
            self._save_to_history(text)
            
            # Clean up draft
            self._cleanup_draft()
            
            # Provide feedback
            self._speak(f"Texto guardado en {filename}")
            if self.gui:
                self.gui.show_success(f"Texto guardado en:\n{filepath}")
            
            # Close dictation
            self._cleanup()
            
        except Exception as e:
            logger.error(f"Error saving text: {str(e)}")
            if self.gui:
                self.gui.show_error(f"Error guardando texto: {str(e)}")
    
    def _handle_cancel(self):
        """Handle cancel request"""
        self._speak("Dictado cancelado.")
        self._cleanup()
    
    def _speak(self, text: str):
        """Provide vocal feedback using EVA's TTS system"""
        try:
            if (self.eva and 
                hasattr(self.eva, 'speech_synthesizer') and 
                self.eva.speech_synthesizer and
                self.config.get('tts', {}).get('enabled', True)):
                
                # Use EVA's TTS system
                self.eva.speech_synthesizer.speak(text)
            
        except Exception as e:
            logger.warning(f"Could not provide vocal feedback: {str(e)}")
    
    def _start_auto_save(self):
        """Start auto-save timer for draft recovery"""
        if self.auto_save_timer:
            self.auto_save_timer.stop()
        
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save_draft)
        self.auto_save_timer.start(10000)  # Auto-save every 10 seconds
    
    def _auto_save_draft(self):
        """Auto-save current dictation as draft"""
        if not self.gui:
            return
        
        text = self.gui.get_text().strip()
        if not text:
            return
        
        try:
            # Create drafts directory
            drafts_dir = os.path.expanduser("~/Documents/EVA_Dictation_Drafts")
            os.makedirs(drafts_dir, exist_ok=True)
            
            # Save current draft
            if not self.current_draft_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.current_draft_file = os.path.join(drafts_dir, f"draft_{timestamp}.txt")
            
            with open(self.current_draft_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            logger.debug(f"Draft auto-saved: {self.current_draft_file}")
            
        except Exception as e:
            logger.error(f"Error auto-saving draft: {str(e)}")
    
    def _load_last_draft(self):
        """Load the most recent draft if available"""
        try:
            drafts_dir = os.path.expanduser("~/Documents/EVA_Dictation_Drafts")
            if not os.path.exists(drafts_dir):
                return
            
            # Find most recent draft
            draft_files = [f for f in os.listdir(drafts_dir) if f.startswith("draft_") and f.endswith(".txt")]
            if not draft_files:
                return
            
            # Sort by modification time
            draft_files.sort(key=lambda x: os.path.getmtime(os.path.join(drafts_dir, x)), reverse=True)
            latest_draft = os.path.join(drafts_dir, draft_files[0])
            
            # Check if draft is recent (less than 1 hour old)
            if time.time() - os.path.getmtime(latest_draft) < 3600:
                with open(latest_draft, 'r', encoding='utf-8') as f:
                    draft_text = f.read().strip()
                
                if draft_text and self.gui:
                    # Ask user if they want to recover
                    from PySide6.QtWidgets import QMessageBox
                    reply = QMessageBox.question(
                        self.gui,
                        "Recuperar Borrador",
                        f"Se encontró un borrador reciente:\n\n{draft_text[:100]}...\n\n¿Deseas recuperarlo?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        self.gui.text_edit.setPlainText(draft_text)
                        self.current_draft_file = latest_draft
                        self.gui.update_status("Borrador recuperado - continúa dictando")
                        self._speak("Borrador anterior recuperado")
            
        except Exception as e:
            logger.error(f"Error loading draft: {str(e)}")
    
    def _save_to_history(self, text: str):
        """Save completed dictation to history"""
        try:
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "text": text,
                "word_count": len(text.split()),
                "language": self.language
            }
            
            self.dictation_history.append(history_entry)
            
            # Keep only last 10 entries
            if len(self.dictation_history) > 10:
                self.dictation_history = self.dictation_history[-10:]
            
            # Save to file
            history_dir = os.path.expanduser("~/Documents/EVA_Dictation_History")
            os.makedirs(history_dir, exist_ok=True)
            
            history_file = os.path.join(history_dir, "dictation_history.json")
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.dictation_history, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error saving to history: {str(e)}")
    
    def _cleanup_draft(self):
        """Clean up current draft file"""
        if self.current_draft_file and os.path.exists(self.current_draft_file):
            try:
                os.remove(self.current_draft_file)
                self.current_draft_file = None
            except Exception as e:
                logger.error(f"Error cleaning up draft: {str(e)}")
    
    def _cleanup(self):
        """Clean up resources"""
        self.is_active = False

        # Liberar AudioLock
        audio_lock.release("dictation")

        try:
            # Stop auto-save timer
            if self.auto_save_timer:
                self.auto_save_timer.stop()
                self.auto_save_timer = None

            # Stop worker thread
            if self.worker:
                self.worker.stop_recording()
                self.worker.wait(3000)
                self.worker = None

            # Close grammar corrector
            if self.corrector:
                self.corrector.close()
                self.corrector = None

            # Close GUI
            if self.gui:
                self.gui.close()
                self.gui = None

            # Restore clipboard
            self._restore_clipboard()

            # Reactivar procesamiento de comandos de EVA
            if (self.eva and
                hasattr(self.eva, 'voice_engine') and
                hasattr(self.eva.voice_engine, 'pause_command_processing')):
                self.eva.voice_engine.pause_command_processing = False
                logger.info("Procesamiento de comandos reactivado tras dictado")

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def _setup_global_hotkey(self):
        """Setup global hotkey for dictation activation"""
        try:
            def hotkey_callback():
                """Callback for global hotkey activation"""
                if not self.is_active:
                    logger.info(f"🔥 Dictado activado por hotkey: {self.hotkey_combination}")
                    self.start_dictation()
                else:
                    logger.info("🔥 Dictado ya está activo")
            
            success = setup_dictation_hotkey(self.hotkey_combination, hotkey_callback)
            if success:
                logger.info(f"🔥 Hotkey global configurado: {self.hotkey_combination}")
            else:
                logger.warning("🔥 No se pudo configurar el hotkey global")
                
        except Exception as e:
            logger.error(f"Error setting up global hotkey: {str(e)}")
    
    def cleanup_hotkey(self):
        """Clean up global hotkey"""
        try:
            if HOTKEY_AVAILABLE:
                stop_dictation_hotkey()
                logger.info("🔥 Hotkey global desactivado")
        except Exception as e:
            logger.error(f"Error cleaning up hotkey: {str(e)}")


# Global instance for easy access
_dictation_instance = None


def start_dictation_global(config: Dict[str, Any] = None, eva_instance=None) -> bool:
    """
    Start intelligent dictation process
    
    Args:
        config: Configuration dictionary (optional)
        eva_instance: EVA assistant instance for TTS integration (optional)
    
    Returns:
        bool: True if dictation started successfully, False otherwise
    
    Example:
        >>> from EVA.voice.dictation_intelligent import start_dictation_global
        >>> success = start_dictation_global()
        >>> if success:
        ...     print("Dictation started successfully")
    """
    global _dictation_instance
    
    # Use default config if none provided
    if config is None:
        config = {
            "language": "es",
            "tts": {"enabled": True}
        }
    
    try:
        # Stop any existing dictation
        if _dictation_instance and _dictation_instance.is_active:
            _dictation_instance.stop_dictation()
        
        # Create new dictation instance
        _dictation_instance = IntelligentDictation(config, eva_instance)
        
        # Start dictation
        return _dictation_instance.start_dictation()
        
    except Exception as e:
        logger.error(f"Error in start_dictation: {str(e)}")
        return False


def stop_dictation_global():
    """
    Stop current dictation process
    
    Example:
        >>> from EVA.voice.dictation_intelligent import stop_dictation_global
        >>> stop_dictation_global()
    """
    global _dictation_instance
    
    if _dictation_instance:
        _dictation_instance.stop_dictation()
        _dictation_instance = None


def is_dictation_active() -> bool:
    """
    Check if dictation is currently active
    
    Returns:
        bool: True if dictation is active, False otherwise
    """
    global _dictation_instance
    return _dictation_instance is not None and _dictation_instance.is_active


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Create QApplication if it doesn't exist
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Test configuration
    test_config = {
        "language": "es",
        "tts": {"enabled": True}
    }
    
    # Start dictation
    print("Starting intelligent dictation test...")
    success = start_dictation_global(test_config)
    
    if success:
        print("Dictation started successfully!")
        print("Speak into your microphone...")
        print("Say 'parar dictado' to stop recording")
        
        # Run the application
        sys.exit(app.exec())
    else:
        print("Failed to start dictation")
        sys.exit(1)