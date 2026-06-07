"""
Utility functions for handling first-run detection and configuration.
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger("EVA")

CONFIG_DIR = Path.home() / ".eva"
CONFIG_FILE = CONFIG_DIR / "config.json"

def is_first_run():
    """
    Check if this is the first run of the application.
    Returns True only on the very first run, False otherwise.
    """
    try:
        logger.info(f"🔍 Checking first run - Config dir: {CONFIG_DIR}")
        logger.info(f"🔍 Checking first run - Config file: {CONFIG_FILE}")
        
        # Check if config directory exists
        if not CONFIG_DIR.exists():
            logger.info("✅ First run: Config directory doesn't exist")
            return True
            
        # Check if config file exists
        if not CONFIG_FILE.exists():
            logger.info("✅ First run: Config file doesn't exist")
            return True
            
        # Try to read config file
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # Check first_run flag
            if config.get('first_run', True):
                logger.info("First run: First run flag is True")
                return True
                
            # Verify the installation is complete
            if not config.get('installation_complete', False):
                logger.info("First run: Installation not marked as complete")
                return True
                
            logger.info("Not first run: All checks passed")
            return False
            
        except json.JSONDecodeError:
            logger.warning("Config file is corrupted, treating as first run")
            return True
            
    except Exception as e:
        logger.error(f"Error in is_first_run: {e}", exc_info=True)
        return True  # Default to first run if there's an error

def mark_first_run_complete():
    """
    Mark the first run and installation as complete by updating the config file.
    This should only be called after the first run wizard has completed successfully.
    """
    try:
        import time
        
        logger.info(f"🔧 Marking first run complete - Config dir: {CONFIG_DIR}")
        logger.info(f"🔧 Marking first run complete - Config file: {CONFIG_FILE}")
        
        # Create config directory if it doesn't exist
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Config directory created/verified: {CONFIG_DIR}")
        
        # Create or update config
        config = {
            'first_run': False,
            'installation_complete': True,
            'installation_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'version': '1.0'  # Add version for future compatibility
        }
        logger.info(f"📝 Config to save: {config}")
        
        # If config exists, load it first to preserve other settings
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
                    # Update only the necessary fields
                    config.update({
                        k: v for k, v in existing_config.items() 
                        if k not in ['first_run', 'installation_complete', 'installation_date']
                    })
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Error reading existing config: {e}, creating new config")
        
        # Save the updated config
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        
        logger.info("✅ First run and installation marked as complete")
        logger.info(f"💾 Config file saved successfully: {CONFIG_FILE}")
        
        # Verify the file was created
        if CONFIG_FILE.exists():
            logger.info(f"✅ Verification: Config file exists with size {CONFIG_FILE.stat().st_size} bytes")
        else:
            logger.error("❌ ERROR: Config file was not created!")
            
        return True
        
    except Exception as e:
        logger.error(f"Error in mark_first_run_complete: {e}", exc_info=True)
        return False

def get_config():
    """
    Get the current configuration.
    Returns a dictionary with the current configuration.
    """
    try:
        if not CONFIG_FILE.exists():
            return {}
            
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    except Exception as e:
        logger.error(f"Error reading config: {e}")
        return {}

def update_config(updates):
    """
    Update the configuration with the given values.
    
    Args:
        updates (dict): Dictionary of configuration values to update.
    """
    try:
        # Create config directory if it doesn't exist
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load existing config or create new one
        config = {}
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        # Update with new values
        config.update(updates)
        
        # Save config
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
            
    except Exception as e:
        logger.error(f"Error updating configuration: {e}")
