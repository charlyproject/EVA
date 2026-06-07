"""
🧵 ThreadRegistry - Gestor centralizado de hilos para EVA
Optimizado para ejecutables de Windows con cierre limpio
"""

import threading
import logging
import time
import os
import sys
from typing import Dict, Set, Optional, List
import atexit
import signal

logger = logging.getLogger(__name__)

class ThreadRegistry:
    """
    Registro centralizado de hilos para garantizar cierre limpio en ejecutables Windows
    """
    
    def __init__(self):
        self._threads: Dict[str, threading.Thread] = {}
        self._stop_events: Dict[str, threading.Event] = {}
        self._cleanup_callbacks: Dict[str, callable] = {}
        self._lock = threading.Lock()
        self._shutdown_initiated = False
        self._temp_files: Set[str] = set()
        self._temp_dirs: Set[str] = set()
        
        # Registrar limpieza automática
        atexit.register(self._emergency_cleanup)
        
        # Handlers para Windows
        if sys.platform == 'win32':
            try:
                signal.signal(signal.SIGTERM, self._signal_handler)
                signal.signal(signal.SIGINT, self._signal_handler)
            except Exception as e:
                logger.warning(f"No se pudieron registrar signal handlers: {e}")
    
    def register_thread(self, 
                       name: str, 
                       thread: threading.Thread, 
                       stop_event: Optional[threading.Event] = None,
                       cleanup_callback: Optional[callable] = None):
        """
        Registra un hilo para seguimiento y cierre controlado
        
        Args:
            name: Nombre único del hilo
            thread: Instancia del hilo
            stop_event: Evento para señalar parada
            cleanup_callback: Función de limpieza específica
        """
        with self._lock:
            if self._shutdown_initiated:
                logger.warning(f"No se puede registrar hilo {name}: shutdown iniciado")
                return
                
            self._threads[name] = thread
            if stop_event:
                self._stop_events[name] = stop_event
            if cleanup_callback:
                self._cleanup_callbacks[name] = cleanup_callback
                
            logger.debug(f"Hilo registrado: {name}")
    
    def unregister_thread(self, name: str):
        """Desregistra un hilo que ya terminó"""
        with self._lock:
            self._threads.pop(name, None)
            self._stop_events.pop(name, None)
            self._cleanup_callbacks.pop(name, None)
            logger.debug(f"Hilo desregistrado: {name}")
    
    def register_temp_file(self, filepath: str):
        """Registra archivo temporal para limpieza"""
        self._temp_files.add(str(filepath))
    
    def register_temp_dir(self, dirpath: str):
        """Registra directorio temporal para limpieza"""
        self._temp_dirs.add(str(dirpath))
    
    def get_active_threads(self) -> List[str]:
        """Retorna lista de hilos activos"""
        with self._lock:
            return [name for name, thread in self._threads.items() if thread.is_alive()]
    
    def shutdown_all(self, timeout: float = 5.0, force_exit: bool = True):
        """
        Cierre ordenado de todos los hilos registrados
        Optimizado para ejecutables Windows
        
        Args:
            timeout: Tiempo máximo de espera por hilo
            force_exit: Si forzar salida en caso de hilos persistentes
        """
        if self._shutdown_initiated:
            return
            
        self._shutdown_initiated = True
        logger.info("🔄 Iniciando shutdown controlado de hilos...")
        
        start_time = time.time()
        
        # FASE 1: Ejecutar callbacks de limpieza
        logger.info("📋 Ejecutando callbacks de limpieza...")
        for name, callback in self._cleanup_callbacks.items():
            try:
                callback()
                logger.debug(f"Callback ejecutado: {name}")
            except Exception as e:
                logger.error(f"Error en callback {name}: {e}")
        
        # FASE 2: Señalar parada a todos los hilos
        logger.info("🛑 Señalizando parada a hilos...")
        for name, event in self._stop_events.items():
            try:
                event.set()
                logger.debug(f"Stop event enviado: {name}")
            except Exception as e:
                logger.error(f"Error enviando stop event a {name}: {e}")
        
        # FASE 3: Esperar cierre con timeout progresivo
        logger.info("⏳ Esperando cierre de hilos...")
        remaining_timeout = timeout
        
        for name, thread in list(self._threads.items()):
            if not thread.is_alive():
                continue
                
            thread_start = time.time()
            thread.join(timeout=min(remaining_timeout, 2.0))
            elapsed = time.time() - thread_start
            remaining_timeout -= elapsed
            
            if thread.is_alive():
                logger.warning(f"⚠️ Hilo {name} no se cerró en {elapsed:.1f}s")
            else:
                logger.debug(f"✅ Hilo {name} cerrado correctamente")
                
            if remaining_timeout <= 0:
                break
        
        # FASE 4: Verificar hilos persistentes
        active_threads = self.get_active_threads()
        if active_threads:
            logger.warning(f"⚠️ Hilos aún activos: {active_threads}")
            
            # Para ejecutables, intentar cierre más agresivo
            if getattr(sys, 'frozen', False) and force_exit:
                logger.warning("🔥 Ejecutable detectado: forzando cierre...")
                self._cleanup_temp_files()
                time.sleep(0.5)  # Dar tiempo a logs
                os._exit(0)
        
        # FASE 5: Limpieza de archivos temporales
        self._cleanup_temp_files()
        
        total_time = time.time() - start_time
        logger.info(f"✅ Shutdown completado en {total_time:.1f}s")
    
    def _cleanup_temp_files(self):
        """Limpia archivos y directorios temporales"""
        logger.info("🧹 Limpiando archivos temporales...")
        
        # Limpiar archivos
        for filepath in self._temp_files.copy():
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.debug(f"Archivo temporal eliminado: {filepath}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar {filepath}: {e}")
        
        # Limpiar directorios
        for dirpath in self._temp_dirs.copy():
            try:
                if os.path.exists(dirpath):
                    import shutil
                    shutil.rmtree(dirpath)
                    logger.debug(f"Directorio temporal eliminado: {dirpath}")
            except Exception as e:
                logger.warning(f"No se pudo eliminar directorio {dirpath}: {e}")
        
        # Limpiar cache de Python si es ejecutable
        if getattr(sys, 'frozen', False):
            try:
                import tempfile
                temp_dir = tempfile.gettempdir()
                eva_temp_pattern = os.path.join(temp_dir, "_MEI*")
                import glob
                for temp_path in glob.glob(eva_temp_pattern):
                    try:
                        if os.path.exists(temp_path):
                            import shutil
                            shutil.rmtree(temp_path)
                            logger.debug(f"Cache PyInstaller eliminado: {temp_path}")
                    except Exception:
                        pass  # Ignorar errores en limpieza de cache
            except Exception:
                pass  # Ignorar errores en limpieza general
    
    def _signal_handler(self, signum, frame):
        """Handler para señales del sistema"""
        logger.info(f"📡 Señal recibida: {signum}")
        self.shutdown_all(timeout=3.0, force_exit=True)
    
    def _emergency_cleanup(self):
        """Limpieza de emergencia al cerrar"""
        if not self._shutdown_initiated:
            logger.warning("🚨 Limpieza de emergencia activada")
            self.shutdown_all(timeout=1.0, force_exit=False)

# Instancia global
_global_registry: Optional[ThreadRegistry] = None

def get_thread_registry() -> ThreadRegistry:
    """Obtiene la instancia global del registro de hilos"""
    global _global_registry
    if _global_registry is None:
        _global_registry = ThreadRegistry()
    return _global_registry

def register_thread(name: str, 
                   thread: threading.Thread, 
                   stop_event: Optional[threading.Event] = None,
                   cleanup_callback: Optional[callable] = None):
    """Función de conveniencia para registrar hilos"""
    get_thread_registry().register_thread(name, thread, stop_event, cleanup_callback)

def shutdown_all_threads(timeout: float = 5.0):
    """Función de conveniencia para cerrar todos los hilos"""
    get_thread_registry().shutdown_all(timeout)