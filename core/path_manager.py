"""
EVA Path Manager - Centralized, Cross-Platform Path Management System
Handles all file paths dynamically with validation, fallbacks, and OS compatibility
"""

import os
import sys
import logging
import json
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("EVA")


class PathType(Enum):
    """Types of paths managed by the system"""
    RESOURCE = "resource"
    CONFIG = "config"
    DATA = "data"
    CACHE = "cache"
    LOG = "log"
    MODEL = "model"
    VOICE = "voice"
    PROGRAM = "program"
    USER_FOLDER = "user_folder"
    TEMP = "temp"


@dataclass
class PathConfig:
    """Configuration for a managed path"""
    path_type: PathType
    relative_path: str
    fallback_paths: List[str] = field(default_factory=list)
    create_if_missing: bool = False
    validate_exists: bool = True
    platform_specific: Dict[str, str] = field(default_factory=dict)
    description: str = ""


class PathManager:
    """
    Centralized path management system for EVA
    
    Features:
    - Cross-platform compatibility (Windows/Linux/macOS)
    - Dynamic path resolution with fallbacks
    - Environment variable support
    - Path validation and creation
    - Graceful error handling
    - Configuration-driven approach
    """
    
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or self._get_base_directory())
        self.config_file = self.base_dir / "config" / "paths.json"  # Usar archivo existente
        self.paths: Dict[str, PathConfig] = {}
        self.resolved_paths: Dict[str, Path] = {}
        
        # Initialize default path configurations
        self._init_default_paths()
        
        # Load configurations from existing paths.json
        self._load_existing_config()
        
        logger.info(f"PathManager initialized with base directory: {self.base_dir}")
    
    def _get_base_directory(self) -> str:
        """Get the application base directory"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return os.path.dirname(sys.executable)
        else:
            # Running as script
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def _init_default_paths(self):
        """Initialize default path configurations"""
        
        # Resource paths
        self.register_path("icon", PathConfig(
            path_type=PathType.RESOURCE,
            relative_path="resources/icon.ico",
            fallback_paths=["resources/icon.png", "_internal/resources/icon.ico"],
            description="Application icon file"
        ))
        
        self.register_path("splash_icon", PathConfig(
            path_type=PathType.RESOURCE,
            relative_path="resources/icon.png",
            fallback_paths=["resources/icon.ico", "_internal/resources/icon.png"],
            description="Splash screen icon"
        ))
        
        # Configuration paths
        self.register_path("main_config", PathConfig(
            path_type=PathType.CONFIG,
            relative_path="config/paths.json",
            create_if_missing=True,
            description="Main configuration file"
        ))
        
        # Model paths
        self.register_path("vosk_models", PathConfig(
            path_type=PathType.MODEL,
            relative_path="models/vosk",
            fallback_paths=["vosk", "_internal/vosk"],
            create_if_missing=True,
            description="Vosk speech recognition models"
        ))
        
        self.register_path("tts_voices", PathConfig(
            path_type=PathType.VOICE,
            relative_path="Voices",
            fallback_paths=["voices", "_internal/voices"],
            create_if_missing=True,
            description="TTS voice models directory"
        ))
        
        # Cache and data paths
        self.register_path("cache_dir", PathConfig(
            path_type=PathType.CACHE,
            relative_path=self._get_cache_directory(),
            create_if_missing=True,
            platform_specific={
                "windows": os.path.join(os.getenv('APPDATA', ''), 'EVA', 'cache'),
                "linux": os.path.expanduser("~/.cache/eva"),
                "darwin": os.path.expanduser("~/Library/Caches/EVA")
            },
            description="Application cache directory"
        ))
        
        # Log paths
        self.register_path("log_dir", PathConfig(
            path_type=PathType.LOG,
            relative_path=self._get_log_directory(),
            create_if_missing=True,
            platform_specific={
                "windows": os.path.join(os.getenv('APPDATA', ''), 'EVA', 'logs'),
                "linux": os.path.expanduser("~/.local/share/eva/logs"),
                "darwin": os.path.expanduser("~/Library/Logs/EVA")
            },
            description="Application log directory"
        ))
        
        # User data paths
        self.register_path("user_data", PathConfig(
            path_type=PathType.DATA,
            relative_path=self._get_user_data_directory(),
            create_if_missing=True,
            platform_specific={
                "windows": os.path.join(os.getenv('APPDATA', ''), 'EVA'),
                "linux": os.path.expanduser("~/.local/share/eva"),
                "darwin": os.path.expanduser("~/Library/Application Support/EVA")
            },
            description="User data directory"
        ))
        
        # Temporary paths
        self.register_path("temp_dir", PathConfig(
            path_type=PathType.TEMP,
            relative_path=tempfile.gettempdir(),
            description="System temporary directory"
        ))
        
        # External programs (platform-specific)
        self._init_program_paths()
    
    def _init_program_paths(self):
        """Initialize external program paths with cross-platform support"""
        
        programs = {
            "chrome": {
                "windows": [
                    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
                ],
                "linux": ["/usr/bin/google-chrome", "/usr/bin/chromium-browser"],
                "darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
            },
            "firefox": {
                "windows": [
                    "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
                    "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe"
                ],
                "linux": ["/usr/bin/firefox"],
                "darwin": ["/Applications/Firefox.app/Contents/MacOS/firefox"]
            },
            "vlc": {
                "windows": [
                    "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe",
                    "C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe"
                ],
                "linux": ["/usr/bin/vlc"],
                "darwin": ["/Applications/VLC.app/Contents/MacOS/VLC"]
            }
        }
        
        platform = self._get_platform()
        for program_name, paths in programs.items():
            platform_paths = paths.get(platform, [])
            if platform_paths:
                self.register_path(f"program_{program_name}", PathConfig(
                    path_type=PathType.PROGRAM,
                    relative_path=platform_paths[0],
                    fallback_paths=platform_paths[1:],
                    validate_exists=False,  # Programs may not be installed
                    description=f"{program_name.title()} executable"
                ))
    
    def _get_platform(self) -> str:
        """Get the current platform identifier"""
        if sys.platform.startswith('win'):
            return 'windows'
        elif sys.platform.startswith('linux'):
            return 'linux'
        elif sys.platform.startswith('darwin'):
            return 'darwin'
        else:
            return 'unknown'
    
    def _get_cache_directory(self) -> str:
        """Get platform-appropriate cache directory"""
        platform = self._get_platform()
        if platform == 'windows':
            return os.path.join(os.getenv('LOCALAPPDATA', os.getenv('APPDATA', '')), 'EVA', 'cache')
        elif platform == 'linux':
            return os.path.expanduser("~/.cache/eva")
        elif platform == 'darwin':
            return os.path.expanduser("~/Library/Caches/EVA")
        else:
            return os.path.join(tempfile.gettempdir(), 'eva_cache')
    
    def _get_log_directory(self) -> str:
        """Get platform-appropriate log directory"""
        platform = self._get_platform()
        if platform == 'windows':
            return os.path.join(os.getenv('APPDATA', ''), 'EVA', 'logs')
        elif platform == 'linux':
            return os.path.expanduser("~/.local/share/eva/logs")
        elif platform == 'darwin':
            return os.path.expanduser("~/Library/Logs/EVA")
        else:
            return os.path.join(tempfile.gettempdir(), 'eva_logs')
    
    def _get_user_data_directory(self) -> str:
        """Get platform-appropriate user data directory"""
        platform = self._get_platform()
        if platform == 'windows':
            return os.path.join(os.getenv('APPDATA', ''), 'EVA')
        elif platform == 'linux':
            return os.path.expanduser("~/.local/share/eva")
        elif platform == 'darwin':
            return os.path.expanduser("~/Library/Application Support/EVA")
        else:
            return os.path.join(os.path.expanduser("~"), '.eva')
    
    def register_path(self, name: str, config: PathConfig):
        """Register a new path configuration"""
        self.paths[name] = config
        logger.debug(f"Registered path '{name}': {config.relative_path}")
    
    def get_path(self, name: str, create_if_missing: Optional[bool] = None) -> Optional[Path]:
        """
        Get a resolved path by name
        
        Args:
            name: The registered path name
            create_if_missing: Override the default create_if_missing behavior
            
        Returns:
            Resolved Path object or None if not found/invalid
        """
        if name in self.resolved_paths:
            return self.resolved_paths[name]
        
        if name not in self.paths:
            logger.error(f"Path '{name}' not registered")
            return None
        
        config = self.paths[name]
        resolved_path = self._resolve_path(config)
        
        if resolved_path:
            # Handle creation if needed
            should_create = create_if_missing if create_if_missing is not None else config.create_if_missing
            if should_create and not resolved_path.exists():
                try:
                    if config.path_type in [PathType.CONFIG, PathType.DATA, PathType.CACHE, PathType.LOG, PathType.MODEL, PathType.VOICE]:
                        resolved_path.mkdir(parents=True, exist_ok=True)
                        logger.info(f"Created directory: {resolved_path}")
                except Exception as e:
                    logger.error(f"Failed to create directory {resolved_path}: {e}")
                    return None
            
            # Cache the resolved path
            self.resolved_paths[name] = resolved_path
            return resolved_path
        
        return None
    
    def _resolve_path(self, config: PathConfig) -> Optional[Path]:
        """Resolve a path configuration to an actual path"""
        
        # Check for platform-specific override
        platform = self._get_platform()
        if platform in config.platform_specific:
            platform_path = Path(config.platform_specific[platform])
            if self._validate_path(platform_path, config):
                return platform_path
        
        # Check environment variable override
        env_var = f"EVA_{config.path_type.value.upper()}_PATH"
        if env_var in os.environ:
            env_path = Path(os.environ[env_var])
            if self._validate_path(env_path, config):
                logger.info(f"Using environment override for {config.path_type.value}: {env_path}")
                return env_path
        
        # Try main path
        main_path = self.base_dir / config.relative_path
        if self._validate_path(main_path, config):
            return main_path
        
        # Try fallback paths
        for fallback in config.fallback_paths:
            fallback_path = self.base_dir / fallback
            if self._validate_path(fallback_path, config):
                logger.info(f"Using fallback path for {config.path_type.value}: {fallback_path}")
                return fallback_path
        
        # For programs, try system PATH
        if config.path_type == PathType.PROGRAM:
            program_name = Path(config.relative_path).stem
            system_path = self._find_in_system_path(program_name)
            if system_path:
                logger.info(f"Found {program_name} in system PATH: {system_path}")
                return system_path
        
        logger.warning(f"Could not resolve path for {config.path_type.value}: {config.relative_path}")
        return None
    
    def _validate_path(self, path: Path, config: PathConfig) -> bool:
        """Validate a path according to its configuration"""
        if not config.validate_exists:
            return True
        
        if config.path_type == PathType.PROGRAM:
            # For programs, check if executable exists and is executable
            return path.exists() and (path.is_file() or path.is_dir()) and os.access(path, os.X_OK)
        else:
            # For other types, just check existence (or allow creation)
            return path.exists() or config.create_if_missing
    
    def _find_in_system_path(self, program_name: str) -> Optional[Path]:
        """Find a program in the system PATH"""
        import shutil
        
        # Add common extensions on Windows
        if self._get_platform() == 'windows':
            extensions = ['.exe', '.bat', '.cmd']
            for ext in extensions:
                full_name = program_name + ext
                found = shutil.which(full_name)
                if found:
                    return Path(found)
        
        found = shutil.which(program_name)
        return Path(found) if found else None
    
    def get_user_folder_path(self, folder_name: str) -> Optional[Path]:
        """Get a user folder path (Documents, Downloads, etc.)"""
        user_folders = {
            'documents': self._get_documents_folder(),
            'downloads': self._get_downloads_folder(),
            'desktop': self._get_desktop_folder(),
            'pictures': self._get_pictures_folder(),
            'music': self._get_music_folder(),
            'videos': self._get_videos_folder()
        }
        
        folder_path = user_folders.get(folder_name.lower())
        if folder_path and folder_path.exists():
            return folder_path
        
        return None
    
    def _get_documents_folder(self) -> Path:
        """Get the user's Documents folder"""
        platform = self._get_platform()
        if platform == 'windows':
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                  r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as key:
                    documents = winreg.QueryValueEx(key, "Personal")[0]
                    return Path(documents)
            except Exception:
                pass
        
        return Path.home() / "Documents"
    
    def _get_downloads_folder(self) -> Path:
        """Get the user's Downloads folder"""
        return Path.home() / "Downloads"
    
    def _get_desktop_folder(self) -> Path:
        """Get the user's Desktop folder"""
        return Path.home() / "Desktop"
    
    def _get_pictures_folder(self) -> Path:
        """Get the user's Pictures folder"""
        return Path.home() / "Pictures"
    
    def _get_music_folder(self) -> Path:
        """Get the user's Music folder"""
        return Path.home() / "Music"
    
    def _get_videos_folder(self) -> Path:
        """Get the user's Videos folder"""
        return Path.home() / "Videos"
    
    def _load_existing_config(self):
        """Load path configurations from existing paths.json file"""
        if not self.config_file.exists():
            logger.warning(f"Configuration file not found: {self.config_file}")
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Load managed_paths section if it exists
            managed_paths = config_data.get('managed_paths', {})
            
            for name, config_dict in managed_paths.items():
                if 'path_type' in config_dict and 'relative_path' in config_dict:
                    try:
                        path_type = PathType(config_dict['path_type'])
                        config = PathConfig(
                            path_type=path_type,
                            relative_path=config_dict['relative_path'],
                            fallback_paths=config_dict.get('fallback_paths', []),
                            create_if_missing=config_dict.get('create_if_missing', False),
                            validate_exists=config_dict.get('validate_exists', True),
                            platform_specific=config_dict.get('platform_specific', {}),
                            description=config_dict.get('description', '')
                        )
                        self.register_path(name, config)
                    except ValueError as e:
                        logger.warning(f"Invalid path_type for {name}: {config_dict.get('path_type')} - {e}")
                        continue
            
            logger.info(f"Loaded {len(managed_paths)} path configurations from {self.config_file}")
            
            # Also load legacy paths for backward compatibility
            self._load_legacy_paths(config_data)
            
        except Exception as e:
            logger.error(f"Failed to load path configuration: {e}")
    
    def _load_legacy_paths(self, config_data):
        """Load legacy hardcoded paths and convert them to managed paths"""
        try:
            # Convert legacy program paths
            legacy_programs = config_data.get('paths', {}).get('programs', {})
            for program_name, program_path in legacy_programs.items():
                if f"program_{program_name}" not in self.paths:
                    config = PathConfig(
                        path_type=PathType.PROGRAM,
                        relative_path=program_path,
                        fallback_paths=[],
                        validate_exists=False,
                        description=f"Legacy program: {program_name}"
                    )
                    self.register_path(f"legacy_program_{program_name}", config)
            
            # Convert legacy folder paths
            legacy_folders = config_data.get('paths', {}).get('folders', {})
            for folder_name, folder_path in legacy_folders.items():
                if f"folder_{folder_name}" not in self.paths:
                    config = PathConfig(
                        path_type=PathType.USER_FOLDER,
                        relative_path=folder_path,
                        fallback_paths=[],
                        validate_exists=False,
                        description=f"Legacy folder: {folder_name}"
                    )
                    self.register_path(f"legacy_folder_{folder_name}", config)
            
            if legacy_programs or legacy_folders:
                logger.info(f"Loaded {len(legacy_programs)} legacy programs and {len(legacy_folders)} legacy folders")
                
        except Exception as e:
            logger.warning(f"Error loading legacy paths: {e}")
    
    def save_path_config(self):
        """Save current path configurations to existing paths.json file"""
        try:
            # Load existing configuration to preserve other settings
            existing_config = {}
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
            
            # Update only the managed_paths section
            managed_paths = {}
            for name, config in self.paths.items():
                # Skip legacy paths when saving
                if not name.startswith('legacy_'):
                    managed_paths[name] = {
                        'path_type': config.path_type.value,
                        'relative_path': config.relative_path,
                        'fallback_paths': config.fallback_paths,
                        'create_if_missing': config.create_if_missing,
                        'validate_exists': config.validate_exists,
                        'platform_specific': config.platform_specific,
                        'description': config.description
                    }
            
            # Update the managed_paths section while preserving other config
            existing_config['managed_paths'] = managed_paths
            
            # Ensure parent directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save the updated configuration
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(existing_config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(managed_paths)} managed paths to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save path configuration: {e}")
    
    def validate_all_paths(self) -> Dict[str, bool]:
        """Validate all registered paths and return results"""
        results = {}
        for name in self.paths:
            path = self.get_path(name)
            results[name] = path is not None and path.exists()
        
        return results
    
    def get_path_info(self, name: str) -> Optional[Dict]:
        """Get detailed information about a path"""
        if name not in self.paths:
            return None
        
        config = self.paths[name]
        resolved_path = self.get_path(name)
        
        return {
            'name': name,
            'type': config.path_type.value,
            'description': config.description,
            'configured_path': config.relative_path,
            'resolved_path': str(resolved_path) if resolved_path else None,
            'exists': resolved_path.exists() if resolved_path else False,
            'fallback_paths': config.fallback_paths,
            'platform_specific': config.platform_specific
        }
    
    def list_all_paths(self) -> List[Dict]:
        """List all registered paths with their information"""
        return [self.get_path_info(name) for name in self.paths.keys()]


# Global instance
_path_manager = None

def get_path_manager() -> PathManager:
    """Get the global PathManager instance"""
    global _path_manager
    if _path_manager is None:
        _path_manager = PathManager()
    return _path_manager

def get_path(name: str, create_if_missing: Optional[bool] = None) -> Optional[Path]:
    """Convenience function to get a path"""
    return get_path_manager().get_path(name, create_if_missing)

def get_user_folder(folder_name: str) -> Optional[Path]:
    """Convenience function to get a user folder path"""
    return get_path_manager().get_user_folder_path(folder_name)