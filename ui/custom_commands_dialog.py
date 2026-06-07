import logging
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QLabel,
                               QFileDialog, QMessageBox, QInputDialog,
                               QWidget, QGroupBox, QScrollArea, QFrame)

from core.config_manager_unified import config_manager

logger = logging.getLogger("EVA")

class CustomCommandsDialog(QDialog):
    commands_updated = Signal(dict)

    def __init__(self, config, language_manager, parent=None):
        super().__init__(parent)
        self.config = config
        self.language_manager = language_manager
        self.setWindowTitle("Personalización de Comandos")
        
        # Configure window attributes
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        
        # Configure window icon
        icon_path = os.path.join("resources", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            logger.warning("Icono de ventana no encontrado en: " + icon_path)

        # Set window size (same as settings window)
        self.setMinimumSize(450, 280)
        self.resize(600, 450)
        
        # Layout principal de la ventana
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(4)
        self.layout.setContentsMargins(8, 8, 8, 4)

        # Contenedor para el contenido que será scrollable
        self.scrollable_content_widget = QWidget()
        self.scrollable_content_widget.setStyleSheet("background-color: rgb(25, 25, 35);")
        self.scrollable_content_layout = QVBoxLayout(self.scrollable_content_widget)
        self.scrollable_content_layout.setSpacing(4)
        self.scrollable_content_layout.setContentsMargins(0, 0, 0, 0)

        # QScrollArea para el contenido
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scrollable_content_widget)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        self.scroll_area.verticalScrollBar().setStyleSheet(
            """
            QScrollBar:vertical {
                border: 1px solid #4db6ac;
                background: #303040;
                width: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #00bcd4;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            """
        )

        # Estilo con colores de fondo completamente opacos (igual que settings window)
        self.setStyleSheet(
            """
            QDialog {
                background-color: rgb(25, 25, 35);
                font-family: 'Segoe UI', 'Open Sans', sans-serif;
                font-size: 13px;
                border: 2px solid #4db6ac;
                border-radius: 12px;
            }
            QGroupBox {
                font-weight: 600;
                font-size: 13px;
                color: #bb86fc;
                border: 1px solid rgba(77, 182, 172, 0.3);
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 15px;
                background-color: rgb(30, 30, 40);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 8px;
                background-color: rgb(30, 30, 40);
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
            QPushButton {
                background-color: rgba(63, 81, 181, 0.3);
                border: 1px solid rgba(63, 81, 181, 0.5);
                border-radius: 6px;
                padding: 6px 12px;
                min-height: 28px;
                font-weight: 500;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: rgba(63, 81, 181, 0.4);
                border: 1px solid rgba(63, 81, 181, 0.7);
            }
            QCheckBox {
                color: #ffffff;
                spacing: 6px;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                border: 1px solid rgba(77, 182, 172, 0.5);
                background-color: rgb(30, 30, 40);
            }
            QCheckBox::indicator:checked {
                background-color: #00bcd4;
                border: 1px solid #ffffff;
            }
            QSlider::groove:horizontal {
                height: 7px;
                background: rgba(77, 182, 172, 0.2);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00bcd4;
                border: 1px solid rgba(0, 0, 0, 0.2);
                width: 16px;
                height: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #00bcd4;
                border-radius: 3px;
            }
            QLineEdit {
                background-color: rgb(30, 30, 40);
                border: 1px solid rgba(77, 182, 172, 0.3);
                border-radius: 5px;
                padding: 6px;
                color: #ffffff;
                font-size: 12px;
            }
            QListWidget {
                background-color: rgb(30, 30, 40);
                border: 1px solid rgba(77, 182, 172, 0.3);
                border-radius: 6px;
                color: #ffffff;
                font-size: 13px;
            }
            QComboBox {
                background-color: rgb(30, 30, 40);
                border: 1px solid rgba(77, 182, 172, 0.3);
                border-radius: 5px;
                padding: 5px;
                min-height: 28px;
                color: #ffffff;
                font-size: 13px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: rgb(30, 30, 40);
                border: 1px solid rgba(77, 182, 172, 0.3);
                selection-background-color: rgba(0, 188, 212, 0.3);
                color: #ffffff;
            }
        """
        )
        
        self.init_ui()
        self.load_commands()
        
        # Centrar con respecto al padre
        if parent:
            self.center_on_parent(parent)

    def center_on_parent(self, parent):
        parent_rect = parent.geometry()
        x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
        y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
        self.move(x, y)

    def get_text(self, key, default=""):
        """Get localized text using language manager"""
        if self.language_manager and hasattr(self.language_manager, 'get_text'):
            return self.language_manager.get_text(key, default)
        return default

    def init_ui(self):
        # Configurar las secciones principales
        self.setup_programs_section()
        self.setup_folders_section()
        self.setup_websites_section()
        self.setup_hotkeys_section()
        self.setup_variants_section()
        
        # Agregar el scroll area al layout principal
        self.layout.addWidget(self.scroll_area, 1)
        
        # Frame para botones de acción
        btn_frame = QFrame()
        btn_frame.setStyleSheet("background-color: rgb(25, 25, 35); border: none;")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(8, 8, 8, 8)
        btn_layout.setSpacing(8)

        self.save_btn = QPushButton(self.get_text("ui.save", default="Guardar"))
        self.save_btn.setStyleSheet(
            """
            background-color: rgba(76, 175, 80, 0.4);
            min-width: 70px;
            padding: 5px;
            font-weight: 600;
        """
        )
        self.save_btn.clicked.connect(self.save_commands)

        self.cancel_btn = QPushButton(self.get_text("ui.cancel", default="Cancelar"))
        self.cancel_btn.setStyleSheet(
            """
            background-color: rgba(244, 67, 54, 0.4);
            min-width: 70px;
            padding: 5px;
            font-weight: 600;
        """
        )
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        self.layout.addWidget(btn_frame)

    def setup_programs_section(self):
        """Sección para programas configurados"""
        programs_group = QGroupBox(self.get_text("ui.configured_programs", default="Programas Configurados"))
        layout = QVBoxLayout(programs_group)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 15, 8, 8)

        # Descripción
        desc_label = QLabel(self.get_text("ui.programs_description", default="Configura programas que puedes abrir con comandos de voz"))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 12px; color: #aaaaaa; margin-bottom: 8px;")
        layout.addWidget(desc_label)

        # Lista de programas
        self.programs_list = QListWidget()
        self.programs_list.setMaximumHeight(120)
        layout.addWidget(self.programs_list)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        self.add_program_btn = QPushButton(self.get_text("ui.add_program", default="Agregar Programa"))
        self.add_program_btn.setStyleSheet("background-color: rgba(76, 175, 80, 0.3); min-width: 100px;")
        self.add_program_btn.clicked.connect(self.add_program)
        
        self.edit_program_btn = QPushButton(self.get_text("ui.edit", default="Editar"))
        self.edit_program_btn.setStyleSheet("background-color: rgba(255, 152, 0, 0.3); min-width: 60px;")
        self.edit_program_btn.clicked.connect(self.edit_program)
        
        self.remove_program_btn = QPushButton(self.get_text("ui.remove", default="Eliminar"))
        self.remove_program_btn.setStyleSheet("background-color: rgba(244, 67, 54, 0.3); min-width: 60px;")
        self.remove_program_btn.clicked.connect(self.remove_program)
        
        btn_layout.addWidget(self.add_program_btn)
        btn_layout.addWidget(self.edit_program_btn)
        btn_layout.addWidget(self.remove_program_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.scrollable_content_layout.addWidget(programs_group)

    def setup_folders_section(self):
        """Sección para carpetas configuradas"""
        folders_group = QGroupBox(self.get_text("ui.configured_folders", default="Carpetas Configuradas"))
        layout = QVBoxLayout(folders_group)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 15, 8, 8)

        # Descripción
        desc_label = QLabel(self.get_text("ui.folders_description", default="Configura carpetas que puedes abrir con comandos de voz"))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 12px; color: #aaaaaa; margin-bottom: 8px;")
        layout.addWidget(desc_label)

        # Lista de carpetas
        self.folders_list = QListWidget()
        self.folders_list.setMaximumHeight(120)
        layout.addWidget(self.folders_list)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        self.add_folder_btn = QPushButton(self.get_text("ui.add_folder", default="Agregar Carpeta"))
        self.add_folder_btn.setStyleSheet("background-color: rgba(76, 175, 80, 0.3); min-width: 100px;")
        self.add_folder_btn.clicked.connect(self.add_folder)
        
        self.edit_folder_btn = QPushButton(self.get_text("ui.edit", default="Editar"))
        self.edit_folder_btn.setStyleSheet("background-color: rgba(255, 152, 0, 0.3); min-width: 60px;")
        self.edit_folder_btn.clicked.connect(self.edit_folder)
        
        self.remove_folder_btn = QPushButton(self.get_text("ui.remove", default="Eliminar"))
        self.remove_folder_btn.setStyleSheet("background-color: rgba(244, 67, 54, 0.3); min-width: 60px;")
        self.remove_folder_btn.clicked.connect(self.remove_folder)
        
        btn_layout.addWidget(self.add_folder_btn)
        btn_layout.addWidget(self.edit_folder_btn)
        btn_layout.addWidget(self.remove_folder_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.scrollable_content_layout.addWidget(folders_group)

    def setup_websites_section(self):
        """Sección para sitios web configurados"""
        websites_group = QGroupBox(self.get_text("ui.configured_websites", default="Sitios Web Configurados"))
        layout = QVBoxLayout(websites_group)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 15, 8, 8)

        # Descripción
        desc_label = QLabel(self.get_text("ui.websites_description", default="Configura sitios web que puedes abrir con comandos de voz"))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 12px; color: #aaaaaa; margin-bottom: 8px;")
        layout.addWidget(desc_label)

        # Lista de sitios web
        self.websites_list = QListWidget()
        self.websites_list.setMaximumHeight(120)
        layout.addWidget(self.websites_list)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        self.add_website_btn = QPushButton(self.get_text("ui.add_website", default="Agregar Sitio Web"))
        self.add_website_btn.setStyleSheet("background-color: rgba(76, 175, 80, 0.3); min-width: 100px;")
        self.add_website_btn.clicked.connect(self.add_website)
        
        self.edit_website_btn = QPushButton(self.get_text("ui.edit", default="Editar"))
        self.edit_website_btn.setStyleSheet("background-color: rgba(255, 152, 0, 0.3); min-width: 60px;")
        self.edit_website_btn.clicked.connect(self.edit_website)
        
        self.remove_website_btn = QPushButton(self.get_text("ui.remove", default="Eliminar"))
        self.remove_website_btn.setStyleSheet("background-color: rgba(244, 67, 54, 0.3); min-width: 60px;")
        self.remove_website_btn.clicked.connect(self.remove_website)
        
        btn_layout.addWidget(self.add_website_btn)
        btn_layout.addWidget(self.edit_website_btn)
        btn_layout.addWidget(self.remove_website_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.scrollable_content_layout.addWidget(websites_group)

    def setup_hotkeys_section(self):
        """Sección para atajos de teclado"""
        hotkeys_group = QGroupBox(self.get_text("ui.configured_hotkeys", default="Atajos de Teclado"))
        layout = QVBoxLayout(hotkeys_group)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 15, 8, 8)

        # Descripción
        desc_label = QLabel(self.get_text("ui.hotkeys_description", default="Configura combinaciones de teclas para ejecutar acciones rápidas"))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 12px; color: #aaaaaa; margin-bottom: 8px;")
        layout.addWidget(desc_label)

        # Lista de atajos
        self.hotkeys_list = QListWidget()
        self.hotkeys_list.setMaximumHeight(120)
        layout.addWidget(self.hotkeys_list)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        self.add_hotkey_btn = QPushButton(self.get_text("ui.add_hotkey", default="Agregar Atajo"))
        self.add_hotkey_btn.setStyleSheet("background-color: rgba(76, 175, 80, 0.3); min-width: 100px;")
        self.add_hotkey_btn.clicked.connect(self.add_hotkey)
        
        self.edit_hotkey_btn = QPushButton(self.get_text("ui.edit", default="Editar"))
        self.edit_hotkey_btn.setStyleSheet("background-color: rgba(255, 152, 0, 0.3); min-width: 60px;")
        self.edit_hotkey_btn.clicked.connect(self.edit_hotkey)
        
        self.remove_hotkey_btn = QPushButton(self.get_text("ui.remove", default="Eliminar"))
        self.remove_hotkey_btn.setStyleSheet("background-color: rgba(244, 67, 54, 0.3); min-width: 60px;")
        self.remove_hotkey_btn.clicked.connect(self.remove_hotkey)
        
        btn_layout.addWidget(self.add_hotkey_btn)
        btn_layout.addWidget(self.edit_hotkey_btn)
        btn_layout.addWidget(self.remove_hotkey_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.scrollable_content_layout.addWidget(hotkeys_group)

    def setup_variants_section(self):
        """Sección para variantes de comandos"""
        variants_group = QGroupBox(self.get_text("ui.command_variants", default="Variantes de Comandos"))
        layout = QVBoxLayout(variants_group)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 15, 8, 8)

        # Descripción de la funcionalidad
        desc_label = QLabel(self.get_text("ui.variants_description", default="Las variantes permiten que EVA reconozca diferentes formas de pronunciar el mismo comando.\nEjemplo: 'google' puede reconocerse como 'guguel', 'gugle', etc."))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 12px; color: #aaaaaa; margin-bottom: 8px;")
        layout.addWidget(desc_label)
        
        # Lista de variantes
        self.variants_list = QListWidget()
        self.variants_list.setMaximumHeight(120)
        layout.addWidget(self.variants_list)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        self.add_variant_btn = QPushButton(self.get_text("ui.add_variant", default="Agregar Variante"))
        self.add_variant_btn.setStyleSheet("background-color: rgba(76, 175, 80, 0.3); min-width: 100px;")
        self.add_variant_btn.clicked.connect(self.add_variant)
        
        self.edit_variant_btn = QPushButton(self.get_text("ui.edit", default="Editar"))
        self.edit_variant_btn.setStyleSheet("background-color: rgba(255, 152, 0, 0.3); min-width: 60px;")
        self.edit_variant_btn.clicked.connect(self.edit_variant)
        
        self.remove_variant_btn = QPushButton(self.get_text("ui.remove", default="Eliminar"))
        self.remove_variant_btn.setStyleSheet("background-color: rgba(244, 67, 54, 0.3); min-width: 60px;")
        self.remove_variant_btn.clicked.connect(self.remove_variant)
        
        btn_layout.addWidget(self.add_variant_btn)
        btn_layout.addWidget(self.edit_variant_btn)
        btn_layout.addWidget(self.remove_variant_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        self.scrollable_content_layout.addWidget(variants_group)

    def load_commands(self):
        # Cargar programas
        self.programs_list.clear()
        for name, path in self.config.get("paths", {}).get("programs", {}).items():
            item = QListWidgetItem(f"{name}: {path}")
            item.setData(Qt.UserRole, (name, path))
            self.programs_list.addItem(item)
        
        # Cargar carpetas
        self.folders_list.clear()
        for name, path in self.config.get("paths", {}).get("folders", {}).items():
            item = QListWidgetItem(f"{name}: {path}")
            item.setData(Qt.UserRole, (name, path))
            self.folders_list.addItem(item)
        
        # Cargar sitios web
        self.websites_list.clear()
        for name, url in self.config.get("paths", {}).get("websites", {}).items():
            item = QListWidgetItem(f"{name}: {url}")
            item.setData(Qt.UserRole, (name, url))
            self.websites_list.addItem(item)
        
        # Cargar atajos
        self.hotkeys_list.clear()
        for hotkey in self.config.get("paths", {}).get("hotkeys", []):
            key = hotkey.get("key", "")
            action = hotkey.get("action_type", "")
            target = hotkey.get("target", "")
            item = QListWidgetItem(f"{key} → {action}: {target}")
            item.setData(Qt.UserRole, hotkey)
            self.hotkeys_list.addItem(item)
        
        # Cargar variantes
        self.variants_list.clear()
        for command, variants in self.config.get("variants", {}).items():
            variants_text = ", ".join(variants)
            item = QListWidgetItem(f"{command}: {variants_text}")
            item.setData(Qt.UserRole, (command, variants))
            self.variants_list.addItem(item)

    def add_program(self):
        name, ok = QInputDialog.getText(self, self.get_text("ui.add_program", default="Añadir Programa"), self.get_text("ui.command_name", default="Nombre del comando:"))
        if not ok or not name:
            return
        
        path, _ = QFileDialog.getOpenFileName(self, self.get_text("ui.select_executable", default="Seleccionar Ejecutable"), "", self.get_text("ui.executables_filter", default="Ejecutables (*.exe)"))
        if not path:
            return
        
        self.config.setdefault("paths", {}).setdefault("programs", {})[name] = path
        self.load_commands()

    def edit_program(self):
        item = self.programs_list.currentItem()
        if not item:
            return
        
        name, path = item.data(Qt.UserRole)
        
        new_name, ok = QInputDialog.getText(self, self.get_text("ui.edit_program", default="Editar Programa"), self.get_text("ui.new_name", default="Nuevo nombre:"), text=name)
        if not ok or not new_name:
            return
        
        new_path, _ = QFileDialog.getOpenFileName(self, self.get_text("ui.select_executable", default="Seleccionar Ejecutable"), path, self.get_text("ui.executables_filter", default="Ejecutables (*.exe)"))
        if not new_path:
            return
        
        # Actualizar programa
        programs = self.config["paths"]["programs"]
        if name in programs:
            del programs[name]
        programs[new_name] = new_path
        self.load_commands()

    def remove_program(self):
        item = self.programs_list.currentItem()
        if not item:
            return
        
        name, path = item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            self.get_text("ui.remove_program", default="Eliminar Programa"),
            self.get_text("ui.confirm_remove_program", default="¿Seguro que quieres eliminar el programa '{name}'?").format(name=name),
            QMessageBox.Yes | QMessageBox.No,
        )
        
        if reply == QMessageBox.Yes:
            del self.config["paths"]["programs"][name]
            self.load_commands()

    def add_folder(self):
        name, ok = QInputDialog.getText(self, self.get_text("ui.add_folder", default="Añadir Carpeta"), self.get_text("ui.command_name", default="Nombre del comando:"))
        if not ok or not name:
            return
        
        path = QFileDialog.getExistingDirectory(self, self.get_text("ui.select_folder", default="Seleccionar Carpeta"))
        if not path:
            return
        
        self.config.setdefault("paths", {}).setdefault("folders", {})[name] = path
        self.load_commands()

    def edit_folder(self):
        item = self.folders_list.currentItem()
        if not item:
            return
        
        name, path = item.data(Qt.UserRole)
        
        new_name, ok = QInputDialog.getText(self, self.get_text("ui.edit_folder", default="Editar Carpeta"), self.get_text("ui.new_name", default="Nuevo nombre:"), text=name)
        if not ok or not new_name:
            return
        
        new_path = QFileDialog.getExistingDirectory(self, self.get_text("ui.select_folder", default="Seleccionar Carpeta"), path)
        if not new_path:
            return
        
        # Actualizar carpeta
        folders = self.config["paths"]["folders"]
        if name in folders:
            del folders[name]
        folders[new_name] = new_path
        self.load_commands()

    def remove_folder(self):
        item = self.folders_list.currentItem()
        if not item:
            return
        
        name, path = item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            self.get_text("ui.remove_folder", default="Eliminar Carpeta"),
            self.get_text("ui.confirm_remove_folder", default="¿Seguro que quieres eliminar la carpeta '{name}'?").format(name=name),
            QMessageBox.Yes | QMessageBox.No,
        )
        
        if reply == QMessageBox.Yes:
            del self.config["paths"]["folders"][name]
            self.load_commands()

    def add_website(self):
        name, ok = QInputDialog.getText(self, self.get_text("ui.add_website", default="Añadir Sitio Web"), self.get_text("ui.command_name", default="Nombre del comando:"))
        if not ok or not name:
            return
        
        url, ok = QInputDialog.getText(self, self.get_text("ui.add_website", default="Añadir Sitio Web"), self.get_text("ui.website_url", default="URL del sitio web:"))
        if not ok or not url:
            return
        
        self.config.setdefault("paths", {}).setdefault("websites", {})[name] = url
        self.load_commands()

    def edit_website(self):
        item = self.websites_list.currentItem()
        if not item:
            return
        
        name, url = item.data(Qt.UserRole)
        
        new_name, ok = QInputDialog.getText(self, self.get_text("ui.edit_website", default="Editar Sitio Web"), self.get_text("ui.new_name", default="Nuevo nombre:"), text=name)
        if not ok or not new_name:
            return
        
        new_url, ok = QInputDialog.getText(self, self.get_text("ui.edit_website", default="Editar Sitio Web"), self.get_text("ui.new_url", default="Nueva URL:"), text=url)
        if not ok or not new_url:
            return
        
        # Actualizar sitio web
        websites = self.config["paths"]["websites"]
        if name in websites:
            del websites[name]
        websites[new_name] = new_url
        self.load_commands()

    def remove_website(self):
        item = self.websites_list.currentItem()
        if not item:
            return
        
        name, url = item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            self.get_text("ui.remove_website", default="Eliminar Sitio Web"),
            self.get_text("ui.confirm_remove_website", default="¿Seguro que quieres eliminar el sitio web '{name}'?").format(name=name),
            QMessageBox.Yes | QMessageBox.No,
        )
        
        if reply == QMessageBox.Yes:
            del self.config["paths"]["websites"][name]
            self.load_commands()

    def add_hotkey(self):
        key, ok = QInputDialog.getText(self, self.get_text("ui.add_hotkey", default="Añadir Atajo"), self.get_text("ui.key_combination", default="Combinación de teclas (ej: Ctrl+Alt+A):"))
        if not ok or not key:
            return
        
        action_types = [
            self.get_text("ui.action_basic", default="basic"),
            self.get_text("ui.action_program", default="program"), 
            self.get_text("ui.action_folder", default="folder"),
            self.get_text("ui.action_website", default="website")
        ]
        action_type, ok = QInputDialog.getItem(
            self,
            self.get_text("ui.action_type", default="Tipo de Acción"),
            self.get_text("ui.select_action_type", default="Selecciona el tipo de acción:"),
            action_types,
            0,
            False,
        )
        if not ok or not action_type:
            return
        
        # Map translated action type back to actual value
        action_values = ["basic", "program", "folder", "website"]
        action_type_value = action_values[action_types.index(action_type)]
        
        target, ok = QInputDialog.getText(self, self.get_text("ui.target", default="Objetivo"), self.get_text("ui.shortcut_target", default="Objetivo del atajo:"))
        if not ok or not target:
            return
        
        hotkey = {
            "key": key,
            "action_type": action_type_value,
            "target": target,
        }
        
        self.config.setdefault("paths", {}).setdefault("hotkeys", []).append(hotkey)
        self.load_commands()

    def edit_hotkey(self):
        item = self.hotkeys_list.currentItem()
        if not item:
            return
        
        hotkey = item.data(Qt.UserRole)
        
        new_key, ok = QInputDialog.getText(self, self.get_text("ui.edit_hotkey", default="Editar Atajo"), self.get_text("ui.new_key_combination", default="Nueva combinación de teclas:"), text=hotkey["key"])
        if not ok or not new_key:
            return
        
        action_types = [
            self.get_text("ui.action_basic", default="basic"),
            self.get_text("ui.action_program", default="program"), 
            self.get_text("ui.action_folder", default="folder"),
            self.get_text("ui.action_website", default="website")
        ]
        action_values = ["basic", "program", "folder", "website"]
        current_index = action_values.index(hotkey["action_type"]) if hotkey["action_type"] in action_values else 0
        
        new_action_type, ok = QInputDialog.getItem(
            self,
            self.get_text("ui.action_type", default="Tipo de Acción"),
            self.get_text("ui.select_action_type", default="Selecciona el tipo de acción:"),
            action_types,
            current_index,
            False,
        )
        if not ok or not new_action_type:
            return
        
        # Map translated action type back to actual value
        action_type_value = action_values[action_types.index(new_action_type)]
        
        new_target, ok = QInputDialog.getText(self, self.get_text("ui.target", default="Objetivo"), self.get_text("ui.new_target", default="Nuevo objetivo:"), text=hotkey["target"])
        if not ok or not new_target:
            return
        
        # Actualizar atajo
        hotkey["key"] = new_key
        hotkey["action_type"] = action_type_value
        hotkey["target"] = new_target
        
        self.load_commands()

    def remove_hotkey(self):
        item = self.hotkeys_list.currentItem()
        if not item:
            return
        
        hotkey = item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            self.get_text("ui.remove_hotkey", default="Eliminar Atajo"),
            self.get_text("ui.confirm_remove_hotkey", default="¿Seguro que quieres eliminar el atajo '{key}'?").format(key=hotkey['key']),
            QMessageBox.Yes | QMessageBox.No,
        )
        
        if reply == QMessageBox.Yes:
            self.config["paths"]["hotkeys"].remove(hotkey)
            self.load_commands()

    def save_commands(self):
        try:
            config_manager.save()
            self.commands_updated.emit(self.config)
            self.accept()
        except Exception as e:
            logger.error(f"Error guardando comandos: {str(e)}")
            QMessageBox.critical(self, self.get_text("ui.dialogs.error", default="Error"), self.get_text("ui.save_config_error", default="No se pudo guardar la configuración") + f": {str(e)}")

    def add_variant(self):
        command, ok = QInputDialog.getText(self, self.get_text("ui.add_variant", default="Añadir Variante"), self.get_text("ui.base_command", default="Comando base (ej: google, chrome, ccleaner):"))
        if not ok or not command:
            return
        
        variants_text, ok = QInputDialog.getText(
            self, 
            self.get_text("ui.command_variants", default="Variantes del Comando"), 
            self.get_text("ui.variants_input", default="Variantes para '{command}' separadas por comas:\n(ej: guguel, gugle, gogel)").format(command=command)
        )
        if not ok or not variants_text:
            return
        
        # Procesar variantes
        variants = [v.strip().lower() for v in variants_text.split(",") if v.strip()]
        
        # Añadir el comando original como primera variante si no está incluido
        command_lower = command.strip().lower()
        if command_lower not in variants:
            variants.insert(0, command_lower)
        
        # Guardar en configuración
        self.config.setdefault("variants", {})[command_lower] = variants
        self.load_commands()

    def edit_variant(self):
        item = self.variants_list.currentItem()
        if not item:
            return
        
        command, current_variants = item.data(Qt.UserRole)
        
        new_command, ok = QInputDialog.getText(self, self.get_text("ui.edit_variant", default="Editar Variante"), self.get_text("ui.base_command", default="Comando base:"), text=command)
        if not ok or not new_command:
            return
        
        variants_text = ", ".join(current_variants)
        new_variants_text, ok = QInputDialog.getText(
            self, 
            self.get_text("ui.edit_variants", default="Editar Variantes"), 
            self.get_text("ui.variants_for_command", default="Variantes para '{command}':").format(command=new_command), 
            text=variants_text
        )
        if not ok or not new_variants_text:
            return
        
        # Procesar nuevas variantes
        new_variants = [v.strip().lower() for v in new_variants_text.split(",") if v.strip()]
        new_command_lower = new_command.strip().lower()
        
        # Añadir el comando original como primera variante si no está incluido
        if new_command_lower not in new_variants:
            new_variants.insert(0, new_command_lower)
        
        # Actualizar configuración
        variants = self.config.setdefault("variants", {})
        if command in variants:
            del variants[command]
        variants[new_command_lower] = new_variants
        
        self.load_commands()

    def remove_variant(self):
        item = self.variants_list.currentItem()
        if not item:
            return
        
        command, variants = item.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self,
            self.get_text("ui.remove_variant", default="Eliminar Variante"),
            self.get_text("ui.confirm_remove_variant", default="¿Seguro que quieres eliminar las variantes para '{command}'?\nVariantes: {variants}").format(command=command, variants=", ".join(variants)),
            QMessageBox.Yes | QMessageBox.No,
        )
        
        if reply == QMessageBox.Yes:
            if "variants" in self.config and command in self.config["variants"]:
                del self.config["variants"][command]
            self.load_commands()