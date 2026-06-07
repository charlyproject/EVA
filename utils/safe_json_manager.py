#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Safe JSON Manager para EVA
Sistema de protección automática contra archivos JSON corruptos
"""

import json
import os
import shutil
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("EVA")

class SafeJSONManager:
    """Gestor seguro de archivos JSON con backup automático"""
    
    def __init__(self, file_path: str, default_template: Dict[str, Any] = None):
        self.file_path = file_path
        self.default_template = default_template or {}
        self.backup_dir = os.path.join(os.path.dirname(file_path), "backups")
        
        # Crear directorio de backups si no existe
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def load_or_create(self) -> Dict[str, Any]:
        """
        Carga JSON o crea desde template si está corrupto/faltante
        
        Returns:
            Dict con los datos del JSON
        """
        # 1. Intentar cargar archivo principal
        data = self._try_load_file(self.file_path)
        if data is not None:
            return data
        
        # 2. Si falla, crear desde template
        logger.warning(f"Creando {self.file_path} desde template")
        return self._create_from_template()
    
    def _try_load_file(self, path: str) -> Optional[Dict[str, Any]]:
        """Intenta cargar un archivo JSON de forma segura"""
        try:
            # Verificar que existe y no está vacío
            if not os.path.exists(path) or os.path.getsize(path) == 0:
                return None
                
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Validar que es un diccionario
            if not isinstance(data, dict):
                logger.error(f"JSON no es un diccionario: {path}")
                return None
                
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON corrupto: {path} - {str(e)}")
            self._backup_corrupted_file(path)
            return None
        except Exception as e:
            logger.error(f"Error leyendo {path}: {str(e)}")
            return None
    
    def _backup_corrupted_file(self, path: str):
        """Crea backup de archivo corrupto"""
        try:
            if os.path.exists(path):
                timestamp = int(time.time())
                filename = os.path.basename(path)
                backup_path = os.path.join(self.backup_dir, f"{filename}.corrupted.{timestamp}")
                
                shutil.copy2(path, backup_path)
                logger.info(f"✅ Backup de archivo corrupto creado: {backup_path}")
                
        except Exception as e:
            logger.warning(f"No se pudo crear backup de archivo corrupto: {str(e)}")
    
    def _create_from_template(self) -> Dict[str, Any]:
        """Crea archivo nuevo desde template"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # Escribir template
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.default_template, f, ensure_ascii=False, indent=4)
            
            logger.info(f"✅ Archivo creado desde template: {self.file_path}")
            return self.default_template.copy()
            
        except Exception as e:
            logger.error(f"Error creando desde template: {str(e)}")
            return self.default_template.copy()
    
    def save(self, data: Dict[str, Any]):
        """Guarda datos de forma segura"""
        try:
            # Crear backup del archivo actual si existe y es válido
            if os.path.exists(self.file_path):
                current_data = self._try_load_file(self.file_path)
                if current_data is not None:
                    self._create_backup(current_data)
            
            # Guardar nuevos datos
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            logger.debug(f"Archivo guardado: {self.file_path}")
                
        except Exception as e:
            logger.error(f"Error guardando archivo {self.file_path}: {str(e)}")
    
    def _create_backup(self, data: Dict[str, Any]):
        """Crea backup automático de datos válidos"""
        try:
            timestamp = int(time.time())
            filename = os.path.basename(self.file_path)
            backup_path = os.path.join(self.backup_dir, f"{filename}.backup.{timestamp}")
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            # Mantener solo los últimos 5 backups
            self._cleanup_old_backups(filename)
            
        except Exception as e:
            logger.warning(f"No se pudo crear backup: {str(e)}")
    
    def _cleanup_old_backups(self, filename: str):
        """Mantiene solo los últimos 5 backups"""
        try:
            backup_pattern = f"{filename}.backup."
            backups = []
            
            for file in os.listdir(self.backup_dir):
                if file.startswith(backup_pattern):
                    backup_path = os.path.join(self.backup_dir, file)
                    timestamp = os.path.getmtime(backup_path)
                    backups.append((timestamp, backup_path))
            
            # Ordenar por timestamp y mantener solo los últimos 5
            backups.sort(reverse=True)
            for _, backup_path in backups[5:]:
                os.remove(backup_path)
                logger.debug(f"Backup antiguo eliminado: {backup_path}")
                
        except Exception as e:
            logger.warning(f"Error limpiando backups antiguos: {str(e)}")


# Función de utilidad para uso directo
def safe_load_json(file_path: str, default_content: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función de utilidad para cargar JSON de forma segura
    Compatible con el código existente de EVA
    """
    manager = SafeJSONManager(file_path, default_content)
    return manager.load_or_create()


def safe_save_json(file_path: str, data: Dict[str, Any]):
    """
    Función de utilidad para guardar JSON de forma segura
    """
    manager = SafeJSONManager(file_path)
    manager.save(data)


# Templates por defecto para archivos críticos de EVA
DEFAULT_TEMPLATES = {
    "paths.json": {
        "language": "es",
        "paths": {
            "programs": {},
            "folders": {},
            "websites": {}
        },
        "settings": {
            "font_size": 12,
            "theme": "default"
        }
    },
    
    "install_config.json": {
        "hardware_type": "cpu",
        "user_name": "Usuario",
        "user_avatar": "default_avatar.png",
        "language": "es"
    },
    
    "update_state.json": {
        "last_check": None,
        "current_version": "1.0.0",
        "skipped_versions": [],
        "auto_check": True,
        "check_interval": 21600
    },
    
    "eva_knowledge_base.json": {
        "user_profile": {
            "name": "Usuario",
            "greeting_preference": "auto",
            "preferred_model": "phi3:mini",
            "mute_mode": False,
            "timezone": "Europe/Madrid",
            "work_hours": "09:00-18:00"
        },
        "usage_analytics": {
            "most_used_commands": {},
            "active_hours": {"morning": 0, "afternoon": 0, "evening": 0, "night": 0},
            "total_sessions": 0,
            "last_session": None
        },
        "command_history": {
            "last_commands": [],
            "max_history": 5
        },
        "context_memory": {
            "last_topic": None,
            "last_document": None,
            "last_question": None,
            "last_response": None,
            "conversation_context": []
        },
        "custom_shortcuts": {},
        "preferences": {
            "favorite_programs": [],
            "frequent_folders": [],
            "preferred_language": "es",
            "auto_suggestions": True,
            "contextual_greetings": True
        },
        "learning_data": {
            "command_patterns": {},
            "time_patterns": {},
            "topic_interests": {}
        }
    }
}


def get_safe_json_manager(file_path: str) -> SafeJSONManager:
    """
    Factory function para crear SafeJSONManager con template apropiado
    """
    filename = os.path.basename(file_path)
    template = DEFAULT_TEMPLATES.get(filename, {})
    return SafeJSONManager(file_path, template)