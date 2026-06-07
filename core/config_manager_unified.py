import json
import os
import logging
from typing import Any, Dict
from config.config_validator import validate_full_config

logger = logging.getLogger("EVA")


class ConfigManager:
    """Unified configuration manager for EVA (singleton)"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._config_dir = "config"
        self._paths_file = os.path.join(self._config_dir, "paths.json")
        self._install_file = os.path.join(self._config_dir, "install_config.json")
        self._knowledge_file = "eva_knowledge_base.json"

        self._data: Dict[str, Any] = {}
        self._load_all()

    def _load_all(self):
        """Load and merge all config files"""
        # Load paths.json (main config)
        if os.path.exists(self._paths_file):
            try:
                with open(self._paths_file, 'r', encoding='utf-8') as f:
                    paths = json.load(f)
                    self._data.update(paths)
            except Exception as e:
                logger.error(f"Error loading paths.json: {e}")

        # Load install_config.json (hardware, user name)
        if os.path.exists(self._install_file):
            try:
                with open(self._install_file, 'r', encoding='utf-8') as f:
                    install = json.load(f)
                    self._data.update(install)
            except Exception as e:
                logger.error(f"Error loading install_config.json: {e}")

        # Load knowledge base (user preferences, shortcuts)
        if os.path.exists(self._knowledge_file):
            try:
                with open(self._knowledge_file, 'r', encoding='utf-8') as f:
                    knowledge = json.load(f)
                    self._data["knowledge_base"] = knowledge
            except Exception as e:
                logger.error(f"Error loading knowledge base: {e}")

        # Ensure nested structures exist to prevent KeyErrors
        self._data.setdefault("paths", {"programs": {}, "folders": {}, "websites": {}, "hotkeys": []})
        self._data.setdefault("ollama", {"model": "qwen3:4b", "timeout": 30})
        self._data.setdefault("tts", {})
        self._data.setdefault("vad", {})
        self._data.setdefault("updates", {})
        self._data.setdefault("plugins", {})
        self._data.setdefault("language", "es")
        self._data.setdefault("auto_listen", False)
        self._data.setdefault("sensitivity", 0.5)
        self._data.setdefault("knowledge_base", {})
        self._data.setdefault("ai_provider", "ollama")
        # Validate the full configuration using ConfigValidator
        self._data = validate_full_config(self._data)
        self._data.setdefault("openrouter", {"api_key": "", "model": "openrouter/free"})
        self._data.setdefault("use_mini_mode", False)
        self._data.setdefault("mini_bar_position", [])

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value by dot notation (e.g., 'ollama.model' or 'tts.volume')"""
        parts = key.split('.')
        value = self._data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
                if value is None:
                    return default
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """Set a config value by dot notation and auto-save"""
        parts = key.split('.')
        target = self._data
        for part in parts[:-1]:
            if part not in target or not isinstance(target[part], dict):
                target[part] = {}
            target = target[part]
        target[parts[-1]] = value
        self.save()

    def save(self):
        """Save main config to paths.json (knowledge_base is excluded, saved separately)"""
        try:
            os.makedirs(self._config_dir, exist_ok=True)
            to_save = {k: v for k, v in self._data.items() if k != "knowledge_base"}
            with open(self._paths_file, 'w', encoding='utf-8') as f:
                json.dump(to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def reload(self):
        """Reload all config files from disk"""
        self._load_all()

    def get_knowledge_base(self) -> dict:
        return self._data.get("knowledge_base", {})

    def update_knowledge_base(self, updates: dict):
        if "knowledge_base" not in self._data:
            self._data["knowledge_base"] = {}
        self._data["knowledge_base"].update(updates)
        try:
            with open(self._knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(self._data["knowledge_base"], f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")

    def migrate_old_configs(self):
        """One-shot migration: merges old config files, renames them to .bak"""
        migrated = False

        # Migrate install_config.json -> merge into _data
        bak_file = self._install_file + ".bak"
        if os.path.exists(self._install_file) and not os.path.exists(bak_file):
            try:
                with open(self._install_file, 'r', encoding='utf-8') as f:
                    install = json.load(f)
                self._data.update(install)
                os.rename(self._install_file, bak_file)
                logger.info(f"Migrated: {self._install_file} -> .bak")
                migrated = True
            except Exception as e:
                logger.error(f"Error migrating install_config.json: {e}")
        elif os.path.exists(self._install_file) and os.path.exists(bak_file):
            # Both exist - .bak was already created. Just remove the source.
            try:
                os.remove(self._install_file)
                logger.info(f"Removed already-migrated: {self._install_file}")
                migrated = True
            except Exception as e:
                logger.warning(f"Could not remove already-migrated config: {e}")

        # Migrate paths.json if it existed before (already loaded, just ensure format)
        # Save unified config
        if migrated:
            self.save()
            logger.info("Config migration complete")

    def get_ollama_config(self) -> dict:
        return self._data.get("ollama", {})

    def get_tts_config(self) -> dict:
        return self._data.get("tts", {})

    def get_vad_config(self) -> dict:
        return self._data.get("vad", {})

    def get_update_config(self) -> dict:
        return self._data.get("updates", {})

    def get_plugins_config(self) -> dict:
        return self._data.get("plugins", {})


# Global singleton instance
config_manager = ConfigManager()
