import logging
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QListWidget, QListWidgetItem,
                               QMessageBox, QInputDialog, QFrame, QScrollArea, QWidget)

logger = logging.getLogger("EVA")


class ShortcutEditorDialog(QDialog):
    """Diálogo para crear y editar atajos personalizados de forma visual"""
    
    def __init__(self, shortcut_data=None, parent=None, language_manager=None):
        super().__init__(parent)
        self.shortcut_data = shortcut_data or {}
        self.commands = []
        self.language_manager = language_manager
        
        # Tamaño más compacto como la ventana de ajustes
        self.setMinimumSize(450, 280)
        self.resize(600, 450)
        
        self.setWindowTitle(self.get_text("ui.shortcut_editor.title"))
        self.setModal(True)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        # Configurar icono de la ventana
        import os
        icon_path = os.path.join("resources", "icon.ico")
        if os.path.exists(icon_path):
            from PySide6.QtGui import QIcon
            self.setWindowIcon(QIcon(icon_path))
        
        # Aplicar estilo consistente con EVA
        self.setStyleSheet("""
            QDialog {
                background-color: rgb(25, 25, 35);
                font-family: 'Segoe UI', 'Open Sans', sans-serif;
                font-size: 13px;
                border: 2px solid #4db6ac;
                border-radius: 12px;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit {
                background-color: rgb(30, 30, 40);
                border: 1px solid rgba(77, 182, 172, 0.3);
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #00bcd4;
            }
            QPushButton {
                background-color: rgba(63, 81, 181, 0.3);
                border: 1px solid rgba(63, 81, 181, 0.5);
                border-radius: 6px;
                padding: 8px 16px;
                min-height: 32px;
                font-weight: 500;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: rgba(63, 81, 181, 0.4);
                border: 1px solid rgba(63, 81, 181, 0.7);
            }
            QListWidget {
                background-color: rgba(30, 30, 40, 0.8);
                border: 1px solid rgba(77, 182, 172, 0.3);
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(77, 182, 172, 0.1);
                border-radius: 4px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background-color: rgba(0, 188, 212, 0.3);
                border: 1px solid rgba(0, 188, 212, 0.5);
            }
            QFrame {
                background-color: rgba(40, 40, 50, 0.5);
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        self.setup_ui()
        
        # Cargar datos si se proporcionaron
        if shortcut_data:
            self.load_shortcut_data(shortcut_data)
    
    def get_text(self, key):
        """Obtiene texto traducido del language manager"""
        if self.language_manager:
            return self.language_manager.get_text(key)
        # Fallback en español si no hay language manager
        fallback_texts = {
            "ui.shortcut_editor.title": "Editor de Atajos Personalizados",
            "ui.shortcut_editor.create_shortcut": "🚀 Crear Atajo Personalizado",
            "ui.shortcut_editor.description": "Los atajos te permiten ejecutar múltiples comandos con una sola palabra. Por ejemplo, 'trabajo' puede abrir Chrome, tu carpeta de documentos y cambiar el modelo de IA.",
            "ui.shortcut_editor.shortcut_name": "Nombre del atajo:",
            "ui.shortcut_editor.shortcut_placeholder": "ej: trabajo, descanso, programar, estudiar",
            "ui.shortcut_editor.commands_to_execute": "📋 Comandos a ejecutar (en orden):",
            "ui.shortcut_editor.add_command": "➕ Añadir Comando",
            "ui.shortcut_editor.edit_command": "✏️ Editar",
            "ui.shortcut_editor.delete_command": "🗑️ Eliminar",
            "ui.shortcut_editor.test_shortcut": "🧪 Probar Atajo",
            "ui.shortcut_editor.save": "💾 Guardar",
            "ui.shortcut_editor.cancel": "❌ Cancelar",
            "ui.shortcut_editor.examples": "💡 Ejemplos de comandos: 'abre chrome', 'abre data', 'modelo phi3:mini', 'eva quien eres'"
        }
        return fallback_texts.get(key, key)

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Layout principal de la ventana
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(8, 8, 8, 4)

        # Contenedor para el contenido que será scrollable
        scrollable_content_widget = QWidget()
        scrollable_content_widget.setStyleSheet("background-color: rgb(25, 25, 35);")
        scrollable_content_layout = QVBoxLayout(scrollable_content_widget)
        scrollable_content_layout.setSpacing(12)
        scrollable_content_layout.setContentsMargins(16, 16, 16, 16)

        # QScrollArea para el contenido
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scrollable_content_widget)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        scroll_area.verticalScrollBar().setStyleSheet(
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

        # Usar scrollable_content_layout en lugar de layout para el contenido
        layout = scrollable_content_layout
        
        # Título y descripción
        title_label = QLabel(self.get_text("ui.shortcut_editor.create_shortcut"))
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #bb86fc; margin-bottom: 8px;")
        layout.addWidget(title_label)
        
        desc_label = QLabel(self.get_text("ui.shortcut_editor.description"))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #aaaaaa; margin-bottom: 12px;")
        layout.addWidget(desc_label)
        
        # Frame para configuración del atajo
        config_frame = QFrame()
        config_layout = QVBoxLayout(config_frame)
        
        # Nombre del atajo
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel(self.get_text("ui.shortcut_editor.shortcut_name")))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.get_text("ui.shortcut_editor.shortcut_placeholder"))
        name_layout.addWidget(self.name_input)
        config_layout.addLayout(name_layout)
        
        layout.addWidget(config_frame)
        
        # Frame para comandos
        commands_frame = QFrame()
        commands_layout = QVBoxLayout(commands_frame)
        
        commands_layout.addWidget(QLabel(self.get_text("ui.shortcut_editor.commands_to_execute")))
        
        self.commands_list = QListWidget()
        self.commands_list.setMinimumHeight(120)  # Más compacto para scroll
        commands_layout.addWidget(self.commands_list)
        
        # Botones para gestionar comandos
        cmd_btn_layout = QHBoxLayout()
        
        add_cmd_btn = QPushButton(self.get_text("ui.shortcut_editor.add_command"))
        add_cmd_btn.setStyleSheet("background-color: rgba(76, 175, 80, 0.3); border: 1px solid rgba(76, 175, 80, 0.5);")
        add_cmd_btn.clicked.connect(self.add_command)
        
        edit_cmd_btn = QPushButton(self.get_text("ui.shortcut_editor.edit_command"))
        edit_cmd_btn.setStyleSheet("background-color: rgba(255, 152, 0, 0.3); border: 1px solid rgba(255, 152, 0, 0.5);")
        edit_cmd_btn.clicked.connect(self.edit_command)
        
        delete_cmd_btn = QPushButton(self.get_text("ui.shortcut_editor.delete_command"))
        delete_cmd_btn.setStyleSheet("background-color: rgba(244, 67, 54, 0.3); border: 1px solid rgba(244, 67, 54, 0.5);")
        delete_cmd_btn.clicked.connect(self.delete_command)
        
        move_up_btn = QPushButton("⬆️")
        move_up_btn.setMaximumWidth(50)
        move_up_btn.clicked.connect(self.move_command_up)
        
        move_down_btn = QPushButton("⬇️")
        move_down_btn.setMaximumWidth(50)
        move_down_btn.clicked.connect(self.move_command_down)
        
        cmd_btn_layout.addWidget(add_cmd_btn)
        cmd_btn_layout.addWidget(edit_cmd_btn)
        cmd_btn_layout.addWidget(delete_cmd_btn)
        cmd_btn_layout.addStretch()
        cmd_btn_layout.addWidget(move_up_btn)
        cmd_btn_layout.addWidget(move_down_btn)
        
        commands_layout.addLayout(cmd_btn_layout)
        layout.addWidget(commands_frame)
        
        # Ejemplos de comandos
        examples_label = QLabel(self.get_text("ui.shortcut_editor.examples"))
        examples_label.setWordWrap(True)
        examples_label.setStyleSheet("font-size: 11px; color: #888888; margin: 6px 0;")
        layout.addWidget(examples_label)
        
        # Añadir scroll area al layout principal
        main_layout.addWidget(scroll_area)

        # Botones de acción fuera del área scrollable
        btn_frame = QFrame()
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 8, 0, 0)
        
        test_btn = QPushButton(self.get_text("ui.shortcut_editor.test_shortcut"))
        test_btn.setStyleSheet("background-color: rgba(33, 150, 243, 0.3); border: 1px solid rgba(33, 150, 243, 0.5);")
        test_btn.clicked.connect(self.test_shortcut)
        
        save_btn = QPushButton(self.get_text("ui.shortcut_editor.save"))
        save_btn.setStyleSheet(
            """
            background-color: rgba(76, 175, 80, 0.4);
            border: 1px solid rgba(76, 175, 80, 0.6);
            font-weight: 600;
            min-width: 70px;
            padding: 5px;
        """
        )
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton(self.get_text("ui.shortcut_editor.cancel"))
        cancel_btn.setStyleSheet(
            """
            background-color: rgba(244, 67, 54, 0.4);
            border: 1px solid rgba(244, 67, 54, 0.6);
            font-weight: 600;
            min-width: 70px;
            padding: 5px;
        """
        )
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(test_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        
        main_layout.addWidget(btn_frame)

    def add_command(self):
        """Añade un nuevo comando a la lista"""
        command, ok = QInputDialog.getText(
            self, 
            self.get_text("ui.shortcut_editor.add_command_dialog"), 
            self.get_text("ui.shortcut_editor.add_command_prompt"),
            text=""
        )
        
        if ok and command.strip():
            command = command.strip()
            self.commands.append(command)
            self.update_commands_list()

    def edit_command(self):
        """Edita el comando seleccionado"""
        current_row = self.commands_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, self.get_text("ui.shortcut_editor.selection_required"), self.get_text("ui.shortcut_editor.select_command_edit"))
            return
        
        current_command = self.commands[current_row]
        command, ok = QInputDialog.getText(
            self, 
            self.get_text("ui.shortcut_editor.edit_command_dialog"), 
            self.get_text("ui.shortcut_editor.edit_command_prompt"),
            text=current_command
        )
        
        if ok and command.strip():
            self.commands[current_row] = command.strip()
            self.update_commands_list()

    def delete_command(self):
        """Elimina el comando seleccionado"""
        current_row = self.commands_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, self.get_text("ui.shortcut_editor.selection_required"), self.get_text("ui.shortcut_editor.select_command_delete"))
            return
        
        reply = QMessageBox.question(
            self, 
            self.get_text("ui.shortcut_editor.delete_confirm"), 
            self.get_text("ui.shortcut_editor.delete_confirm_text").format(command=self.commands[current_row]),
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.commands[current_row]
            self.update_commands_list()

    def move_command_up(self):
        """Mueve el comando seleccionado hacia arriba"""
        current_row = self.commands_list.currentRow()
        if current_row <= 0:
            return
        
        # Intercambiar comandos
        self.commands[current_row], self.commands[current_row - 1] = \
            self.commands[current_row - 1], self.commands[current_row]
        
        self.update_commands_list()
        self.commands_list.setCurrentRow(current_row - 1)

    def move_command_down(self):
        """Mueve el comando seleccionado hacia abajo"""
        current_row = self.commands_list.currentRow()
        if current_row < 0 or current_row >= len(self.commands) - 1:
            return
        
        # Intercambiar comandos
        self.commands[current_row], self.commands[current_row + 1] = \
            self.commands[current_row + 1], self.commands[current_row]
        
        self.update_commands_list()
        self.commands_list.setCurrentRow(current_row + 1)

    def update_commands_list(self):
        """Actualiza la lista visual de comandos"""
        self.commands_list.clear()
        for i, command in enumerate(self.commands):
            item = QListWidgetItem(f"{i+1}. {command}")
            self.commands_list.addItem(item)

    def test_shortcut(self):
        """Prueba el atajo mostrando qué comandos se ejecutarían"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, self.get_text("ui.shortcut_editor.name_required"), self.get_text("ui.shortcut_editor.name_required_text"))
            return
        
        if not self.commands:
            QMessageBox.warning(self, self.get_text("ui.shortcut_editor.commands_required"), self.get_text("ui.shortcut_editor.commands_required_text"))
            return
        
        commands_text = "\n".join([f"• {cmd}" for cmd in self.commands])
        QMessageBox.information(
            self,
            self.get_text("ui.shortcut_editor.test_title").format(name=name),
            self.get_text("ui.shortcut_editor.test_message").format(name=name, commands=commands_text)
        )

    def load_shortcut_data(self, data):
        """Carga datos de un atajo existente"""
        if "name" in data:
            self.name_input.setText(data["name"])
        
        if "commands" in data:
            if isinstance(data["commands"], list):
                self.commands = data["commands"].copy()
            elif isinstance(data["commands"], str):
                self.commands = [data["commands"]]
            else:
                self.commands = []
            
            self.update_commands_list()

    def get_shortcut_data(self):
        """Obtiene los datos del atajo configurado"""
        name = self.name_input.text().strip()
        if not name or not self.commands:
            return None
        
        return {
            "name": name,
            "commands": self.commands.copy()
        }

    def accept(self):
        """Valida y acepta el diálogo"""
        name = self.name_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, self.get_text("ui.shortcut_editor.name_required"), self.get_text("ui.shortcut_editor.name_required_text"))
            return
        
        if not self.commands:
            QMessageBox.warning(self, self.get_text("ui.shortcut_editor.commands_required"), self.get_text("ui.shortcut_editor.commands_required_text"))
            return
        
        # Validar que el nombre no contenga caracteres especiales
        import re
        if not re.match(r'^[a-zA-Z0-9áéíóúñü\s]+$', name):
            QMessageBox.warning(
                self, 
                self.get_text("ui.shortcut_editor.invalid_name"), 
                self.get_text("ui.shortcut_editor.invalid_name_text")
            )
            return
        
        super().accept()