"""
Unified Piper TTS System for EVA
Replaces the complex multi-engine TTS system with a simple, efficient Piper-based solution
Uses sounddevice/soundfile instead of pygame (better Python 3.14 compatibility)
"""

import logging
import os
import subprocess
import tempfile
import threading
import time
import queue
from pathlib import Path
from typing import Optional, Dict, Any

import numpy as np
import sounddevice as sd
import soundfile as sf
from PySide6.QtCore import Signal, QObject

from utils.threading_utils import submit_background_task

logger = logging.getLogger("EVA")


class UnifiedPiperTTS(QObject):
    """
    Unified TTS system using Piper for both Spanish and English voices.
    Replaces Coqui TTS, MeloTTS, and Windows SAPI with a single, efficient solution.
    """

    tts_started = Signal()
    tts_completed = Signal()

    def __init__(self, config, language_manager=None):
        super().__init__()
        self.config = config
        self.language_manager = language_manager

        # Voice configuration with 2 variants - Spanish and English only
        self.voices = {
            "es": {
                "name": "EVA Español",
                "model": "es_MX-claude-high.onnx",
                "gender": "female",
                "language": "Spanish",
                "quality": "high",
                "voice_style": "natural"
            },
            "en": {
                "name": "EVA English",
                "model": "en_US-kristin-medium.onnx",
                "gender": "female",
                "language": "English",
                "quality": "medium",
                "voice_style": "neutral"
            }
        }

        # Paths
        self.piper_root = Path(__file__).parent.parent / "piper"
        self.piper_exe = self.piper_root / "piper.exe"
        self.models_dir = self.piper_root / "models"

        # Audio playback state
        self.active_playback_thread = None
        self.is_muted = False
        self.should_stop_speaking = False
        self._current_stream = None
        self._stream_stop_flag = False
        self._playback_data = np.array([], dtype=np.float32)
        self._playback_pos = 0
        self._audio_lock = threading.Lock()

        # Processing queue for async TTS
        self.tts_queue = queue.Queue()
        self.processing_thread = submit_background_task(
            self._process_queue,
            name="tts_processing_queue"
        )
        self.is_processing = False

        # Initialize audio system (sounddevice)
        self._initialize_audio()

        # Verify installation
        self._verify_installation()

        logger.info("🎵 Unified Piper TTS initialized successfully (sounddevice)")
        logger.info(f"🎵 Available voice variants: {list(self.voices.keys())}")
        logger.info("🎵 Voice configuration: Spanish (natural), English (US)")

    def _initialize_audio(self):
        """Initialize sounddevice for audio playback"""
        try:
            # Query available output devices
            devices = sd.query_devices()
            output_devices = [d for d in devices if d['max_output_channels'] > 0]
            logger.info(f"🎵 Audio devices found: {len(output_devices)} output device(s)")
            for d in output_devices:
                logger.info(f"   - [{d['index']}] {d['name']} (channels: {d['max_output_channels']})")
            logger.info("🎵 Audio system initialized (sounddevice)")
        except Exception as e:
            logger.error(f"🎵 Error initializing audio: {str(e)}")

    def _verify_installation(self):
        """Verify that Piper and voice models are properly installed"""
        issues = []

        # Check Piper executable
        if not self.piper_exe.exists():
            issues.append(f"Piper executable not found: {self.piper_exe}")

        # Check voice models
        for lang, voice_info in self.voices.items():
            model_path = self.models_dir / voice_info["model"]
            json_path = self.models_dir / f"{voice_info['model']}.json"

            if not model_path.exists():
                issues.append(f"Voice model not found: {model_path}")
            if not json_path.exists():
                issues.append(f"Voice config not found: {json_path}")

        if issues:
            logger.error("🚨 Piper TTS installation issues:")
            for issue in issues:
                logger.error(f"   • {issue}")
            raise RuntimeError("Piper TTS not properly installed")
        else:
            logger.info("✅ Piper TTS installation verified successfully")

    def speak(self, text: str, language: Optional[str] = None, use_transition: bool = False):
        """
        Add text to speech queue for processing
        """
        if self.is_muted:
            return

        # 🛡️ FILTRAR EMOJIS Y CARACTERES PROBLEMÁTICOS
        cleaned_text = self._clean_text_for_tts(text)

        if not cleaned_text or not cleaned_text.strip():
            logger.warning("🎵 Text became empty after cleaning")
            return

        # Auto-detect language if not specified
        if language is None:
            language = self._detect_language(cleaned_text)

        # Add to processing queue
        self.tts_queue.put((cleaned_text, language, use_transition))
        if not self.is_processing:
            self._start_processing()

    def _detect_language(self, text: str) -> str:
        """Detect language and return appropriate voice"""
        if self.language_manager:
            lang = self.language_manager.current_lang
            if lang == "es":
                return "es"
            else:
                return "en"

        # Simple heuristic
        spanish_indicators = ['el', 'la', 'de', 'que', 'y', 'es', 'en', 'un', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'una', 'tiene', 'más', 'este', 'está', 'como', 'todo', 'pero', 'sus', 'muy', 'era', 'sobre', 'ser', 'hacer', 'cada', 'estado', 'también', 'hasta', 'estos', 'desde', 'durante', 'si', 'entre', 'sin', 'bajo', 'estar', 'tener', 'tanto', 'donde', 'sido', 'según', 'menos', 'pueden', 'parte', 'después', 'mismo', 'tiempo']

        words = text.lower().split()
        spanish_count = sum(1 for word in words if word in spanish_indicators)

        if len(words) > 0 and spanish_count / len(words) > 0.3:
            return 'es'
        else:
            return 'en'

    def _start_processing(self):
        """Start processing the TTS queue"""
        self.is_processing = True

    def _process_queue(self):
        """Process TTS queue in background thread"""
        while True:
            try:
                if not self.tts_queue.empty() and not self.should_stop_speaking:
                    text, language, use_transition = self.tts_queue.get()
                    if not self.is_muted and not self.should_stop_speaking:
                        self._synthesize_speech(text, language, use_transition)
                    self.tts_queue.task_done()
                else:
                    self.is_processing = False
                    time.sleep(0.1)
            except Exception as e:
                logger.error(f"🎵 Error processing TTS queue: {str(e)}")
                logger.info("🎵 TTS queue processing error, but continuing operation")
                self.is_processing = False
                time.sleep(0.5)

    def _synthesize_speech(self, text: str, language: str, use_transition: bool):
        """Synthesize speech using Piper"""
        if self.should_stop_speaking or self.is_muted:
            return

        # Emit start signal
        self.tts_started.emit()
        logger.debug("🎵 TTS started - indicator should be visible")

        try:
            # Filter text content
            filtered_text = self._filter_tts_content(text)
            if not filtered_text.strip():
                logger.info("🎵 Filtered text is empty, skipping synthesis")
                self.tts_completed.emit()
                return

            # Check if we should stop before transition
            if self.should_stop_speaking or self.is_muted:
                self.tts_completed.emit()
                return

            # Add transition if requested
            if use_transition and not self.should_stop_speaking and not self.is_muted:
                transition_phrases = self.config.get("frases_transicion", [""])
                if transition_phrases and transition_phrases[0]:
                    import random
                    transition = random.choice(transition_phrases)
                    self._generate_and_play_audio(transition, language)

            # Check again before main synthesis
            if self.should_stop_speaking or self.is_muted:
                self.tts_completed.emit()
                return

            # Generate and play main audio
            self._generate_and_play_audio(filtered_text, language)

        except Exception as e:
            logger.error(f"🎵 Error in speech synthesis: {str(e)}")
            logger.error(f"🎵 TTS synthesis failed for text: {text[:50]}...")
            logger.info("🎵 TTS synthesis failed, but continuing normal operation")
            self.tts_completed.emit()

    def _filter_tts_content(self, text: str) -> str:
        """Filter out content that shouldn't be spoken"""
        import re

        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'\*.*?\*', '', text)
        text = re.sub(r'_.*?_', '', text)
        text = re.sub(r':\w+:', '', text)

        special_chars = ["*", "_", "~", "`", "|", ">", "<"]
        for char in special_chars:
            text = text.replace(char, " ")

        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _clean_text_for_tts(self, text: str) -> str:
        """
        Limpia el texto para que TTS hable de forma natural
        """
        import re

        original_text = text

        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"
                                   u"\U0001F300-\U0001F5FF"
                                   u"\U0001F680-\U0001F6FF"
                                   u"\U0001F1E0-\U0001F1FF"
                                   u"\U00002500-\U00002BEF"
                                   u"\U00002702-\U000027B0"
                                   u"\U00002702-\U000027B0"
                                   u"\U000024C2-\U0001F251"
                                   u"\U0001f926-\U0001f937"
                                   u"\U00010000-\U0010ffff"
                                   u"\u2640-\u2642"
                                   u"\u2600-\u2B55"
                                   u"\u200d"
                                   u"\u23cf"
                                   u"\u23e9"
                                   u"\u231a"
                                   u"\ufe0f"
                                   u"\u3030"
                                   "]+", flags=re.UNICODE)
        text = emoji_pattern.sub('', text)

        text = re.sub(r'\bEVA\b', 'Eva', text)
        text = re.sub(r'\bE\.V\.A\.?\b', 'Eva', text)
        text = re.sub(r'\bE V A\b', 'Eva', text)

        text = re.sub(r'[/\\|]', ' ', text)
        text = re.sub(r'[•·▪▫]', ', ', text)
        text = re.sub(r'[→←↑↓]', ' ', text)
        text = re.sub(r'[★☆✓✗✘]', '', text)

        text = re.sub(r'\.{2,}', '.', text)
        text = re.sub(r'!{2,}', '!', text)
        text = re.sub(r'\?{2,}', '?', text)

        text = re.sub(r'[^\w\s.,;:!?¿¡\-\'"()]', ' ', text, flags=re.UNICODE)

        text = re.sub(r'\bDr\.', 'Doctor', text)
        text = re.sub(r'\bSr\.', 'Señor', text)
        text = re.sub(r'\bSra\.', 'Señora', text)
        text = re.sub(r'\betc\.', 'etcétera', text)

        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = text.strip()

        if text != original_text:
            logger.debug(f"🎵 Text cleaned for natural TTS: '{original_text}' -> '{text}'")

        return text

    def _generate_and_play_audio(self, text: str, language: str):
        """
        Generate audio using Piper and play it via sounddevice
        """
        if self.should_stop_speaking or self.is_muted:
            return

        # Validate language and map to voice variants
        if language not in self.voices:
            if language and language.startswith('es'):
                language = 'es'
                logger.debug("🎵 Mapped language variant to 'es'")
            else:
                logger.warning(f"🎵 Unsupported language '{language}', using 'es'")
                language = 'es'

        voice_info = self.voices[language]
        model_path = self.models_dir / voice_info["model"]

        # Create temporary output file
        with tempfile.NamedTemporaryFile(prefix="eva_piper_", suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Check again before generation
            if self.should_stop_speaking or self.is_muted:
                self._cleanup_temp_file(temp_path)
                return

            # Generate audio using Piper
            cmd = [
                str(self.piper_exe),
                "--model", str(model_path),
                "--output_file", temp_path
            ]

            # Apply voice configuration
            speed = self.config.get("tts", {}).get("speed", 1.0)
            if speed != 1.0:
                cmd.extend(["--length_scale", str(1.0 / speed)])

            logger.debug(f"🎵 Using default Piper parameters for {language}")
            logger.debug(f"🎵 Generating audio with Piper: {voice_info['name']}")

            # Run Piper TTS
            process = subprocess.run(
                cmd,
                input=text,
                text=True,
                capture_output=True,
                timeout=30
            )

            if process.returncode != 0:
                error_msg = process.stderr.strip() if process.stderr else "Unknown error"
                logger.error(f"Piper TTS process failed with return code {process.returncode}")
                logger.error(f"Piper TTS stderr: {error_msg}")
                logger.error(f"Piper TTS stdout: {process.stdout}")
                raise RuntimeError(f"Piper TTS failed: {error_msg}")

            # Check if we should stop after generation
            if self.should_stop_speaking or self.is_muted:
                self._cleanup_temp_file(temp_path)
                return

            # Verify audio file was created
            if not os.path.exists(temp_path) or os.path.getsize(temp_path) < 1024:
                raise RuntimeError("Invalid audio file generated")

            logger.info(f"🎵 Audio generated successfully with {voice_info['name']}")

            # Play audio if not muted
            if not self.should_stop_speaking and not self.is_muted:
                self._play_audio(temp_path)
            else:
                self._cleanup_temp_file(temp_path)

        except subprocess.TimeoutExpired:
            logger.error("🎵 Piper TTS timeout")
            self._cleanup_temp_file(temp_path)
            self.tts_completed.emit()
        except Exception as e:
            logger.error(f"🎵 Error generating audio: {str(e)}")
            self._cleanup_temp_file(temp_path)
            self.tts_completed.emit()

    def _play_audio(self, file_path: str):
        """Play audio file using sounddevice in a separate thread"""

        def playback_thread():
            try:
                # Check before loading
                if self.should_stop_speaking or self.is_muted:
                    self._cleanup_temp_file(file_path)
                    self.tts_completed.emit()
                    return

                with self._audio_lock:
                    # Load audio data with soundfile
                    data, samplerate = sf.read(file_path, dtype='float32')

                    if self.should_stop_speaking or self.is_muted:
                        self._cleanup_temp_file(file_path)
                        self.tts_completed.emit()
                        return

                    # Get volume from config
                    volume = self.config.get("tts", {}).get("volume", 0.8)
                    if self.is_muted:
                        volume = 0.0

                    # Apply volume
                    data = data * volume

                    # Ensure data is contiguous and correct dtype
                    if data.ndim > 1:
                        data = data[:, 0]  # Use first channel if stereo
                    data = np.ascontiguousarray(data, dtype=np.float32)

                    # Play using sounddevice
                    self._current_stream = sd.OutputStream(
                        samplerate=samplerate,
                        channels=1,
                        dtype='float32',
                        callback=_stream_callback
                    )

                    self._playback_data = data
                    self._playback_pos = 0
                    self._stream_stop_flag = False

                    with self._current_stream:
                        # Wait for playback to finish with real-time mute checking
                        chunk_duration = 0.05  # 50ms chunks
                        total_duration = len(data) / samplerate
                        elapsed = 0

                        while elapsed < total_duration and not self._stream_stop_flag:
                            if self.should_stop_speaking or self.is_muted:
                                break
                            time.sleep(chunk_duration)
                            elapsed += chunk_duration

                    # Clean up
                    self._current_stream = None
                    self._cleanup_temp_file(file_path)

                    # Emit completion signal (only if not stopped by user)
                    if not self._stream_stop_flag:
                        self.tts_completed.emit()
                    logger.debug("🎵 Audio playback completed - emitting tts_completed signal")

            except Exception as e:
                logger.error(f"🎵 Playback error: {str(e)}")
                try:
                    self._cleanup_temp_file(file_path)
                except Exception:
                    pass
                self.tts_completed.emit()
            finally:
                self.active_playback_thread = None

        def _stream_callback(outdata, frames, time_info, status):
            """Callback for sounddevice streaming playback"""
            if self._stream_stop_flag or self.should_stop_speaking or self.is_muted:
                outdata[:] = 0
                raise sd.CallbackStop()
                return

            chunk_size = frames
            if self._playback_pos >= len(self._playback_data):
                outdata[:] = 0
                raise sd.CallbackStop()
                return

            end_pos = min(self._playback_pos + chunk_size, len(self._playback_data))
            chunk = self._playback_data[self._playback_pos:end_pos]

            # Pad with zeros if we're at the end
            if len(chunk) < chunk_size:
                chunk = np.pad(chunk, (0, chunk_size - len(chunk)), mode='constant')

            outdata[:] = chunk.reshape(-1, 1)
            self._playback_pos = end_pos

        # Start playback thread
        self.active_playback_thread = submit_background_task(
            playback_thread,
            name="tts_playback"
        )

    def _cleanup_temp_file(self, file_path: str):
        """Safely delete temporary file"""
        try:
            if os.path.exists(file_path):
                for _ in range(3):
                    try:
                        os.remove(file_path)
                        break
                    except PermissionError:
                        time.sleep(0.5)
        except Exception as e:
            logger.debug(f"🎵 Could not delete temp file {file_path}: {str(e)}")

    def stop(self):
        """Stop any ongoing speech synthesis"""
        try:
            self.should_stop_speaking = True
            self._stream_stop_flag = True

            # Stop sounddevice stream
            if self._current_stream is not None:
                try:
                    self._current_stream.stop()
                except Exception:
                    pass

            # Clear TTS queue
            while not self.tts_queue.empty():
                try:
                    self.tts_queue.get_nowait()
                    self.tts_queue.task_done()
                except queue.Empty:
                    break

            logger.debug("🎵 Speech synthesis stopped")

        except Exception as e:
            logger.error(f"🎵 Error stopping synthesis: {str(e)}")

    def set_mute(self, muted: bool):
        """Set mute state with immediate effect"""
        self.is_muted = muted
        if muted:
            self._stream_stop_flag = True
            self.stop()
            logger.debug("🎵 TTS muted")
        else:
            logger.debug("🎵 TTS unmuted")

    def resume_speech(self):
        """Resume speech synthesis"""
        self.should_stop_speaking = False
        self.is_muted = False
        self._stream_stop_flag = False
        logger.debug("🎵 Speech synthesis resumed")

    def get_available_voices(self) -> list:
        """Get list of available voices for compatibility"""
        voices = []
        for lang, voice_info in self.voices.items():
            voices.append({
                "id": lang,
                "name": voice_info["name"],
                "language": voice_info["language"],
                "gender": voice_info["gender"],
                "quality": voice_info["quality"]
            })
        return voices

    def set_voice(self, voice_id: str):
        """Set voice for compatibility (Piper uses language-based selection)"""
        if voice_id in self.voices:
            logger.info(f"🎵 Voice set to: {self.voices[voice_id]['name']}")
        else:
            logger.warning(f"🎵 Voice '{voice_id}' not available, using default")

    def update_config(self, new_config: Dict[str, Any]):
        """Update configuration"""
        self.config = new_config
        logger.info("🎵 Configuration updated")

    def cleanup(self):
        """Clean up resources"""
        try:
            self.stop()

            while not self.tts_queue.empty():
                try:
                    self.tts_queue.get_nowait()
                    self.tts_queue.task_done()
                except queue.Empty:
                    break

            logger.info("🎵 Unified Piper TTS cleaned up")

        except Exception as e:
            logger.error(f"🎵 Cleanup error: {str(e)}")

    # Legacy Coqui TTS methods removed - no longer needed with Piper TTS

    @property
    def conversation_mode(self) -> bool:
        """Compatibility property"""
        return getattr(self, '_conversation_mode', False)

    @conversation_mode.setter
    def conversation_mode(self, value: bool):
        """Compatibility property setter"""
        self._conversation_mode = value
        logger.debug(f"🎵 Conversation mode: {value}")