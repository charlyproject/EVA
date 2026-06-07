"""
Simple Resource Manager for EVA
Replaces complex resource management with basic functionality
"""

import logging
import threading
from typing import Dict, Any, Optional

logger = logging.getLogger("EVA")

class SimpleResourceManager:
    """Simplified resource management for EVA"""
    
    def __init__(self, eva_instance=None):
        self.eva = eva_instance
        self._lock = threading.RLock()
        self._resources: Dict[str, Any] = {}
        self._running = False
        
    def start(self):
        """Start resource manager"""
        with self._lock:
            self._running = True
            logger.info("Simple resource manager started")
    
    def stop(self):
        """Stop resource manager"""
        with self._lock:
            self._running = False
            # Clean up any resources
            for name, resource in self._resources.items():
                try:
                    if hasattr(resource, 'cleanup'):
                        resource.cleanup()
                    elif hasattr(resource, 'close'):
                        resource.close()
                except Exception as e:
                    logger.warning(f"Error cleaning up resource {name}: {str(e)}")
            
            self._resources.clear()
            logger.info("Simple resource manager stopped")
    
    def register_resource(self, name: str, resource: Any):
        """Register a resource for management"""
        with self._lock:
            self._resources[name] = resource
            logger.debug(f"Resource registered: {name}")
    
    def unregister_resource(self, name: str):
        """Unregister a resource"""
        with self._lock:
            if name in self._resources:
                del self._resources[name]
                logger.debug(f"Resource unregistered: {name}")
    
    def get_resource(self, name: str) -> Optional[Any]:
        """Get a registered resource"""
        with self._lock:
            return self._resources.get(name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get resource statistics"""
        with self._lock:
            return {
                'total_resources': len(self._resources),
                'resource_names': list(self._resources.keys()),
                'running': self._running
            }

# Global instance
simple_resource_manager = SimpleResourceManager()