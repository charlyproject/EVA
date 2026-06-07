"""
First-run wizard for EVA.
This module handles the first-run experience and configuration.
"""
import sys
import logging
from PySide6.QtWidgets import QApplication

from ui.first_run_dialog import NewFirstRunWizard
from utils.first_run import is_first_run, update_config

logger = logging.getLogger("EVA")

def create_language_manager():
    """
    Create and return a language manager instance.
    """
    from ui.first_run_dialog import TEXTS
    
    class LanguageManager:
        def __init__(self):
            self.current_lang = "en"  # Default to English
            self.texts = TEXTS
            
        def get_text(self, key, default=""):
            """Get text in the current language"""
            try:
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
    
    return LanguageManager()

def run_first_run_wizard():
    """
    Run the first-run wizard if this is the first time the application is launched.
    Returns True if the wizard completed successfully, False otherwise.
    """
    try:
        # Check if this is the first run
        if not is_first_run():
            return True
            
        logger.info("First run detected, launching configuration wizard...")
        
        # Get existing application (should already exist from main.py)
        app = QApplication.instance()
        if not app:
            logger.error("No QApplication instance found - this should not happen")
            app = QApplication(sys.argv)
        
        # Create language manager
        language_manager = create_language_manager()
        
        # Create and configure wizard
        wizard = NewFirstRunWizard(language_manager, parent=None)
        wizard.setWindowTitle("EVA - First Run Configuration")
        wizard.setModal(True)
        wizard.resize(700, 500)
        
        # Show wizard and wait for completion using exec() instead of app.exec()
        wizard.show()
        
        # Use wizard.exec() instead of app.exec() to avoid creating a nested event loop
        result = wizard.exec()
        
        # Check if wizard was completed
        # QDialog.exec() returns QDialog.Accepted (1) if accepted, QDialog.Rejected (0) if rejected
        if result == 1:  # QDialog.Accepted - User completed the wizard
            try:
                # Get configuration from wizard
                config = wizard.get_config()
                
                # Save configuration
                update_config({
                    'first_run': False,
                    'language': language_manager.current_lang,
                    'hardware': config.get('hardware', 'cpu'),
                    'model': config.get('model', 'default'),
                    'voice': config.get('voice', 'default'),
                    'cuda_available': config.get('cuda_available', False)
                })
                
                logger.info("✅ First run configuration completed successfully")
                return True
                
            except Exception as e:
                logger.error(f"Error saving first run configuration: {e}")
                return False
        else:
            logger.warning("❌ First run wizard was cancelled or rejected")
            return False
            
    except Exception as e:
        logger.error(f"Error in first run wizard: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the first run wizard
    success = run_first_run_wizard()
    
    if success:
        print("✅ First run configuration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Failed to complete first run configuration")
        sys.exit(1)
