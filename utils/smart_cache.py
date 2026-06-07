# smart_cache.py — implementacion minima (812 lineas → 40)
# La interfaz publica se mantiene identica para compatibilidad.
import time
import threading
import logging

logger = logging.getLogger("EVA")

class SmartCache:
    """Cache TTL en memoria, thread-safe. Misma API que la version anterior."""
    def __init__(self, name="default", max_memory_mb=50.0, max_disk_mb=200.0,
                 default_ttl=3600.0, strategy=None, cache_dir="cache"):
        self.name = name
        self.default_ttl = default_ttl
        self._cache = {}  # key -> (value, expires_at)
        self._lock = threading.Lock()
        self._memory_cache = self._cache  # alias para compatibilidad
        logger.debug(f"SmartCache '{name}' iniciado (modo minimo)")

    def start(self): pass
    def stop(self): pass

    def get(self, key, default=None):
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return default
            value, expires_at = entry
            if expires_at and time.time() > expires_at:
                del self._cache[key]
                return default
            return value

    def set(self, key, value, ttl=None, **kwargs):
        expires_at = time.time() + (ttl if ttl is not None else self.default_ttl)
        with self._lock:
            self._cache[key] = (value, expires_at)
        return True

    def delete(self, key):
        with self._lock:
            return self._cache.pop(key, None) is not None

    def clear(self):
        with self._lock:
            self._cache.clear()

    def get_stats(self):
        return {"name": self.name, "entries": len(self._cache)}


# Instancias globales (mismos nombres que antes)
ollama_cache = SmartCache("ollama_responses", default_ttl=3600.0)
voice_cache  = SmartCache("voice_models",     default_ttl=7200.0)
command_cache = SmartCache("commands",        default_ttl=1800.0)