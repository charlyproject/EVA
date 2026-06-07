#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Backup y Rollback para EVA
Protege los datos del usuario durante actualizaciones
"""

import shutil
import json
import logging
import zipfile
from datetime import datetime
from pathlib import Path

logger = logging.getLogger('EVA.BackupManager')

class BackupManager:
    """Gestor de backups para proteger datos durante actualizaciones"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.backup_dir = self.base_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        # Archivos y directorios críticos a respaldar
        self.critical_paths = [
            "config/",
            "eva_knowledge_base.json",
            "eva_knowledge.db",
            "__version__.py",
            "cache/user_data/",
            "Voices/custom/",  # Voces personalizadas del usuario
        ]
        
        # Archivos de configuración específicos
        self.config_files = [
            "config/config.json",
            "config/install_config.json",
            "config/session.dat",
            "config/update_state.json",
            "config/user_preferences.json"
        ]
        
        logger.info(f"BackupManager inicializado - Directorio: {self.backup_dir}")
    
    def create_backup(self, version, backup_type="update"):
        """
        Crea un backup completo antes de una actualización
        
        Args:
            version (str): Versión actual antes del update
            backup_type (str): Tipo de backup ('update', 'manual', 'auto')
            
        Returns:
            str: Ruta del backup creado o None si falló
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"eva_v{version}_{backup_type}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            logger.info(f"Creando backup: {backup_name}")
            
            # Crear directorio de backup
            backup_path.mkdir(exist_ok=True)
            
            # Información del backup
            backup_info = {
                "version": version,
                "backup_type": backup_type,
                "timestamp": timestamp,
                "created_at": datetime.now().isoformat(),
                "files_backed_up": [],
                "total_size": 0,
                "status": "in_progress"
            }
            
            total_size = 0
            files_backed_up = []
            
            # Backup de archivos y directorios críticos
            for path_str in self.critical_paths:
                src_path = self.base_dir / path_str
                
                if src_path.exists():
                    dst_path = backup_path / path_str
                    
                    try:
                        if src_path.is_dir():
                            # Copiar directorio completo
                            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                            size = self._get_directory_size(dst_path)
                            logger.info(f"Directorio copiado: {path_str} ({size} bytes)")
                        else:
                            # Copiar archivo individual
                            dst_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src_path, dst_path)
                            size = dst_path.stat().st_size
                            logger.info(f"Archivo copiado: {path_str} ({size} bytes)")
                        
                        files_backed_up.append(path_str)
                        total_size += size
                        
                    except Exception as e:
                        logger.warning(f"Error copiando {path_str}: {str(e)}")
                else:
                    logger.info(f"Ruta no existe, omitiendo: {path_str}")
            
            # Backup adicional de archivos de configuración específicos
            for config_file in self.config_files:
                src_path = self.base_dir / config_file
                if src_path.exists() and config_file not in files_backed_up:
                    dst_path = backup_path / config_file
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dst_path)
                    size = dst_path.stat().st_size
                    files_backed_up.append(config_file)
                    total_size += size
                    logger.info(f"Config copiado: {config_file} ({size} bytes)")
            
            # Actualizar información del backup
            backup_info.update({
                "files_backed_up": files_backed_up,
                "total_size": total_size,
                "status": "completed",
                "completed_at": datetime.now().isoformat()
            })
            
            # Guardar información del backup
            info_file = backup_path / "backup_info.json"
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(backup_info, f, indent=2, ensure_ascii=False)
            
            # Crear archivo ZIP comprimido para ahorrar espacio
            zip_path = self._create_compressed_backup(backup_path)
            
            logger.info(f"Backup completado: {backup_name} ({total_size} bytes, {len(files_backed_up)} archivos)")
            
            # Limpiar backups antiguos
            self._cleanup_old_backups()
            
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Error creando backup: {str(e)}")
            backup_info["status"] = "failed"
            backup_info["error"] = str(e)
            
            # Intentar guardar info de error
            try:
                info_file = backup_path / "backup_info.json"
                with open(info_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_info, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error writing backup info file: {e}")
                pass
            
            return None
    
    def _create_compressed_backup(self, backup_path):
        """Crea una versión comprimida del backup"""
        try:
            zip_path = backup_path.with_suffix('.zip')
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in backup_path.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(backup_path)
                        zipf.write(file_path, arcname)
            
            # Verificar que el ZIP se creó correctamente
            if zip_path.exists() and zip_path.stat().st_size > 0:
                # Eliminar directorio original para ahorrar espacio
                shutil.rmtree(backup_path)
                logger.info(f"Backup comprimido creado: {zip_path.name}")
                return zip_path
            
        except Exception as e:
            logger.error(f"Error creando backup comprimido: {str(e)}")
        
        return backup_path
    
    def restore_backup(self, backup_path):
        """
        Restaura un backup específico
        
        Args:
            backup_path (str): Ruta del backup a restaurar
            
        Returns:
            bool: True si la restauración fue exitosa
        """
        try:
            backup_path = Path(backup_path)
            
            # Si es un archivo ZIP, extraerlo primero
            if backup_path.suffix == '.zip':
                extract_path = backup_path.with_suffix('')
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(extract_path)
                backup_path = extract_path
            
            # Verificar que existe el archivo de información
            info_file = backup_path / "backup_info.json"
            if not info_file.exists():
                raise Exception("Backup inválido: falta archivo de información")
            
            # Cargar información del backup
            with open(info_file, 'r', encoding='utf-8') as f:
                backup_info = json.load(f)
            
            if backup_info.get("status") != "completed":
                raise Exception("Backup incompleto o corrupto")
            
            logger.info(f"Restaurando backup v{backup_info['version']} del {backup_info['created_at']}")
            
            # Crear backup de seguridad antes de restaurar
            current_version = self._get_current_version()
            safety_backup = self.create_backup(current_version, "pre_restore")
            
            restored_files = []
            
            # Restaurar archivos
            for file_path in backup_info['files_backed_up']:
                src_path = backup_path / file_path
                dst_path = self.base_dir / file_path
                
                if src_path.exists():
                    try:
                        # Crear directorio padre si no existe
                        dst_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Eliminar destino si existe
                        if dst_path.exists():
                            if dst_path.is_dir():
                                shutil.rmtree(dst_path)
                            else:
                                dst_path.unlink()
                        
                        # Copiar desde backup
                        if src_path.is_dir():
                            shutil.copytree(src_path, dst_path)
                        else:
                            shutil.copy2(src_path, dst_path)
                        
                        restored_files.append(file_path)
                        logger.info(f"Restaurado: {file_path}")
                        
                    except Exception as e:
                        logger.error(f"Error restaurando {file_path}: {str(e)}")
                else:
                    logger.warning(f"Archivo no encontrado en backup: {file_path}")
            
            logger.info(f"Restauración completada: {len(restored_files)} archivos restaurados")
            
            # Crear registro de restauración
            restore_log = {
                "restored_from": backup_info,
                "restored_at": datetime.now().isoformat(),
                "restored_files": restored_files,
                "safety_backup": safety_backup
            }
            
            log_file = self.backup_dir / f"restore_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(restore_log, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error restaurando backup: {str(e)}")
            return False
    
    def list_backups(self):
        """
        Lista todos los backups disponibles
        
        Returns:
            list: Lista de información de backups
        """
        backups = []
        
        try:
            for item in self.backup_dir.iterdir():
                if item.is_dir() or item.suffix == '.zip':
                    info_file = None
                    
                    if item.is_dir():
                        info_file = item / "backup_info.json"
                    elif item.suffix == '.zip':
                        # Extraer info del ZIP temporalmente
                        try:
                            with zipfile.ZipFile(item, 'r') as zipf:
                                info_content = zipf.read('backup_info.json').decode('utf-8')
                                backup_info = json.loads(info_content)
                                backup_info['path'] = str(item)
                                backup_info['compressed'] = True
                                backups.append(backup_info)
                                continue
                        except Exception as e:
                            logger.debug(f"Error processing backup file: {e}")
                            continue
                    
                    if info_file and info_file.exists():
                        try:
                            with open(info_file, 'r', encoding='utf-8') as f:
                                backup_info = json.load(f)
                                backup_info['path'] = str(item)
                                backup_info['compressed'] = False
                                backups.append(backup_info)
                        except Exception as e:
                            logger.warning(f"Error leyendo info de backup {item}: {str(e)}")
            
            # Ordenar por fecha de creación (más reciente primero)
            backups.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
        except Exception as e:
            logger.error(f"Error listando backups: {str(e)}")
        
        return backups
    
    def delete_backup(self, backup_path):
        """Elimina un backup específico"""
        try:
            backup_path = Path(backup_path)
            if backup_path.exists():
                if backup_path.is_dir():
                    shutil.rmtree(backup_path)
                else:
                    backup_path.unlink()
                logger.info(f"Backup eliminado: {backup_path.name}")
                return True
        except Exception as e:
            logger.error(f"Error eliminando backup: {str(e)}")
        return False
    
    def _cleanup_old_backups(self, max_backups=10):
        """Limpia backups antiguos manteniendo solo los más recientes"""
        try:
            backups = self.list_backups()
            
            if len(backups) > max_backups:
                # Mantener solo los más recientes
                to_delete = backups[max_backups:]
                
                for backup in to_delete:
                    if backup.get('backup_type') != 'manual':  # No eliminar backups manuales
                        self.delete_backup(backup['path'])
                        logger.info(f"Backup antiguo eliminado: {Path(backup['path']).name}")
                
        except Exception as e:
            logger.error(f"Error limpiando backups antiguos: {str(e)}")
    
    def _get_directory_size(self, path):
        """Calcula el tamaño total de un directorio"""
        total_size = 0
        try:
            for file_path in Path(path).rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.warning(f"Error calculando tamaño de {path}: {str(e)}")
        return total_size
    
    def _get_current_version(self):
        """Obtiene la versión actual de EVA"""
        try:
            try:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from __version__ import __version__
            except ImportError:
                __version__ = "2.0.0"
            return __version__
        except ImportError:
            return "unknown"
    
    def verify_backup_integrity(self, backup_path):
        """Verifica la integridad de un backup"""
        try:
            backup_path = Path(backup_path)
            
            # Si es ZIP, verificar que se puede abrir
            if backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    # Verificar que contiene backup_info.json
                    if 'backup_info.json' not in zipf.namelist():
                        return False
                    
                    # Intentar leer la información
                    info_content = zipf.read('backup_info.json').decode('utf-8')
                    backup_info = json.loads(info_content)
            else:
                # Verificar directorio
                info_file = backup_path / "backup_info.json"
                if not info_file.exists():
                    return False
                
                with open(info_file, 'r', encoding='utf-8') as f:
                    backup_info = json.load(f)
            
            # Verificar que el backup se completó correctamente
            return backup_info.get('status') == 'completed'
            
        except Exception as e:
            logger.error(f"Error verificando integridad del backup: {str(e)}")
            return False