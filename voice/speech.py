"""
Enhanced Voice Assistant v.2.0 - Unified Piper TTS System
Simple, efficient, and reliable voice synthesis using Piper TTS
"""

import logging
from typing import Dict, Any

from PySide6.QtCore import Signal, QObject

from .unified_piper_tts import UnifiedPiperTTS

logger = logging.getLogger("EVA")


class SpeechSynthesizer(QObject):
    """
    Simplified Speech Synthesizer using Unified Piper TTS
    Replaces the complex multi-engine system with a single, efficient solution
    """
    tts_started = Signal()
    tts_completed = Signal()
    
    def __init__(
        self,
        config,
        hardware_config=None,
        stealth_mode=False,
        download_callback=None,
        status_callback=None,
        language_manager=None,
    ):
        super().__init__()
        self.config = config
        self.stealth_mode = stealth_mode
        self.download_callback = download_callback
        self.status_callback = status_callback
        self.language_manager = language_manager

        # Initialize unified Piper TTS system
        try:
            self.piper_tts = UnifiedPiperTTS(config, language_manager)
            
            # Connect signals
            self.piper_tts.tts_started.connect(self.tts_started.emit)
            self.piper_tts.tts_completed.connect(self.tts_completed.emit)
            
            logger.info("🎵 Speech Synthesizer initialized with Unified Piper TTS")
            
        except Exception as e:
            logger.error(f"🚨 Failed to initialize Piper TTS: {str(e)}")
            logger.error("🚨 Please check Piper installation in EVA/piper/")
            raise RuntimeError(f"Piper TTS initialization failed: {str(e)}")

        # Compatibility properties for existing EVA integration
        self.available_voices = self.piper_tts.get_available_voices()
        self.is_muted = False
        self.should_stop_speaking = False
        self.conversation_mode = False
        


    def speak(self, text: str, use_transition: bool = False):
        """Synthesize speech from text using Piper TTS"""
        if self.stealth_mode:
            return
        
        # Delegate to Piper TTS system
        language = None
        if self.language_manager:
            language = self.language_manager.current_lang
        
        self.piper_tts.speak(text, language, use_transition)
    
    def stop(self):
        """Stop any ongoing speech"""
        self.piper_tts.stop()
        self.should_stop_speaking = True
    
    def set_mute(self, muted: bool):
        """Set mute state"""
        self.is_muted = muted
        self.piper_tts.set_mute(muted)
        if muted:
            self.should_stop_speaking = True
    
    def resume_speech(self):
        """Resume speech synthesis"""
        self.should_stop_speaking = False
        self.is_muted = False
        self.piper_tts.resume_speech()
    
    def get_available_voices(self):
        """Get available voices"""
        return self.piper_tts.get_available_voices()
    
    def set_voice(self, voice_id: str):
        """Set voice (compatibility method)"""
        self.piper_tts.set_voice(voice_id)
        logger.info(f"🎵 Voice setting delegated to Piper TTS: {voice_id}")
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update configuration"""
        self.config = new_config
        self.piper_tts.update_config(new_config)
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.piper_tts.cleanup()
            logger.info("🎵 Speech Synthesizer cleaned up")
        except Exception as e:
            logger.error(f"🎵 Cleanup error: {str(e)}")
    

    
    @property
    def engine(self):
        """Compatibility property for pyttsx3 engine"""
        return None  # No longer used
    

    
    def process_enhanced_command(self, command_text: str) -> bool:
        """Process enhanced voice commands - simplified for Piper"""
        logger.debug(f"🎵 Enhanced command processing: {command_text}")
        return False  # Simplified - no complex command processing needed