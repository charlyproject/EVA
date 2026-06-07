#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz de Notificación de Actualizaciones para EVA
Diálogo moderno para mostrar actualizaciones disponibles
"""

import webbrowser
import logging
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QTextEdit, QCheckBox, QFrame,
                               QProgressBar)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal

logger = logging.getLogger('EVA.UpdateNotification')

class ModernButton(QPushButton):
    """Botón moderno con efectos hover"""
    def __init__(self, text, button_type="normal"):
        super().__init__(text)
        self.button_type = button_type
        self.setup_style()
    
    def setup_style(self):
        if self.button_type == "primary":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #3d8b40;
                }
            """)
        elif self.button_type == "secondary":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
                QPushButton:pressed {
                    background-color: #1565C0;
                }
            """)
        elif self.button_type == "danger":
            self.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
                QPushButton:pressed {
                    background-color: #c62828;
                }
            """)
        else:  # normal
            self.setStyleSheet("""
                QPushButton {
                    background-color: #757575;
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #616161;
                }
                QPushButton:pressed {
                    background-color: #424242;
                }
            """)

class UpdateNotificationDialog(QDialog):
    """Diálogo moderno para notificaciones de actualización"""
    
    # Señales para comunicar la decisión del usuario
    update_accepted = Signal()
    update_postponed = Signal(int)  # horas a posponer
    update_skipped = Signal(str)    # versión a omitir
    
    def __init__(self, update_info, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.setup_ui()
        self.setup_animations()
        
        logger.info(f"Mostrando notificación de actualización para v{update_info['version']}")
        
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self.setWindowTitle("Nueva Actualización Disponible - EVA")
        self.setFixedSize(550, 500)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.WindowCloseButtonHint)
        
        # Estilo general del diálogo
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                border-radius: 10px;
            }
            QLabel {
                color: #333333;
            }
            QTextEdit {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QCheckBox {
                color: #666666;
                font-size: 12px;
            }
            QFrame {
                background-color: white;
                border-radius: 8px;
            }
        """)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Header con icono y título
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #2196F3; border-radius: 8px;")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        # Icono de actualización (usando texto como icono)
        icon_label = QLabel("🔄")
        icon_label.setStyleSheet("color: white; font-size: 32px;")
        header_layout.addWidget(icon_label)
        
        # Título y versión
        title_layout = QVBoxLayout()
        title_label = QLabel("Nueva Actualización Disponible")
        title_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        
        version_label = QLabel(f"EVA v{self.update_info['version']}")
        version_label.setStyleSheet("color: #E3F2FD; font-size: 14px;")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        header_layout.addLayout(title_layout)
        
        header_layout.addStretch()
        
        # Indicador de actualización crítica
        if self.update_info.get('is_critical', False):
            critical_label = QLabel("CRÍTICA")
            critical_label.setStyleSheet("""
                background-color: #f44336; 
                color: white; 
                padding: 4px 8px; 
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            """)
            header_layout.addWidget(critical_label)
        
        main_layout.addWidget(header_frame)
        
        # Información de la actualización
        info_frame = QFrame()
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(20, 20, 20, 20)
        
        # Fecha de lanzamiento
        if self.update_info.get('release_date'):
            date_label = QLabel(f"📅 Fecha de lanzamiento: {self.update_info['release_date'][:10]}")
            date_label.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 10px;")
            info_layout.addWidget(date_label)
        
        # Descripción de cambios
        changes_label = QLabel("📝 Novedades y mejoras:")
        changes_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        info_layout.addWidget(changes_label)
        
        self.description_text = QTextEdit()
        self.description_text.setPlainText(self.update_info.get('description', 'Nueva versión disponible con mejoras y correcciones.'))
        self.description_text.setMaximumHeight(150)
        self.description_text.setReadOnly(True)
        info_layout.addWidget(self.description_text)
        
        # Información adicional
        additional_info = QHBoxLayout()
        
        # Tamaño de descarga (si está disponible)
        if self.update_info.get('size', 0) > 0:
            size_mb = self.update_info['size'] / (1024 * 1024)
            size_label = QLabel(f"💾 Tamaño: {size_mb:.1f} MB")
            size_label.setStyleSheet("color: #666; font-size: 12px;")
            additional_info.addWidget(size_label)
        
        additional_info.addStretch()
        info_layout.addLayout(additional_info)
        
        main_layout.addWidget(info_frame)
        
        # Opciones del usuario
        options_frame = QFrame()
        options_layout = QVBoxLayout(options_frame)
        options_layout.setContentsMargins(20, 15, 20, 15)
        
        # Checkbox para recordar decisión
        self.remember_choice = QCheckBox("No volver a mostrar notificaciones para esta versión")
        self.remember_choice.setStyleSheet("margin-bottom: 15px;")
        options_layout.addWidget(self.remember_choice)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("color: #ddd;")
        options_layout.addWidget(separator)
        
        main_layout.addWidget(options_frame)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        # Botón principal - Descargar
        self.download_btn = ModernButton("🔗 Ir a Gumroad", "primary")
        self.download_btn.clicked.connect(self.download_update)
        button_layout.addWidget(self.download_btn)
        
        # Botón secundario - Más tarde
        self.later_btn = ModernButton("⏰ Recordar en 24h", "secondary")
        self.later_btn.clicked.connect(self.remind_later)
        button_layout.addWidget(self.later_btn)
        
        # Botón omitir - Solo si no es crítica
        if not self.update_info.get('is_critical', False):
            self.skip_btn = ModernButton("❌ Omitir Versión", "danger")
            self.skip_btn.clicked.connect(self.skip_version)
            button_layout.addWidget(self.skip_btn)
        
        main_layout.addLayout(button_layout)
        
        # Información adicional en la parte inferior
        footer_label = QLabel("💡 La actualización se descargará desde Gumroad. Cierra EVA antes de instalar.")
        footer_label.setStyleSheet("color: #888; font-size: 11px; text-align: center; margin-top: 10px;")
        footer_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer_label)
        
        self.setLayout(main_layout)
        
    def setup_animations(self):
        """Configura animaciones para el diálogo"""
        # Animación de entrada
        self.setWindowOpacity(0)
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Iniciar animación cuando se muestre
        QTimer.singleShot(50, self.fade_in_animation.start)
        
    def download_update(self):
        """Abre el enlace de descarga en Gumroad"""
        try:
            gumroad_url = self.update_info.get('gumroad_url', 'https://gumroad.com/l/eva-assistant')
            webbrowser.open(gumroad_url)
            logger.info(f"Abriendo enlace de descarga: {gumroad_url}")
            
            # Emitir señal y cerrar
            self.update_accepted.emit()
            self.accept()
            
        except Exception as e:
            logger.error(f"Error abriendo enlace de descarga: {str(e)}")
            
    def remind_later(self):
        """Pospone la notificación por 24 horas"""
        hours = 24
        logger.info(f"Usuario eligió recordar en {hours} horas")
        
        # Emitir señal con las horas a posponer
        self.update_postponed.emit(hours)
        self.done(1)  # Código para "más tarde"
        
    def skip_version(self):
        """Omite esta versión permanentemente"""
        version = self.update_info['version']
        logger.info(f"Usuario eligió omitir versión {version}")
        
        # Emitir señal con la versión a omitir
        self.update_skipped.emit(version)
        self.done(2)  # Código para "omitir"
        
    def closeEvent(self, event):
        """Maneja el cierre del diálogo"""
        # Si se cierra sin elegir opción, tratar como "más tarde"
        if not self.result():
            self.remind_later()
        event.accept()

class UpdateProgressDialog(QDialog):
    """Diálogo para mostrar progreso de descarga (para uso futuro)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz del diálogo de progreso"""
        self.setWindowTitle("Descargando Actualización - EVA")
        self.setFixedSize(400, 150)
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Etiqueta de estado
        self.status_label = QLabel("Preparando descarga...")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Botón cancelar
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self.cancel_btn)
        
        self.setLayout(layout)
        
    def update_progress(self, value, status=""):
        """Actualiza el progreso de la descarga"""
        self.progress_bar.setValue(value)
        if status:
            self.status_label.setText(status)