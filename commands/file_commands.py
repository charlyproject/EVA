"""
Comandos de archivos unificados para EVA
Maneja listado, ordenamiento y apertura de archivos con comandos naturales
Filosofía: 1 comando = 1 función
"""

import logging
import os
import json

from utils.bilingual_command import BilingualCommand
try:
    from utils.file_utils import get_working_folder, save_last_folder_path
except ImportError:
    # Fallback si no están disponibles
    def get_working_folder():
        return None
    def save_last_folder_path(path):
        pass

logger = logging.getLogger("EVA")


class FileCommandHandler:
    """Handler unificado para comandos de archivos"""
    
    def __init__(self, processor):
        self.processor = processor
        self.config = processor.config
        self.language_manager = processor.language_manager
        
        # Comandos de archivos unificados con filosofía natural
        self.commands = {
            # Comando para listar archivos
            BilingualCommand("lista archivos", "list files"): self._list_files,
            
            # Comando para configurar ordenamiento
            BilingualCommand("ordena archivos", "sort files"): self._configure_sort,
        }
    
    def can_handle(self, text: str) -> bool:
        """Verifica si puede manejar el comando"""
        text_lower = text.lower().strip()
        
        # Verificar comandos de archivos
        for bilingual_cmd in self.commands.keys():
            if bilingual_cmd.matches(text_lower):
                return True
        
        # Verificar selección de ordenamiento (1, 2, 3) cuando está pendiente
        if (hasattr(self.processor, 'pending_file_order') and 
            self.processor.pending_file_order and 
            text_lower in ["1", "2", "3"]):
            return True
        
        return False
    
    def handle(self, text: str, chat_window) -> bool:
        """Maneja el comando de archivos"""
        try:
            text_lower = text.lower().strip()
            
            # Manejar selección de ordenamiento pendiente
            if (hasattr(self.processor, 'pending_file_order') and 
                self.processor.pending_file_order and 
                text_lower in ["1", "2", "3"]):
                return self._handle_sort_selection(text_lower, chat_window)
            
            # Buscar comando coincidente
            for bilingual_cmd, handler_func in self.commands.items():
                if bilingual_cmd.matches(text_lower):
                    logger.info(f"📁 Ejecutando comando de archivos: {bilingual_cmd}")
                    return handler_func(chat_window)
            
            return False
            
        except Exception as e:
            logger.error(f"Error en comando de archivos: {str(e)}")
            error_msg = self.language_manager.get_text("responses.file_command_error", 
                                                     default="Error en comando de archivos")
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _list_files(self, chat_window) -> bool:
        """Lista archivos de la carpeta activa"""
        try:
            # Obtener carpeta de trabajo
            working_folder = self._get_working_folder()
            if not working_folder:
                no_folder_msg = self.language_manager.get_text("responses.no_recent_folder", 
                                                             default="No hay carpeta activa")
                chat_window.add_message(no_folder_msg, is_user=False)
                return True
            
            # Obtener archivos con información completa
            files = []
            try:
                for entry in os.scandir(working_folder):
                    if entry.is_file():
                        stat = entry.stat()
                        files.append({
                            'name': entry.name,
                            'creation': stat.st_ctime,
                            'modification': stat.st_mtime
                        })
            except Exception as e:
                logger.error(f"Error escaneando carpeta: {str(e)}")
                error_msg = f"Error accediendo a la carpeta: {working_folder}"
                chat_window.add_message(error_msg, is_user=False)
                return True
            
            if not files:
                no_files_msg = self.language_manager.get_text("responses.no_files", 
                                                            default="No hay archivos en la carpeta")
                chat_window.add_message(no_files_msg, is_user=False)
                return True
            
            # Ordenar según método configurado
            sort_method = getattr(self.processor, 'file_sort_method', 'creation')
            files = self._sort_files(files, sort_method)
            
            # Mostrar lista de archivos
            folder_name = os.path.basename(working_folder)
            sort_name = self.language_manager.get_text(f"responses.sort_name_{sort_method}", default=sort_method)
            header_msg = self.language_manager.get_text("responses.files_in_folder", folder=folder_name, sort_method=sort_name)
            chat_window.add_message(header_msg, is_user=False)
            
            # Mostrar hasta 15 archivos numerados
            for i, file_info in enumerate(files[:15], 1):
                chat_window.add_message(f"{i}. {file_info['name']}", is_user=False)
            
            if len(files) > 15:
                more_msg = self.language_manager.get_text("responses.more_files", count=len(files)-15)
                chat_window.add_message(more_msg, is_user=False)
            
            # Sugerencia útil
            tip_msg = self.language_manager.get_text("responses.file_list_tip")
            chat_window.add_message(tip_msg, is_user=False)
            
            logger.info(f"📁 Listados {len(files)} archivos de {working_folder}")
            return True
            
        except Exception as e:
            logger.error(f"Error listando archivos: {str(e)}")
            return False
    
    def _configure_sort(self, chat_window) -> bool:
        """Configura el ordenamiento de archivos"""
        try:
            # Verificar que hay carpeta activa
            working_folder = self._get_working_folder()
            if not working_folder:
                no_folder_msg = self.language_manager.get_text("responses.no_recent_folder", 
                                                             default="No hay carpeta activa")
                chat_window.add_message(no_folder_msg, is_user=False)
                return True
            
            # Mostrar opciones de ordenamiento
            options_msg = self.language_manager.get_text("responses.file_order_options", 
                default="Selecciona el orden de archivos:\n1. Por nombre (alfabético)\n2. Por fecha de creación (más reciente primero)\n3. Por fecha de modificación (más reciente primero)")
            chat_window.add_message(options_msg, is_user=False)
            
            # Establecer estado de espera para selección
            self.processor.context.pending_file_order = True
            logger.info("📁 Esperando selección de ordenamiento de archivos")
            return True
            
        except Exception as e:
            logger.error(f"Error configurando ordenamiento: {str(e)}")
            return False
    
    def _handle_sort_selection(self, selection: str, chat_window) -> bool:
        """Maneja la selección del tipo de ordenamiento"""
        try:
            order_type = int(selection)
            
            # Aplicar el ordenamiento seleccionado
            if order_type == 1:
                self.processor.context.file_sort_method = "name"
                response = self.language_manager.get_text("responses.file_order_name", 
                                                        default="✅ Archivos ordenados por nombre (alfabético)")
            elif order_type == 2:
                self.processor.context.file_sort_method = "creation"
                response = self.language_manager.get_text("responses.file_order_creation", 
                                                        default="✅ Archivos ordenados por fecha de creación")
            elif order_type == 3:
                self.processor.context.file_sort_method = "modification"
                response = self.language_manager.get_text("responses.file_order_modification", 
                                                        default="✅ Archivos ordenados por fecha de modificación")
            else:
                invalid_msg = self.language_manager.get_text("responses.invalid_selection", 
                                                           default="❌ Selección inválida. Usa 1, 2 o 3")
                chat_window.add_message(invalid_msg, is_user=False)
                return True
            
            # Guardar configuración permanentemente
            self._save_sort_config()
            
            chat_window.add_message(response, is_user=False)
            
            # Resetear estado
            self.processor.context.pending_file_order = False
            
            logger.info(f"📁 Ordenamiento configurado: {self.processor.context.file_sort_method}")
            return True
            
        except Exception as e:
            logger.error(f"Error procesando selección: {str(e)}")
            self.processor.context.pending_file_order = False
            return False
    
    def _get_working_folder(self):
        """Obtiene la carpeta de trabajo activa"""
        try:
            # Usar función centralizada
            working_folder = get_working_folder()
            
            if working_folder:
                # Actualizar carpeta del procesador si es diferente
                if working_folder != self.processor.last_opened_folder:
                    self.processor.context.last_opened_folder = working_folder
                    save_last_folder_path(working_folder)
                return working_folder
            
            # Fallback a última carpeta del procesador
            if (hasattr(self.processor, 'last_opened_folder') and 
                self.processor.last_opened_folder and 
                os.path.isdir(self.processor.last_opened_folder)):
                return self.processor.last_opened_folder
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo carpeta de trabajo: {str(e)}")
            return None
    
    def _sort_files(self, files, sort_method):
        """Ordena la lista de archivos según el método especificado"""
        try:
            if sort_method == "name":
                return sorted(files, key=lambda x: x['name'].lower())
            elif sort_method == "creation":
                return sorted(files, key=lambda x: x['creation'], reverse=True)
            elif sort_method == "modification":
                return sorted(files, key=lambda x: x['modification'], reverse=True)
            else:
                # Fallback a creación
                return sorted(files, key=lambda x: x['creation'], reverse=True)
                
        except Exception as e:
            logger.error(f"Error ordenando archivos: {str(e)}")
            return files
    
    def _get_sort_name(self, sort_method):
        """Obtiene el nombre legible del método de ordenamiento"""
        return self.language_manager.get_text(f"responses.sort_name_{sort_method}", default=sort_method)
    
    def _save_sort_config(self):
        """Guarda la configuración de ordenamiento permanentemente"""
        try:
            # Actualizar configuración en memoria
            self.config["file_sort_method"] = self.processor.file_sort_method
            
            # Guardar en archivo de configuración
            config_path = os.path.join("config", "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
                logger.info(f"✅ Configuración de ordenamiento guardada: {self.processor.file_sort_method}")
            
        except Exception as e:
            logger.error(f"Error guardando configuración: {str(e)}")