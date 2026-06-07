"""
Factory Pattern para Comandos de EVA
Sistema dinámico y extensible para crear y gestionar handlers de comandos
"""

import logging
import re
import threading
from typing import Dict, List, Type, Optional, Any, Pattern
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
import importlib
import inspect

logger = logging.getLogger("EVA")

class CommandPriority(Enum):
    """Prioridades de comandos"""
    CRITICAL = 0    # Comandos del sistema críticos
    HIGH = 1        # Comandos importantes del usuario
    NORMAL = 2      # Comandos estándar
    LOW = 3         # Comandos de conveniencia
    FALLBACK = 4    # Handlers de fallback

class CommandScope(Enum):
    """Ámbito de aplicación de comandos"""
    GLOBAL = "global"       # Disponible siempre
    CONTEXT = "context"     # Disponible en contexto específico
    SESSION = "session"     # Disponible durante la sesión
    PREMIUM = "premium"     # Solo para usuarios premium

@dataclass
class CommandPattern:
    """Patrón de comando con metadatos"""
    pattern: Pattern[str]
    handler_class: Type
    priority: CommandPriority
    scope: CommandScope
    description: str
    examples: List[str]
    requires_premium: bool = False
    context_required: Optional[str] = None
    enabled: bool = True

class ICommandHandler(ABC):
    """Interfaz base para handlers de comandos"""
    
    def __init__(self, processor):
        self.processor = processor
        self.config = processor.config
        self.language_manager = processor.language_manager
        self.session_manager = processor.session_manager
    
    @abstractmethod
    def can_handle(self, text: str) -> bool:
        """Verifica si puede manejar el comando"""
        pass
    
    @abstractmethod
    def handle(self, text: str, chat_window) -> bool:
        """Maneja el comando"""
        pass
    
    @abstractmethod
    def get_patterns(self) -> List[str]:
        """Retorna patrones que puede manejar"""
        pass
    
    def get_priority(self) -> CommandPriority:
        """Retorna la prioridad del handler"""
        return CommandPriority.NORMAL
    
    def get_scope(self) -> CommandScope:
        """Retorna el ámbito del handler"""
        return CommandScope.GLOBAL
    
    def requires_premium(self) -> bool:
        """Indica si requiere licencia premium"""
        return False
    
    def get_description(self) -> str:
        """Retorna descripción del handler"""
        return self.__class__.__name__
    
    def get_examples(self) -> List[str]:
        """Retorna ejemplos de uso"""
        return []

class CommandFactory:
    """
    Factory dinámico para crear y gestionar handlers de comandos
    """
    
    def __init__(self, processor):
        self.processor = processor
        self._lock = threading.RLock()
        
        # Registro de patrones y handlers
        self._patterns: List[CommandPattern] = []
        self._handler_classes: Dict[str, Type[ICommandHandler]] = {}
        self._handler_instances: Dict[str, ICommandHandler] = {}
        
        # Cache de matching para optimización
        self._pattern_cache: Dict[str, Optional[CommandPattern]] = {}
        self._cache_max_size = 1000
        
        # Configuración
        self.config = {
            'enable_caching': True,
            'auto_reload_handlers': False,
            'max_handler_instances': 50,
            'pattern_timeout': 5.0,  # Timeout para regex complejos
            'enable_fuzzy_matching': True,
            'fuzzy_threshold': 0.8
        }
        
        # Estadísticas
        self.stats = {
            'total_patterns': 0,
            'total_handlers': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'commands_processed': 0,
            'failed_matches': 0,
            'avg_match_time': 0.0
        }
        
        # Contexto actual
        self._current_context: Optional[str] = None
        self._context_stack: List[str] = []
        
        logger.info("CommandFactory inicializado")
    
    def register_handler(self, 
                        handler_class: Type[ICommandHandler],
                        patterns: Optional[List[str]] = None,
                        priority: CommandPriority = CommandPriority.NORMAL,
                        scope: CommandScope = CommandScope.GLOBAL,
                        description: str = "",
                        examples: Optional[List[str]] = None) -> bool:
        """
        Registra un handler de comandos
        
        Args:
            handler_class: Clase del handler
            patterns: Patrones regex opcionales (si no se especifican, se obtienen del handler)
            priority: Prioridad del handler
            scope: Ámbito de aplicación
            description: Descripción del handler
            examples: Ejemplos de uso
            
        Returns:
            True si se registró exitosamente
        """
        with self._lock:
            try:
                # Validar handler
                if not issubclass(handler_class, ICommandHandler):
                    logger.error(f"Handler {handler_class.__name__} no implementa ICommandHandler")
                    return False
                
                # Crear instancia temporal para obtener información
                temp_instance = handler_class(self.processor)
                
                # Obtener patrones
                if patterns is None:
                    patterns = temp_instance.get_patterns()
                
                if not patterns:
                    logger.warning(f"Handler {handler_class.__name__} no tiene patrones definidos")
                    return False
                
                # Obtener metadatos del handler
                handler_priority = temp_instance.get_priority()
                handler_scope = temp_instance.get_scope()
                handler_description = description or temp_instance.get_description()
                handler_examples = examples or temp_instance.get_examples()
                requires_premium = temp_instance.requires_premium()
                
                # Registrar cada patrón
                handler_name = handler_class.__name__
                self._handler_classes[handler_name] = handler_class
                
                for pattern_str in patterns:
                    try:
                        # Compilar patrón regex
                        compiled_pattern = re.compile(pattern_str, re.IGNORECASE)
                        
                        # Crear registro de patrón
                        pattern_obj = CommandPattern(
                            pattern=compiled_pattern,
                            handler_class=handler_class,
                            priority=handler_priority,
                            scope=handler_scope,
                            description=handler_description,
                            examples=handler_examples,
                            requires_premium=requires_premium
                        )
                        
                        self._patterns.append(pattern_obj)
                        
                    except re.error as e:
                        logger.error(f"Error compilando patrón '{pattern_str}': {str(e)}")
                        continue
                
                # Ordenar patrones por prioridad
                self._patterns.sort(key=lambda p: p.priority.value)
                
                # Limpiar cache
                self._pattern_cache.clear()
                
                # Actualizar estadísticas
                self.stats['total_patterns'] = len(self._patterns)
                self.stats['total_handlers'] = len(self._handler_classes)
                
                logger.info(f"Handler {handler_name} registrado con {len(patterns)} patrones")
                return True
                
            except Exception as e:
                logger.error(f"Error registrando handler {handler_class.__name__}: {str(e)}")
                return False
    
    def unregister_handler(self, handler_class: Type[ICommandHandler]) -> bool:
        """Desregistra un handler de comandos"""
        with self._lock:
            try:
                handler_name = handler_class.__name__
                
                if handler_name not in self._handler_classes:
                    logger.warning(f"Handler {handler_name} no está registrado")
                    return False
                
                # Remover patrones asociados
                self._patterns = [p for p in self._patterns if p.handler_class != handler_class]
                
                # Remover de registros
                del self._handler_classes[handler_name]
                
                if handler_name in self._handler_instances:
                    del self._handler_instances[handler_name]
                
                # Limpiar cache
                self._pattern_cache.clear()
                
                # Actualizar estadísticas
                self.stats['total_patterns'] = len(self._patterns)
                self.stats['total_handlers'] = len(self._handler_classes)
                
                logger.info(f"Handler {handler_name} desregistrado")
                return True
                
            except Exception as e:
                logger.error(f"Error desregistrando handler: {str(e)}")
                return False
    
    def create_handler(self, command: str) -> Optional[ICommandHandler]:
        """
        Crea un handler apropiado para un comando
        
        Args:
            command: Comando de texto
            
        Returns:
            Handler apropiado o None si no se encuentra
        """
        import time
        start_time = time.time()
        
        with self._lock:
            try:
                # Verificar cache primero
                if self.config['enable_caching'] and command in self._pattern_cache:
                    pattern = self._pattern_cache[command]
                    if pattern:
                        handler = self._get_handler_instance(pattern.handler_class)
                        self.stats['cache_hits'] += 1
                        return handler
                    else:
                        self.stats['cache_misses'] += 1
                        return None
                
                # Buscar patrón coincidente
                matching_pattern = self._find_matching_pattern(command)
                
                if matching_pattern:
                    # Verificar restricciones
                    if not self._check_handler_restrictions(matching_pattern):
                        self.stats['failed_matches'] += 1
                        return None
                    
                    # Crear/obtener instancia del handler
                    handler = self._get_handler_instance(matching_pattern.handler_class)
                    
                    # Actualizar cache
                    if self.config['enable_caching']:
                        self._update_cache(command, matching_pattern)
                    
                    self.stats['cache_misses'] += 1
                    return handler
                
                # No se encontró patrón
                if self.config['enable_caching']:
                    self._update_cache(command, None)
                
                self.stats['failed_matches'] += 1
                return None
                
            except Exception as e:
                logger.error(f"Error creando handler para '{command}': {str(e)}")
                return None
            
            finally:
                # Actualizar estadísticas de tiempo
                execution_time = time.time() - start_time
                self._update_avg_match_time(execution_time)
                self.stats['commands_processed'] += 1
    
    def _find_matching_pattern(self, command: str) -> Optional[CommandPattern]:
        """Busca un patrón que coincida con el comando"""
        import signal
        
        # Función para timeout de regex
        def timeout_handler(signum, frame):
            raise TimeoutError("Regex timeout")
        
        for pattern_obj in self._patterns:
            try:
                # Verificar si está habilitado
                if not pattern_obj.enabled:
                    continue
                
                # Verificar ámbito
                if not self._check_scope(pattern_obj.scope):
                    continue
                
                # Configurar timeout para regex complejos
                if self.config['pattern_timeout'] > 0:
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(int(self.config['pattern_timeout']))
                
                try:
                    # Intentar match
                    if pattern_obj.pattern.search(command):
                        return pattern_obj
                finally:
                    if self.config['pattern_timeout'] > 0:
                        signal.alarm(0)  # Cancelar timeout
                
            except TimeoutError:
                logger.warning(f"Timeout en patrón: {pattern_obj.pattern.pattern}")
                continue
            except Exception as e:
                logger.error(f"Error evaluando patrón: {str(e)}")
                continue
        
        # Intentar matching difuso si está habilitado
        if self.config['enable_fuzzy_matching']:
            return self._fuzzy_match(command)
        
        return None
    
    def _fuzzy_match(self, command: str) -> Optional[CommandPattern]:
        """Intenta matching difuso con patrones conocidos"""
        try:
            from rapidfuzz import fuzz, process
            
            # Obtener ejemplos de todos los patrones
            examples = []
            pattern_map = {}
            
            for pattern_obj in self._patterns:
                if not pattern_obj.enabled or not self._check_scope(pattern_obj.scope):
                    continue
                
                for example in pattern_obj.examples:
                    examples.append(example)
                    pattern_map[example] = pattern_obj
            
            if not examples:
                return None
            
            # Buscar mejor coincidencia
            result = process.extractOne(
                command, 
                examples, 
                scorer=fuzz.token_set_ratio
            )
            
            if result and result[1] >= (self.config['fuzzy_threshold'] * 100):
                best_match = result[0]
                return pattern_map[best_match]
            
        except ImportError:
            logger.debug("rapidfuzz no disponible para matching difuso")
        except Exception as e:
            logger.error(f"Error en matching difuso: {str(e)}")
        
        return None
    
    def _check_scope(self, scope: CommandScope) -> bool:
        """Verifica si el ámbito del comando es válido"""
        if scope == CommandScope.GLOBAL:
            return True
        elif scope == CommandScope.PREMIUM:
            return self.processor.session_manager.is_premium()
        elif scope == CommandScope.CONTEXT:
            return self._current_context is not None
        elif scope == CommandScope.SESSION:
            return self.processor.session_manager.can_operate()
        
        return True
    
    def _check_handler_restrictions(self, pattern: CommandPattern) -> bool:
        """Verifica restricciones del handler"""
        # Sin restricciones premium: todos los handlers disponibles
        
        # Verificar contexto
        if pattern.context_required and self._current_context != pattern.context_required:
            logger.debug(f"Handler requiere contexto {pattern.context_required}")
            return False
        
        return True
    
    def _get_handler_instance(self, handler_class: Type[ICommandHandler]) -> ICommandHandler:
        """Obtiene o crea una instancia del handler"""
        handler_name = handler_class.__name__
        
        if handler_name not in self._handler_instances:
            # Verificar límite de instancias
            if len(self._handler_instances) >= self.config['max_handler_instances']:
                # Remover instancia menos usada (simplificado)
                oldest_handler = next(iter(self._handler_instances))
                del self._handler_instances[oldest_handler]
            
            # Crear nueva instancia
            self._handler_instances[handler_name] = handler_class(self.processor)
        
        return self._handler_instances[handler_name]
    
    def _update_cache(self, command: str, pattern: Optional[CommandPattern]):
        """Actualiza el cache de patrones"""
        if len(self._pattern_cache) >= self._cache_max_size:
            # Limpiar cache (FIFO simple)
            oldest_key = next(iter(self._pattern_cache))
            del self._pattern_cache[oldest_key]
        
        self._pattern_cache[command] = pattern
    
    def _update_avg_match_time(self, execution_time: float):
        """Actualiza tiempo promedio de matching"""
        total_commands = self.stats['commands_processed']
        if total_commands > 1:
            self.stats['avg_match_time'] = (
                (self.stats['avg_match_time'] * (total_commands - 1) + execution_time) 
                / total_commands
            )
        else:
            self.stats['avg_match_time'] = execution_time
    
    def set_context(self, context: str):
        """Establece el contexto actual"""
        with self._lock:
            if self._current_context:
                self._context_stack.append(self._current_context)
            self._current_context = context
            logger.debug(f"Contexto establecido: {context}")
    
    def pop_context(self) -> Optional[str]:
        """Restaura el contexto anterior"""
        with self._lock:
            old_context = self._current_context
            
            if self._context_stack:
                self._current_context = self._context_stack.pop()
            else:
                self._current_context = None
            
            logger.debug(f"Contexto restaurado: {self._current_context}")
            return old_context
    
    def clear_context(self):
        """Limpia todo el contexto"""
        with self._lock:
            self._current_context = None
            self._context_stack.clear()
            logger.debug("Contexto limpiado")
    
    def get_available_commands(self, 
                              scope: Optional[CommandScope] = None,
                              premium_only: bool = False) -> List[Dict[str, Any]]:
        """Obtiene lista de comandos disponibles"""
        commands = []
        
        with self._lock:
            for pattern_obj in self._patterns:
                if not pattern_obj.enabled:
                    continue
                
                if scope and pattern_obj.scope != scope:
                    continue
                
                if premium_only and not pattern_obj.requires_premium:
                    continue
                
                if not self._check_scope(pattern_obj.scope):
                    continue
                
                commands.append({
                    'pattern': pattern_obj.pattern.pattern,
                    'handler': pattern_obj.handler_class.__name__,
                    'priority': pattern_obj.priority.value,
                    'scope': pattern_obj.scope.value,
                    'description': pattern_obj.description,
                    'examples': pattern_obj.examples,
                    'requires_premium': pattern_obj.requires_premium
                })
        
        return commands
    
    def reload_handlers(self):
        """Recarga todos los handlers dinámicamente"""
        if not self.config['auto_reload_handlers']:
            logger.warning("Recarga automática de handlers deshabilitada")
            return
        
        with self._lock:
            try:
                # Limpiar instancias existentes
                self._handler_instances.clear()
                
                # Recargar módulos de handlers
                for handler_name, handler_class in self._handler_classes.items():
                    module = inspect.getmodule(handler_class)
                    if module:
                        importlib.reload(module)
                
                logger.info("Handlers recargados dinámicamente")
                
            except Exception as e:
                logger.error(f"Error recargando handlers: {str(e)}")
    
    def enable_pattern(self, pattern_str: str, enabled: bool = True):
        """Habilita/deshabilita un patrón específico"""
        with self._lock:
            for pattern_obj in self._patterns:
                if pattern_obj.pattern.pattern == pattern_str:
                    pattern_obj.enabled = enabled
                    logger.info(f"Patrón '{pattern_str}' {'habilitado' if enabled else 'deshabilitado'}")
                    break
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del factory"""
        with self._lock:
            return {
                'config': self.config.copy(),
                'stats': self.stats.copy(),
                'current_context': self._current_context,
                'context_stack_depth': len(self._context_stack),
                'cache_size': len(self._pattern_cache),
                'active_handlers': len(self._handler_instances)
            }
    
    def clear_cache(self):
        """Limpia el cache de patrones"""
        with self._lock:
            self._pattern_cache.clear()
            logger.info("Cache de patrones limpiado")


# Instancia global del factory de comandos
command_factory = CommandFactory(None)  # Se inicializará con el processor real