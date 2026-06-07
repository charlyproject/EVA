"""
🧹 Windows Cleanup Manager - Limpieza específica para ejecutables Windows
Maneja archivos temporales, cache, registros y recursos del sistema
"""

import os
import sys
import tempfile
import shutil
import logging
import winreg
import ctypes
from pathlib import Path
from typing import List, Set, Optional
import glob
import time

logger = logging.getLogger(__name__)

class WindowsCleanupManager:
    """
    Gestor de limpieza específico para Windows
    Optimizado para ejecutables PyInstaller
    """
    
    def __init__(self):
        self.temp_files: Set[str] = set()
        self.temp_dirs: Set[str] = set()
        self.registry_keys: List[str] = []
        self.mutex_handles: List[int] = []
        self.is_frozen = getattr(sys, 'frozen', False)
        
        # Directorios comunes de temporales
        self.temp_base = tempfile.gettempdir()
        self.user_temp = os.path.expanduser("~/AppData/Local/Temp")
        self.eva_temp_dir = os.path.join(self.temp_base, "EVA_Assistant")
        
        # Directorios temporales adicionales que otros módulos esperan
        self.eva_session_temp = os.path.join(self.temp_base, "eva", "session_temp")
        
        # Crear directorios temporales de EVA si no existen
        os.makedirs(self.eva_temp_dir, exist_ok=True)
        try:
            os.makedirs(self.eva_session_temp, exist_ok=True)
        except Exception as e:
            logger.warning(f"No se pudo crear eva/session_temp: {e}")
    
    def register_temp_file(self, filepath: str):
        """Registra archivo temporal para limpieza"""
        self.temp_files.add(str(Path(filepath).resolve()))
        logger.debug(f"Archivo temporal registrado: {filepath}")
    
    def register_temp_dir(self, dirpath: str):
        """Registra directorio temporal para limpieza"""
        self.temp_dirs.add(str(Path(dirpath).resolve()))
        logger.debug(f"Directorio temporal registrado: {dirpath}")
    
    def register_registry_key(self, key_path: str):
        """Registra clave de registro para limpieza"""
        self.registry_keys.append(key_path)
        logger.debug(f"Clave de registro registrada: {key_path}")
    
    def create_temp_file(self, suffix: str = "", prefix: str = "eva_") -> str:
        """
        Crea archivo temporal y lo registra automáticamente
        
        Returns:
            Ruta del archivo temporal creado
        """
        import tempfile
        fd, filepath = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=self.eva_temp_dir)
        os.close(fd)  # Cerrar descriptor
        self.register_temp_file(filepath)
        return filepath
    
    def create_temp_dir(self, suffix: str = "", prefix: str = "eva_") -> str:
        """
        Crea directorio temporal y lo registra automáticamente
        
        Returns:
            Ruta del directorio temporal creado
        """
        import tempfile
        dirpath = tempfile.mkdtemp(suffix=suffix, prefix=prefix, dir=self.eva_temp_dir)
        self.register_temp_dir(dirpath)
        return dirpath
    
    def cleanup_registered_files(self):
        """Limpia archivos y directorios registrados"""
        logger.info("🧹 Limpiando archivos temporales registrados...")
        
        # Limpiar archivos
        cleaned_files = 0
        for filepath in self.temp_files.copy():
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    cleaned_files += 1
                    logger.debug(f"Eliminado: {filepath}")
                self.temp_files.discard(filepath)
            except Exception as e:
                logger.warning(f"No se pudo eliminar {filepath}: {e}")
        
        # Limpiar directorios
        cleaned_dirs = 0
        for dirpath in self.temp_dirs.copy():
            try:
                if os.path.exists(dirpath):
                    shutil.rmtree(dirpath)
                    cleaned_dirs += 1
                    logger.debug(f"Directorio eliminado: {dirpath}")
                self.temp_dirs.discard(dirpath)
            except Exception as e:
                logger.warning(f"No se pudo eliminar directorio {dirpath}: {e}")
        
        logger.info(f"✅ Limpieza completada: {cleaned_files} archivos, {cleaned_dirs} directorios")
    
    def cleanup_pyinstaller_cache(self):
        """Limpia cache específico de PyInstaller"""
        if not self.is_frozen:
            return
            
        logger.info("🗂️ Limpiando cache de PyInstaller...")
        
        try:
            # Patrones de cache de PyInstaller
            patterns = [
                os.path.join(self.temp_base, "_MEI*"),
                os.path.join(self.user_temp, "_MEI*"),
                os.path.join(self.temp_base, "pyinstaller_*"),
            ]
            
            cleaned = 0
            for pattern in patterns:
                for cache_path in glob.glob(pattern):
                    try:
                        if os.path.exists(cache_path):
                            shutil.rmtree(cache_path)
                            cleaned += 1
                            logger.debug(f"Cache PyInstaller eliminado: {cache_path}")
                    except Exception as e:
                        logger.debug(f"No se pudo eliminar cache {cache_path}: {e}")
            
            logger.info(f"✅ Cache PyInstaller limpiado: {cleaned} directorios")
            
        except Exception as e:
            logger.warning(f"Error limpiando cache PyInstaller: {e}")
    
    def cleanup_eva_temp_files(self):
        """Limpia archivos temporales específicos de EVA"""
        logger.info("📁 Limpiando archivos temporales de EVA...")
        
        try:
            # Patrones de archivos temporales de EVA
            eva_patterns = [
                os.path.join(self.temp_base, "eva_*"),
                os.path.join(self.temp_base, "EVA_*"),
                os.path.join(self.user_temp, "eva_*"),
                os.path.join(self.user_temp, "EVA_*"),
            ]
            
            cleaned = 0
            for pattern in eva_patterns:
                for temp_path in glob.glob(pattern):
                    try:
                        if os.path.isfile(temp_path):
                            os.remove(temp_path)
                            cleaned += 1
                        elif os.path.isdir(temp_path):
                            shutil.rmtree(temp_path)
                            cleaned += 1
                        logger.debug(f"Temporal EVA eliminado: {temp_path}")
                    except Exception as e:
                        logger.debug(f"No se pudo eliminar {temp_path}: {e}")
            
            logger.info(f"✅ Temporales EVA limpiados: {cleaned} elementos")
            
        except Exception as e:
            logger.warning(f"Error limpiando temporales EVA: {e}")
    
    def cleanup_registry_entries(self):
        """Limpia entradas de registro registradas"""
        if not self.registry_keys:
            return
            
        logger.info("📋 Limpiando entradas de registro...")
        
        cleaned = 0
        for key_path in self.registry_keys:
            try:
                # Intentar eliminar clave de registro
                parts = key_path.split('\\', 1)
                if len(parts) == 2:
                    root_name, subkey = parts
                    root_key = getattr(winreg, root_name, None)
                    if root_key:
                        winreg.DeleteKey(root_key, subkey)
                        cleaned += 1
                        logger.debug(f"Clave de registro eliminada: {key_path}")
            except FileNotFoundError:
                # Clave ya no existe
                pass
            except Exception as e:
                logger.warning(f"No se pudo eliminar clave {key_path}: {e}")
        
        logger.info(f"✅ Registro limpiado: {cleaned} claves")
    
    def release_mutex_handles(self):
        """Libera handles de mutex registrados"""
        if not self.mutex_handles:
            return
            
        logger.info("🔒 Liberando mutex handles...")
        
        released = 0
        for handle in self.mutex_handles:
            try:
                ctypes.windll.kernel32.CloseHandle(handle)
                released += 1
                logger.debug(f"Mutex handle liberado: {handle}")
            except Exception as e:
                logger.warning(f"Error liberando handle {handle}: {e}")
        
        self.mutex_handles.clear()
        logger.info(f"✅ Mutex handles liberados: {released}")
    
    def force_close_handles(self):
        """Fuerza el cierre de handles del proceso actual"""
        if not self.is_frozen:
            return
            
        try:
            import psutil
            current_process = psutil.Process()
            
            # Cerrar handles de archivos abiertos
            for file_handle in current_process.open_files():
                try:
                    file_handle.fd.close()
                except Exception:
                    pass
                    
            logger.info("🔧 Handles de archivos forzados a cerrar")
            
        except ImportError:
            logger.debug("psutil no disponible para cierre de handles")
        except Exception as e:
            logger.warning(f"Error forzando cierre de handles: {e}")
    
    def full_cleanup(self):
        """Ejecuta limpieza completa para cierre de ejecutable"""
        logger.info("🧹 Iniciando limpieza completa de Windows...")
        
        start_time = time.time()
        
        # Secuencia de limpieza
        self.cleanup_registered_files()
        self.cleanup_eva_temp_files()
        self.cleanup_pyinstaller_cache()
        self.cleanup_registry_entries()
        self.release_mutex_handles()
        
        # Para ejecutables, limpieza más agresiva
        if self.is_frozen:
            self.force_close_handles()
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Limpieza completa finalizada en {elapsed:.1f}s")
    
    def emergency_cleanup(self):
        """Limpieza de emergencia rápida"""
        logger.warning("🚨 Ejecutando limpieza de emergencia...")
        
        try:
            # Solo lo esencial
            for filepath in list(self.temp_files):
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                except Exception:
                    pass
            
            for dirpath in list(self.temp_dirs):
                try:
                    if os.path.exists(dirpath):
                        shutil.rmtree(dirpath)
                except Exception:
                    pass
            
            self.release_mutex_handles()
            
        except Exception as e:
            logger.error(f"Error en limpieza de emergencia: {e}")

# Instancia global
_global_cleanup_manager: Optional[WindowsCleanupManager] = None

def get_cleanup_manager() -> WindowsCleanupManager:
    """Obtiene la instancia global del gestor de limpieza"""
    global _global_cleanup_manager
    if _global_cleanup_manager is None:
        _global_cleanup_manager = WindowsCleanupManager()
    return _global_cleanup_manager

def create_temp_file(suffix: str = "", prefix: str = "eva_") -> str:
    """Función de conveniencia para crear archivo temporal"""
    return get_cleanup_manager().create_temp_file(suffix, prefix)

def create_temp_dir(suffix: str = "", prefix: str = "eva_") -> str:
    """Función de conveniencia para crear directorio temporal"""
    return get_cleanup_manager().create_temp_dir(suffix, prefix)

def register_temp_file(filepath: str):
    """Función de conveniencia para registrar archivo temporal"""
    get_cleanup_manager().register_temp_file(filepath)

def register_temp_dir(dirpath: str):
    """Función de conveniencia para registrar directorio temporal"""
    get_cleanup_manager().register_temp_dir(dirpath)

def full_cleanup():
    """Función de conveniencia para limpieza completa"""
    get_cleanup_manager().full_cleanup()