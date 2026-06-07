"""
Dynamic Path Resolver for EVA
Eliminates all hardcoded paths and provides portable path resolution for EXE deployment
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional
import tempfile
import platform

logger = logging.getLogger("EVA")

class DynamicPathResolver:
    """
    Centralized path resolution system for EVA
    Automatically detects runtime environment and resolves all paths dynamically
    """
    
    def __init__(self):
        self._base_dir = self._detect_base_directory()
        self._is_frozen = getattr(sys, 'frozen', False)
        self._platform = platform.system().lower()
        self._paths_cache = {}
        self._config_cache = {}
        
        # Initialize path mappings
        self._init_path_mappings()
        
        logger.info("Dynamic Path Resolver initialized:")
        logger.info(f"  Base Directory: {self._base_dir}")
        logger.info(f"  Is Frozen (EXE): {self._is_frozen}")
        logger.info(f"  Platform: {self._platform}")
    
    def _detect_base_directory(self) -> str:
        """Detect the base directory dynamically"""
        if getattr(sys, 'frozen', False):
            # Running as EXE - use executable directory
            base_dir = os.path.dirname(sys.executable)
            # Ensure we're in the correct directory for EVA
            if os.path.exists(os.path.join(base_dir, 'config')):
                return base_dir
            # If config not found, try parent directory
            parent_dir = os.path.dirname(base_dir)
            if os.path.exists(os.path.join(parent_dir, 'config')):
                return parent_dir
            return base_dir
        else:
            # Running as script - get project root
            current_file = os.path.abspath(__file__)
            current_dir = os.path.dirname(current_file)
            # Go up one level from core/ to get project root
            project_root = os.path.dirname(current_dir)
            return project_root
    
    def _init_path_mappings(self):
        """Initialize dynamic path mappings"""
        self._path_mappings = {
            # Core application paths
            'base': self._base_dir,
            'config': self._resolve_config_dir(),
            'models': self._resolve_models_dir(),
            'voices': self._resolve_voices_dir(),
            'resources': self._resolve_resources_dir(),
            'logs': self._resolve_logs_dir(),
            'cache': self._resolve_cache_dir(),
            'temp': self._resolve_temp_dir(),
            'data': self._resolve_data_dir(),
            
            # External tools
            'ffmpeg': self._resolve_ffmpeg_path(),
            'ollama': self._resolve_ollama_path(),
            
            # User directories
            'user_home': self._resolve_user_home(),
            'user_documents': self._resolve_user_documents(),
            'user_downloads': self._resolve_user_downloads(),
            'user_desktop': self._resolve_user_desktop(),
        }
    
    def _resolve_config_dir(self) -> str:
        """Resolve config directory"""
        candidates = [
            os.path.join(self._base_dir, "config"),
            os.path.join(self._base_dir, "_internal", "config"),
        ]
        return self._find_existing_path(candidates, create_if_missing=True)
    
    def _resolve_models_dir(self) -> str:
        """Resolve models directory"""
        candidates = [
            os.path.join(self._base_dir, "models"),
            os.path.join(self._base_dir, "_internal", "models"),
        ]
        return self._find_existing_path(candidates, create_if_missing=True)
    
    def _resolve_voices_dir(self) -> str:
        """Resolve voices directory"""
        candidates = [
            os.path.join(self._base_dir, "voices"),
            os.path.join(self._base_dir, "Voices"),
            os.path.join(self._base_dir, "_internal", "voices"),
        ]
        return self._find_existing_path(candidates, create_if_missing=False)  # No crear - Piper TTS usa piper/models/
    
    def _resolve_resources_dir(self) -> str:
        """Resolve resources directory"""
        candidates = [
            os.path.join(self._base_dir, "resources"),
            os.path.join(self._base_dir, "_internal", "resources"),
        ]
        return self._find_existing_path(candidates, create_if_missing=True)
    
    def _resolve_logs_dir(self) -> str:
        """Resolve logs directory"""
        if self._platform == 'windows':
            appdata = os.getenv('APPDATA')
            if appdata:
                logs_dir = os.path.join(appdata, 'EVA', 'logs')
                os.makedirs(logs_dir, exist_ok=True)
                return logs_dir
        
        # Fallback to local directory
        logs_dir = os.path.join(self._base_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        return logs_dir
    
    def _resolve_cache_dir(self) -> str:
        """Resolve cache directory"""
        if self._platform == 'windows':
            appdata = os.getenv('LOCALAPPDATA') or os.getenv('APPDATA')
            if appdata:
                cache_dir = os.path.join(appdata, 'EVA', 'cache')
                os.makedirs(cache_dir, exist_ok=True)
                return cache_dir
        elif self._platform == 'linux':
            cache_dir = os.path.expanduser("~/.cache/eva")
            os.makedirs(cache_dir, exist_ok=True)
            return cache_dir
        elif self._platform == 'darwin':
            cache_dir = os.path.expanduser("~/Library/Caches/EVA")
            os.makedirs(cache_dir, exist_ok=True)
            return cache_dir
        
        # Fallback to local directory
        cache_dir = os.path.join(self._base_dir, "cache")
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir
    
    def _resolve_temp_dir(self) -> str:
        """Resolve temporary directory"""
        return tempfile.gettempdir()
    
    def _resolve_data_dir(self) -> str:
        """Resolve data directory"""
        if self._platform == 'windows':
            appdata = os.getenv('APPDATA')
            if appdata:
                data_dir = os.path.join(appdata, 'EVA', 'data')
                os.makedirs(data_dir, exist_ok=True)
                return data_dir
        
        # Fallback to local directory
        data_dir = os.path.join(self._base_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        return data_dir
    
    def _resolve_ffmpeg_path(self) -> str:
        """Resolve FFmpeg executable path"""
        candidates = [
            os.path.join(self._base_dir, "ffmpeg", "bin", "ffmpeg.exe" if self._platform == 'windows' else "ffmpeg"),
            os.path.join(self._base_dir, "_internal", "ffmpeg", "bin", "ffmpeg.exe" if self._platform == 'windows' else "ffmpeg"),
        ]
        
        # Add system PATH search
        system_ffmpeg = self._find_in_system_path("ffmpeg.exe" if self._platform == 'windows' else "ffmpeg")
        if system_ffmpeg:
            candidates.append(system_ffmpeg)
        
        return self._find_existing_path(candidates)
    
    def _resolve_ollama_path(self) -> str:
        """Resolve Ollama executable path (shutil.which -> config -> bundled -> PATH)"""
        import shutil

        # 1. shutil.which (sistema PATH)
        exe_name = "ollama.exe" if self._platform == 'windows' else "ollama"
        system_ollama = shutil.which(exe_name)
        if system_ollama:
            return system_ollama

        # 2. Fallbacks desde managed_paths en config/paths.json
        config_fallbacks = self._get_managed_fallback_paths("program_ollama")
        if config_fallbacks:
            found = self._find_existing_path(config_fallbacks)
            if found:
                return found

        # 3. Bundled ollama (EVA portable)
        candidates = [
            os.path.join(self._base_dir, "ollama", exe_name),
            os.path.join(self._base_dir, "_internal", "ollama", exe_name),
        ]
        found = self._find_existing_path(candidates)
        if found:
            return found

        # 4. Fallback final: buscar en PATH manualmente
        return self._find_in_system_path(exe_name) or ""
    
    def _resolve_user_home(self) -> str:
        """Resolve user home directory"""
        return os.path.expanduser("~")
    
    def _resolve_user_documents(self) -> str:
        """Resolve user documents directory"""
        if self._platform == 'windows':
            return os.path.join(os.path.expanduser("~"), "Documents")
        else:
            return os.path.join(os.path.expanduser("~"), "Documents")
    
    def _resolve_user_downloads(self) -> str:
        """Resolve user downloads directory"""
        return os.path.join(os.path.expanduser("~"), "Downloads")
    
    def _resolve_user_desktop(self) -> str:
        """Resolve user desktop directory"""
        return os.path.join(os.path.expanduser("~"), "Desktop")
    
    def _find_existing_path(self, candidates: List[str], create_if_missing: bool = False) -> str:
        """Find first existing path from candidates"""
        for path in candidates:
            if os.path.exists(path):
                return path
        
        # If no existing path found, return first candidate
        first_candidate = candidates[0] if candidates else ""
        
        if create_if_missing and first_candidate:
            os.makedirs(first_candidate, exist_ok=True)
        
        return first_candidate
    
    def _find_in_system_path(self, executable: str) -> Optional[str]:
        """Find executable in system PATH"""
        for path in os.environ.get("PATH", "").split(os.pathsep):
            full_path = os.path.join(path, executable)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return full_path
        return None

    def _get_managed_fallback_paths(self, managed_key: str) -> list:
        """Lee fallback_paths de managed_paths en config/paths.json"""
        try:
            config_path = self.get_config_file('paths')
            if not os.path.exists(config_path):
                return []
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            managed = data.get("managed_paths", {}).get(managed_key, {})
            raw_paths = managed.get("fallback_paths", [])
            return [os.path.expandvars(p) for p in raw_paths]
        except Exception as e:
            logger.debug(f"Error leyendo managed_paths '{managed_key}': {e}")
            return []
    
    def get_path(self, path_key: str, *sub_paths) -> str:
        """Get resolved path by key with optional sub-paths"""
        if path_key in self._paths_cache:
            base_path = self._paths_cache[path_key]
        elif path_key in self._path_mappings:
            base_path = self._path_mappings[path_key]
            self._paths_cache[path_key] = base_path
        else:
            logger.warning(f"Unknown path key: {path_key}")
            return ""
        
        if sub_paths:
            return os.path.join(base_path, *sub_paths)
        return base_path
    
    def get_vosk_model_path(self, language: str = "es") -> str:
        """Get Vosk model path for specific language"""
        # Definir los nombres de los modelos por idioma
        model_names = {
            "es": "vosk-model-small-es-0.42",
            "en": "vosk-model-small-en-us-0.15"
        }
        model_name = model_names.get(language, model_names["es"])
        
        # 1. Buscar en la ruta estándar del proyecto
        models_dir = self.get_path('models', 'vosk')
        model_path = os.path.join(models_dir, model_name)
        if os.path.exists(model_path):
            logger.info(f"Modelo Vosk encontrado en ruta estándar: {model_path}")
            return model_path
        
        # 2. Buscar en AppData/Local/EVA/models/vosk (para instalaciones de usuario)
        local_appdata = os.environ.get('LOCALAPPDATA', '')
        local_eva_models = os.path.join(local_appdata, 'EVA', 'models', 'vosk')
        local_model_path = os.path.join(local_eva_models, model_name)
        if os.path.exists(local_model_path):
            logger.info(f"Modelo Vosk encontrado en AppData: {local_model_path}")
            return local_model_path
            
        # 3. Buscar en el directorio _internal (para instalaciones portátiles)
        internal_models_dir = os.path.join(self._base_dir, '_internal', 'models', 'vosk')
        internal_model_path = os.path.join(internal_models_dir, model_name)
        if os.path.exists(internal_model_path):
            logger.info(f"Modelo Vosk encontrado en directorio _internal: {internal_model_path}")
            return internal_model_path
            
        # 4. Buscar cualquier modelo en AppData/Local/EVA/models/vosk
        if os.path.exists(local_eva_models):
            for item in os.listdir(local_eva_models):
                if not os.path.isdir(os.path.join(local_eva_models, item)):
                    continue
                if "vosk-model" in item:
                    item_path = os.path.join(local_eva_models, item)
                    logger.warning(f"Usando modelo Vosk alternativo en AppData: {item}")
                    return item_path
        
        # 5. Buscar cualquier modelo en la ruta estándar
        if os.path.exists(models_dir):
            for item in os.listdir(models_dir):
                if not os.path.isdir(os.path.join(models_dir, item)):
                    continue
                if "vosk-model" in item:
                    item_path = os.path.join(models_dir, item)
                    logger.warning(f"Usando modelo Vosk alternativo: {item}")
                    return item_path
        
        # 6. Buscar en el directorio raíz del ejecutable
        exe_dir = os.path.dirname(sys.executable) if hasattr(sys, 'frozen') else self._base_dir
        exe_models_dir = os.path.join(exe_dir, 'models', 'vosk')
        exe_model_path = os.path.join(exe_models_dir, model_name)
        if os.path.exists(exe_model_path):
            logger.info(f"Modelo Vosk encontrado en directorio del ejecutable: {exe_model_path}")
            return exe_model_path
        
        # 7. Si no se encuentra ningún modelo, devolver la ruta esperada
        expected_path = os.path.join(models_dir, model_name)
        logger.error(f"No se encontró ningún modelo Vosk para el idioma: {language}")
        logger.error("Se buscó en:")
        logger.error(f"- {model_path}")
        logger.error(f"- {local_model_path}")
        logger.error(f"- {internal_model_path}")
        logger.error(f"- {exe_model_path}")
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(expected_path), exist_ok=True)
        return expected_path  # Devolver la ruta esperada incluso si no existe
    
    def get_piper_model_path(self, language: str = "es", quality: str = "medium") -> str:
        """Get Piper TTS model path"""
        models_dir = self.get_path('models', 'piper')
        
        model_files = {
            "es": f"es_ES-sharvard-{quality}.onnx",
            "en": f"en_US-kristin-{quality}.onnx"
        }
        
        model_file = model_files.get(language, model_files["es"])
        return os.path.join(models_dir, model_file)
    
    def get_ollama_models_dir(self) -> str:
        """Get Ollama models directory"""
        return self.get_path('models', 'ollama', 'models')
    
    def get_config_file(self, config_name: str) -> str:
        """Get configuration file path"""
        config_files = {
            'paths': 'paths.json',
            'install': 'install_config.json',
            'lang_es': 'lang_es.json',
            'lang_en': 'lang_en.json',
            'session': 'session.dat',
            'update_state': 'update_state.json',
            'user_preferences': 'user_preferences.json'
        }
        
        filename = config_files.get(config_name, f"{config_name}.json")
        return self.get_path('config', filename)
    
    def get_resource_file(self, resource_name: str) -> str:
        """Get resource file path"""
        return self.get_path('resources', resource_name)
    
    def get_icon_path(self, icon_type: str = "ico") -> str:
        """Get application icon path"""
        icon_files = {
            'ico': 'icon.ico',
            'png': 'icon.png'
        }
        
        filename = icon_files.get(icon_type, 'icon.ico')
        return self.get_resource_file(filename)
    
    def get_log_file(self, log_name: str = "eva_debug.log") -> str:
        """Get log file path"""
        return self.get_path('logs', log_name)
    
    def get_cache_dir(self, cache_type: str = "") -> str:
        """Get cache directory path"""
        if cache_type:
            return self.get_path('cache', cache_type)
        return self.get_path('cache')
    
    def get_temp_file(self, filename: str) -> str:
        """Get temporary file path"""
        return os.path.join(self.get_path('temp'), filename)
    
    def resolve_external_program(self, program_name: str) -> Optional[str]:
        """Resolve external program path"""
        if self._platform == 'windows':
            program_paths = {
                'chrome': [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                ],
                'firefox': [
                    r"C:\Program Files\Mozilla Firefox\firefox.exe",
                    r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
                ],
                'vlc': [
                    r"C:\Program Files\VideoLAN\VLC\vlc.exe",
                    r"C:\Program Files (x86)\VideoLAN\VLC\vlc.exe"
                ]
            }
            
            if program_name in program_paths:
                return self._find_existing_path(program_paths[program_name])
        
        # Fallback to system PATH
        exe_name = f"{program_name}.exe" if self._platform == 'windows' else program_name
        return self._find_in_system_path(exe_name)
    
    def create_portable_config(self) -> Dict:
        """Create portable configuration with all resolved paths"""
        return {
            "eva_info": {
                "version": "1.0",
                "portable": True,
                "platform": self._platform,
                "is_frozen": self._is_frozen
            },
            "paths": {
                "base": self.get_path('base'),
                "config": self.get_path('config'),
                "models": self.get_path('models'),
                "voices": self.get_path('voices'),
                "resources": self.get_path('resources'),
                "logs": self.get_path('logs'),
                "cache": self.get_path('cache'),
                "data": self.get_path('data'),
                "temp": self.get_path('temp')
            },
            "external_tools": {
                "ffmpeg": self.get_path('ffmpeg'),
                "ollama": self.get_path('ollama')
            },
            "user_directories": {
                "home": self.get_path('user_home'),
                "documents": self.get_path('user_documents'),
                "downloads": self.get_path('user_downloads'),
                "desktop": self.get_path('user_desktop')
            }
        }
    
    def save_portable_config(self, config_file: Optional[str] = None):
        """Save portable configuration to file"""
        if not config_file:
            config_file = self.get_config_file('portable_paths')
        
        config = self.create_portable_config()
        
        try:
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Portable configuration saved to: {config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving portable config: {str(e)}")
            return False

# Global instance
dynamic_path_resolver = DynamicPathResolver()