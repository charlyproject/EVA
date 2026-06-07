import logging
import os
from typing import List, Optional

from utils.file_utils import get_working_folder, load_last_folder_path, save_last_folder_path

logger = logging.getLogger("EVA")


class ContextManager:
    """Manages EVA's session state: current folder, file sorting, etc."""

    def __init__(self, config, language_manager):
        self.config = config
        self.language_manager = language_manager

        # Folder state
        self.last_opened_folder: Optional[str] = None
        self.current_folder_files: List[str] = []
        self.pending_file_order = False

        # File sorting
        self.file_sort_method = config.get("file_sort_method", "creation")
        logger.info(f"Orden de archivos cargado: {self.file_sort_method}")

        # Load persisted folder
        self.last_opened_folder = load_last_folder_path()
        logger.info(f"Última carpeta cargada: {self.last_opened_folder}")

    # --- Folder resolution ---

    def get_working_folder(self) -> Optional[str]:
        """Obtiene carpeta de trabajo con detección de cambios de contexto"""
        working_folder = get_working_folder()
        if working_folder != self.last_opened_folder:
            self.last_opened_folder = working_folder
            logger.info(f"Carpeta de trabajo cambiada: {working_folder}")
        if self.last_opened_folder and os.path.isdir(self.last_opened_folder):
            return self.last_opened_folder

        if self.last_opened_folder and os.path.isdir(self.last_opened_folder):
            return self.last_opened_folder

        saved_folder = load_last_folder_path()
        if saved_folder:
            self.last_opened_folder = saved_folder
            return saved_folder

        return None

    def update_folder_cache(self, folder_path: str, files: List[str] = None):
        """Actualiza la carpeta activa y su lista de archivos"""
        self.last_opened_folder = folder_path
        if files is not None:
            self.current_folder_files = files
        save_last_folder_path(folder_path)

    # --- File sorting ---

    def set_sort_method(self, method: str):
        """Cambia el método de ordenación de archivos"""
        valid_methods = ["name", "creation", "modification"]
        if method in valid_methods:
            self.file_sort_method = method
            self.config["file_sort_method"] = method
            logger.info(f"Método de orden cambiado a: {method}")

    def save_sort_method_to_config(self):
        """Persiste el método de orden en la configuración"""
        self.config["file_sort_method"] = self.file_sort_method
