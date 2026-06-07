"""
Enhanced Voice Assistant v.1.0 - Sistema Centralizado de Manejo de Errores
Proporciona manejo consistente y robusto de errores en todo el sistema
"""

import logging
import traceback
from typing import Dict, Any
from enum import Enum

logger = logging.getLogger("EVA")


class ErrorSeverity(Enum):
    """Niveles de severidad de errores"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categorías de errores del sistema"""
    TTS_ERROR = "tts_error"
    MEMORY_ERROR = "memory_error"
    HARDWARE_ERROR = "hardware_error"
    NETWORK_ERROR = "network_error"
    FILE_ERROR = "file_error"
    OLLAMA_ERROR = "ollama_error"
    VOICE_ERROR = "voice_error"
    CONFIG_ERROR = "config_error"
    UNKNOWN_ERROR = "unknown_error"


class CentralizedErrorHandler:
    """Manejador centralizado de errores para EVA"""
    
    def __init__(self):
        self.error_handlers = {}
        self.error_stats = {
            'total_errors': 0,
            'errors_by_category': {},
            'errors_by_severity': {},
            'recent_errors': []
        }
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Registra manejadores de error por defecto"""
        self.error_handlers[ErrorCategory.TTS_ERROR] = self._handle_tts_error
        self.error_handlers[ErrorCategory.MEMORY_ERROR] = self._handle_memory_error
        self.error_handlers[ErrorCategory.HARDWARE_ERROR] = self._handle_hardware_error
        self.error_handlers[ErrorCategory.NETWORK_ERROR] = self._handle_network_error
        self.error_handlers[ErrorCategory.FILE_ERROR] = self._handle_file_error
        self.error_handlers[ErrorCategory.OLLAMA_ERROR] = self._handle_ollama_error
        self.error_handlers[ErrorCategory.VOICE_ERROR] = self._handle_voice_error
        self.error_handlers[ErrorCategory.CONFIG_ERROR] = self._handle_config_error
    
    def handle_error(self, 
                    error: Exception, 
                    category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                    context: str = "",
                    auto_recover: bool = True) -> Dict[str, Any]:
        """
        Maneja un error de forma centralizada
        
        Args:
            error: La excepción a manejar
            category: Categoría del error
            severity: Severidad del error
            context: Contexto adicional del error
            auto_recover: Si debe intentar recuperación automática
            
        Returns:
            Dict con información del manejo del error
        """
        try:
            # Actualizar estadísticas
            self._update_error_stats(category, severity, error, context)
            
            # Log del error
            error_msg = f"{context}: {str(error)}" if context else str(error)
            
            if severity == ErrorSeverity.CRITICAL:
                logger.critical(f"CRITICAL ERROR [{category.value}]: {error_msg}")
                logger.critical(f"Traceback: {traceback.format_exc()}")
            elif severity == ErrorSeverity.HIGH:
                logger.error(f"HIGH ERROR [{category.value}]: {error_msg}")
            elif severity == ErrorSeverity.MEDIUM:
                logger.warning(f"MEDIUM ERROR [{category.value}]: {error_msg}")
            else:
                logger.info(f"LOW ERROR [{category.value}]: {error_msg}")
            
            # Ejecutar manejador específico
            recovery_result = None
            if auto_recover and category in self.error_handlers:
                try:
                    recovery_result = self.error_handlers[category](error, context)
                except Exception as handler_error:
                    logger.error(f"Error en manejador de {category.value}: {str(handler_error)}")
            
            return {
                'handled': True,
                'category': category.value,
                'severity': severity.value,
                'recovery_attempted': auto_recover,
                'recovery_result': recovery_result,
                'error_message': error_msg
            }
            
        except Exception as e:
            logger.error(f"Error en manejador centralizado de errores: {str(e)}")
            return {
                'handled': False,
                'error': str(e)
            }
    
    def _update_error_stats(self, category: ErrorCategory, severity: ErrorSeverity, error: Exception, context: str):
        """Actualiza estadísticas de errores"""
        self.error_stats['total_errors'] += 1
        
        # Por categoría
        if category.value not in self.error_stats['errors_by_category']:
            self.error_stats['errors_by_category'][category.value] = 0
        self.error_stats['errors_by_category'][category.value] += 1
        
        # Por severidad
        if severity.value not in self.error_stats['errors_by_severity']:
            self.error_stats['errors_by_severity'][severity.value] = 0
        self.error_stats['errors_by_severity'][severity.value] += 1
        
        # Errores recientes (mantener últimos 10)
        error_record = {
            'category': category.value,
            'severity': severity.value,
            'error': str(error),
            'context': context,
            'timestamp': __import__('time').time()
        }
        
        self.error_stats['recent_errors'].append(error_record)
        if len(self.error_stats['recent_errors']) > 10:
            self.error_stats['recent_errors'].pop(0)
    
    # MANEJADORES ESPECÍFICOS DE ERROR
    
    def _handle_tts_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Maneja errores de TTS con recuperación automática"""
        error_str = str(error).lower()
        
        if "cuda" in error_str or "gpu" in error_str:
            logger.info("Error de GPU en TTS - cambiando a CPU")
            return {'action': 'fallback_to_cpu', 'device': 'cpu'}
        
        elif "memory" in error_str or "out of memory" in error_str:
            logger.info("Error de memoria en TTS - liberando memoria")
            try:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                # REMOVED: unified_memory_manager (deprecated system)
                pass  # Skip deprecated import
            except ImportError:
                logger.debug("Sistema unificado de memoria no disponible")
            
            # REMOVED: All unified_memory_manager logic (deprecated system)
            try:
                import gc
                gc.collect()
                return {'action': 'basic_cleanup', 'success': True}
            except Exception as e:
                logger.error(f"Error during basic cleanup: {e}")
                return {'action': 'basic_cleanup', 'success': False}
        
        elif "model" in error_str or "file not found" in error_str:
            logger.info("Error de modelo en TTS - usando fallback")
            return {'action': 'use_fallback_voice', 'fallback': 'system_voice'}
        
        return {'action': 'log_only'}
    
    def _handle_memory_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Maneja errores de memoria"""
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            # REMOVED: unified_memory_manager (deprecated system)
            import gc
            gc.collect()  # Simple fallback cleanup
            
            # REMOVED: unified_memory_manager calls (deprecated system)
            try:
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
                import gc
                gc.collect()
                return {'action': 'basic_cleanup'}
            except Exception:
                import gc
                gc.collect()
                return {'action': 'basic_cleanup'}
                
        except ImportError:
            logger.debug("Sistema unificado de memoria no disponible")
            return {'action': 'memory_manager_unavailable'}
        except Exception as e:
            logger.error(f"Error en limpieza forzada: {str(e)}")
            return {'action': 'cleanup_failed', 'error': str(e)}
    
    def _handle_hardware_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Maneja errores de hardware"""
        error_str = str(error).lower()
        
        if "cuda" in error_str:
            return {'action': 'disable_cuda', 'fallback': 'cpu'}
        elif "gpu" in error_str:
            return {'action': 'disable_gpu', 'fallback': 'cpu'}
        
        return {'action': 'log_only'}
    
    def _handle_network_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Maneja errores de red"""
        if "timeout" in str(error).lower():
            return {'action': 'retry_with_longer_timeout'}
        elif "connection" in str(error).lower():
            return {'action': 'check_connection'}
        
        return {'action': 'log_only'}
    
    def _handle_file_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Maneja errores de archivos"""
        error_str = str(error).lower()
        
        if "not found" in error_str:
            return {'action': 'create_missing_file'}
        elif "permission" in error_str:
            return {'action': 'check_permissions'}
        
        return {'action': 'log_only'}
    
    def _handle_ollama_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Maneja errores de Ollama"""
        error_str = str(error).lower()
        
        if "connection" in error_str or "refused" in error_str:
            return {'action': 'ollama_not_running', 'message': 'Ollama no está ejecutándose'}
        elif "model" in error_str:
            return {'action': 'model_not_available', 'message': 'Modelo no disponible'}
        
        return {'action': 'log_only'}
    
    def _handle_voice_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Maneja errores de reconocimiento de voz"""
        return {'action': 'restart_voice_engine'}
    
    def _handle_config_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Maneja errores de configuración"""
        return {'action': 'reset_to_defaults'}
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de errores"""
        return self.error_stats.copy()
    
    def clear_error_stats(self):
        """Limpia estadísticas de errores"""
        self.error_stats = {
            'total_errors': 0,
            'errors_by_category': {},
            'errors_by_severity': {},
            'recent_errors': []
        }
        logger.info("Estadísticas de errores limpiadas")


# Instancia global del manejador de errores
centralized_error_handler = CentralizedErrorHandler()


# FUNCIONES DE CONVENIENCIA PARA USO FÁCIL

def handle_error(error: Exception, 
                category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR,
                severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                context: str = "",
                auto_recover: bool = True) -> Dict[str, Any]:
    """Función de conveniencia para manejar errores"""
    return centralized_error_handler.handle_error(error, category, severity, context, auto_recover)


def handle_tts_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """Maneja errores específicos de TTS"""
    return handle_error(error, ErrorCategory.TTS_ERROR, ErrorSeverity.MEDIUM, context)


def handle_memory_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """Maneja errores específicos de memoria"""
    return handle_error(error, ErrorCategory.MEMORY_ERROR, ErrorSeverity.HIGH, context)


def handle_ollama_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """Maneja errores específicos de Ollama"""
    return handle_error(error, ErrorCategory.OLLAMA_ERROR, ErrorSeverity.MEDIUM, context)


def handle_critical_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """Maneja errores críticos del sistema"""
    return handle_error(error, ErrorCategory.UNKNOWN_ERROR, ErrorSeverity.CRITICAL, context)
