#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de prueba independiente para el Wizard de Primera Ejecución de EVA
Permite probar el wizard sin ejecutar toda la aplicación
"""

import sys
import os
import logging

# Agregar el directorio de EVA al path
eva_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, eva_dir)

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("EVA_WIZARD_TEST")

def setup_qt_environment():
    """Configura el entorno Qt para el wizard"""
    try:
        # Configurar variables de entorno para Qt
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
        os.environ["QT_SCALE_FACTOR"] = "1.0"
        os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
        os.environ["QT_SCREEN_SCALE_FACTORS"] = "1.0"
        os.environ["QT_QPA_PLATFORM"] = "windows"
        os.environ["QT_OPENGL"] = "software"
        
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        
        # Configurar atributos Qt
        QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, False)
        QApplication.setAttribute(Qt.AA_UseDesktopOpenGL, False)
        QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)
        QApplication.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings, True)
        
        logger.info("✅ Entorno Qt configurado correctamente")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error configurando entorno Qt: {e}")
        return False

def create_mock_language_manager():
    """Create a mock language manager for the wizard that uses the proper translation system"""
    from ui.first_run_dialog import TEXTS
    
    class MockLanguageManager:
        def __init__(self):
            self.current_lang = "en"  # Default to English
            self.texts = TEXTS
            
        def get_text(self, key, default=""):
            """Get text in the current language"""
            try:
                # Try to get the text in the current language
                return self.texts.get(self.current_lang, {}).get(key, default)
            except Exception as e:
                logger.error(f"Error getting text for key '{key}': {e}")
                return default
                
        def set_language(self, lang):
            """Set the current language"""
            if lang in self.texts:
                self.current_lang = lang
                return True
            return False
    
    return MockLanguageManager()

import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="module")
def qt_app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # No podemos destruir QApplication fácilmente en PySide6
    # pero aseguramos que esté limpio para el siguiente uso si es posible.

def run_wizard_test_logic(app):
    """Main function to test the wizard"""
    try:
        logger.info("🚀 Starting EVA Wizard test...")
        
        # 1. Setup Qt environment
        if not setup_qt_environment():
            return False
        
        # 2. Use existing app
        app.setApplicationName("EVA Wizard Test")
        
        logger.info("✅ Qt application prepared")
        
        # 3. Create language manager with proper translation system
        language_manager = create_mock_language_manager()
        
        # Set initial language to English
        language_manager.set_language("en")
        logger.info("✅ Language manager initialized with English translations")
        
        # 4. Import and create the wizard
        from ui.first_run_dialog import NewFirstRunWizard
        wizard = NewFirstRunWizard(language_manager, parent=None)
        
        logger.info("✅ Wizard created successfully")
        
        # 5. Configure the wizard
        wizard.setWindowTitle("EVA - Wizard Test")
        wizard.setModal(True)
        wizard.resize(700, 500)  # Slightly larger size for better visualization
        
        # 6. Show the wizard
        logger.info("📋 Showing wizard...")
        wizard.show()
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("💡 Make sure PySide6 is installed: pip install PySide6")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error running wizard: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_wizard(qt_app):
    """Pytest wrapper for the wizard test"""
    assert run_wizard_test_logic(qt_app) is True

def main():
    """Main entry point"""
    print("🧙‍♂️ EVA Wizard Test")
    print("="*30)
    print("This script tests the EVA initial configuration wizard")
    print("independently, without needing to run the entire application.\n")
    
    try:
        success = test_wizard()
        
        if success:
            print("\n✅ Wizard test completed successfully!")
        else:
            print("\n❌ Error during wizard test")
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
        return 0
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())