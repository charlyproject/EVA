import threading
import logging

logger = logging.getLogger("EVA")


class AudioLock:
    """Global singleton for coordinating microphone access."""

    _instance = None
    _class_lock = threading.Lock()

    def __new__(cls):
        with cls._class_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._owner = None
        self._owner_lock = threading.Lock()

    def acquire(self, owner: str, blocking: bool = True) -> bool:
        """Try to acquire the mic lock for an owner ('voice_engine' or 'dictation')."""
        with self._owner_lock:
            if self._owner is None:
                self._owner = owner
                logger.debug(f"AudioLock adquirido por {owner}")
                return True
            if self._owner == owner:
                return True
            if blocking:
                return False
            return False

    def release(self, owner: str):
        """Release the lock if current owner matches."""
        with self._owner_lock:
            if self._owner == owner:
                logger.debug(f"AudioLock liberado por {owner}")
                self._owner = None
            else:
                logger.warning(f"AudioLock: {owner} intentó liberar pero dueño es {self._owner}")

    @property
    def is_locked(self) -> bool:
        return self._owner is not None

    @property
    def current_owner(self) -> str:
        return self._owner


audio_lock = AudioLock()
