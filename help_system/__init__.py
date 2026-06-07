"""
Sistema de Ayuda Interactivo para EVA
====================================

Este módulo proporciona un sistema de ayuda guiada con navegación por menús,
búsqueda inteligente y soporte bilingüe (español/inglés).

Componentes principales:
- HelpManager: Controlador principal del sistema
- HelpNavigator: Navegación por menús interactivos
- HelpSearcher: Búsqueda inteligente en el contenido
- HelpHandler: Integración con el sistema de comandos de EVA
"""

from .help_manager import HelpManager
from .help_navigator import HelpNavigator
from .help_search import HelpSearcher

__version__ = "1.0.0"
__author__ = "EVA Team"

__all__ = [
    "HelpManager",
    "HelpNavigator", 
    "HelpSearcher"
]