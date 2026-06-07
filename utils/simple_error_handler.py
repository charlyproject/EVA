"""
Simplified Error Handler for EVA
Replaces the overengineered EnhancedErrorHandler with a clean, functional approach
"""

import logging
import traceback
import functools
from typing import Callable, Any
from datetime import datetime

logger = logging.getLogger("EVA")

class SimpleErrorHandler:
    """Simplified error handling with basic recovery and logging"""
    
    def __init__(self, eva_instance=None):
        self.eva = eva_instance
        self.error_count = 0
        self.last_error_time = None
        
    def handle_error(self, error: Exception, context: str = "", notify_user: bool = True):
        """Handle an error with logging and optional user notification"""
        try:
            self.error_count += 1
            self.last_error_time = datetime.now()
            
            error_msg = f"Error in {context}: {str(error)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            
            # Notify user for critical errors
            if notify_user and hasattr(self.eva, 'chat_window'):
                user_msg = f"❌ Error: {str(error)}"
                self.eva.chat_window.add_message(user_msg, is_user=False)
                
        except Exception as e:
            logger.critical(f"Error in error handler: {str(e)}")
    
    def safe_execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function safely with error handling"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.handle_error(e, f"executing {func.__name__}")
            return None
    
    def cleanup(self):
        """Simple cleanup"""
        logger.info(f"Error handler processed {self.error_count} errors")

def error_handler(context: str = ""):
    """Decorator for automatic error handling"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {context or func.__name__}: {str(e)}")
                logger.debug(traceback.format_exc())
                return None
        return wrapper
    return decorator

# Global instance
simple_error_handler = SimpleErrorHandler()