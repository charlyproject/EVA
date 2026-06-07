# core/update_manager.py — STUB (sin servidor de actualizaciones configurado)
import logging
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger("EVA")

class UpdateManager(QObject):
    update_available  = Signal(str, str)   # version, url
    update_error      = Signal(str)
    check_completed   = Signal(bool)

    def __init__(self, config=None, base_dir=None):
        super().__init__()
        self.current_version = self._get_version()
        logger.debug("UpdateManager: modo stub (sin servidor de actualizaciones)")

    def _get_version(self):
        try:
            from __version__ import __version__
            return __version__
        except Exception:
            return "1.0.0"

    def start_periodic_checks(self, *args, **kwargs): pass
    def check_for_updates(self, silent=True): self.check_completed.emit(False)
    def download_update(self, *args, **kwargs): pass
    def remind_later(self, hours=24): pass
    def skip_version(self, version): pass
    def stop(self): pass