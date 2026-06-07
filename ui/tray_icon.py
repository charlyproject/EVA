import logging
import os
import sys
import tempfile
import shutil
import time
from pathlib import Path

from PySide6.QtCore import Signal, QTimer
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QStyle, QSystemTrayIcon

# Configuración de directorios temporales
def setup_temp_dirs():
    """Configura los directorios temporales de la aplicación"""
    try:
        # Directorio temporal principal
        temp_dir = Path(tempfile.gettempdir()) / 'eva'
        temp_dir.mkdir(exist_ok=True, parents=True)
        
        # Directorio para archivos temporales de sesión
        session_temp = temp_dir / 'session_temp'
        session_temp.mkdir(exist_ok=True)
        
        # Limpiar archivos temporales antiguos (mayores a 1 día)
        cleanup_old_files(temp_dir, days=1)
        
        # Establecer permisos
        os.chmod(temp_dir, 0o777)
        os.chmod(session_temp, 0o777)
        
        return str(session_temp)
    except Exception as e:
        logging.error(f"Error configurando directorios temporales: {e}")
        return None

def cleanup_old_files(directory, days=1):
    """Elimina archivos más antiguos que el número de días especificado"""
    try:
        now = time.time()
        cutoff = now - (days * 86400)
        
        for f in Path(directory).glob('*'):
            try:
                if f.is_file() and f.stat().st_mtime < cutoff:
                    f.unlink()
                elif f.is_dir():
                    # Eliminar directorios vacíos
                    if not any(f.iterdir()):
                        f.rmdir()
            except Exception as e:
                logging.warning(f"No se pudo eliminar {f}: {e}")
    except Exception as e:
        logging.error(f"Error limpiando archivos antiguos: {e}")

# Configurar directorios temporales al importar
TEMP_DIR = setup_temp_dirs()

logger = logging.getLogger("EVA")

class SystemTrayIcon(QSystemTrayIcon):
    show_window = Signal()
    hide_window = Signal()
    exit_requested = Signal()

    def __init__(self, language_manager=None, parent=None, eva=None):
        super().__init__(parent)
        self.language_manager = language_manager
        self.eva = eva
        self._build_menu()
        self._update_tooltip()
        self.activated.connect(self._on_icon_activated)
        
        # Connect to language changes if language manager is available
        if self.language_manager:
            self.language_manager.language_changed.connect(self._on_language_changed)

    def _build_menu(self):
        """Construye el menú contextual del icono de sistema con estilo sombreado."""
        menu = QMenu()

        # Aplicar estilo personalizado al menú
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(30, 30, 30, 230);
                border: 1px solid #555;
                padding: 6px;
                border-radius: 8px;
            }
            QMenu::item {
                color: #e0f0ff;
                padding: 6px 8px 6px 6px;
                background-color: transparent;
            }
            QMenu::item:selected {
                background-color: rgba(100, 100, 120, 180);
                border-radius: 4px;
            }
        """)

        # Use language manager for menu items
        show_text = self._get_text("ui.tray.show", "Mostrar interfaz")
        hide_text = self._get_text("ui.tray.hide", "Ocultar interfaz")
        mini_text = self._get_text("ui.tray.show_mini", "Mostrar mini barra")
        exit_text = self._get_text("ui.tray.exit", "Salir de EVA")

        # Create actions with SVG icons
        self.action_show = QAction(show_text, self)
        self.action_show.setIcon(self._load_tray_icon("show.svg"))
        self.action_show.triggered.connect(self.show_window.emit)
        menu.addAction(self.action_show)

        self.action_hide = QAction(hide_text, self)
        self.action_hide.setIcon(self._load_tray_icon("hide.svg"))
        self.action_hide.triggered.connect(self.hide_window.emit)
        menu.addAction(self.action_hide)

        menu.addSeparator()

        self.action_show_mini = QAction(mini_text, self)
        self.action_show_mini.setIcon(self._load_tray_icon("show.svg"))
        self.action_show_mini.triggered.connect(self._show_mini_bar)
        menu.addAction(self.action_show_mini)

        menu.addSeparator()

        self.action_exit = QAction(exit_text, self)
        self.action_exit.setIcon(self._load_tray_icon("exit.svg"))
        self.action_exit.triggered.connect(self.exit_requested.emit)
        menu.addAction(self.action_exit)

        self.setContextMenu(menu)

    def _get_text(self, key, fallback):
        """Get text from language manager with fallback"""
        if self.language_manager:
            try:
                return self.language_manager.get_text(key)
            except Exception as e:
                logger.debug(f"Error getting text for key '{key}': {e}")
                return fallback
        return fallback

    def _load_tray_icon(self, svg_filename):
        """Load SVG icon for tray menu"""
        try:
            svg_path = os.path.join("resources", "icons", "tray", svg_filename)
            if os.path.exists(svg_path):
                return QIcon(svg_path)
            else:
                return QIcon()  # Empty icon if not found
        except Exception as e:
            logger.error(f"Error loading SVG icon {svg_filename}: {e}")
            return QIcon()

    def _update_tooltip(self):
        """Update tooltip text - ALWAYS use same title regardless of language"""
        # FIXED: Tooltip is ALWAYS "EVA - Enhancement Assistant Voice" regardless of language
        self.setToolTip("EVA - Enhancement Assistant Voice")

    def _on_language_changed(self):
        """Handle language change by rebuilding menu and updating tooltip"""
        self._build_menu()
        self._update_tooltip()

    def _on_icon_activated(self, reason):
        """Manejador de eventos para clics sobre el icono."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window.emit()

    def _show_mini_bar(self):
        if self.eva:
            self.eva._create_mini_bar()
            if self.eva.mini_bar:
                self.eva.mini_bar.show()
                self.eva.mini_bar.activateWindow()
                self.eva.mini_bar.raise_()

    def showMessage(self, title, message, icon=QSystemTrayIcon.Information, msecs=5000):
        """Muestra una notificación con ubicación y formato ajustados."""
        super().showMessage(title, message, icon, msecs)
        self.contextMenu().adjustSize()


def create_tray_icon(app, chat_window, config, language_manager=None, eva=None):
    tray_icon = SystemTrayIcon(language_manager, app, eva=eva)

    # Establecer icono personalizado si existe
    icon_path = os.path.join("resources", "icon.ico")
    if os.path.exists(icon_path):
        tray_icon.setIcon(QIcon(icon_path))
    else:
        tray_icon.setIcon(app.style().standardIcon(QStyle.SP_ComputerIcon))
        logger.warning("Icono personalizado no encontrado. Usando icono por defecto.")

    def show_chat_window():
        """Lógica para mostrar la ventana principal del asistente con manejo correcto de estado minimizado."""
        from PySide6.QtCore import QTimer
        
        try:
            # Forzar estado de pintura válido antes de cualquier operación
            if hasattr(chat_window, 'valid_paint_state'):
                chat_window.valid_paint_state = True
            
            if chat_window.isHidden():
                chat_window.show()
            elif chat_window.isMinimized():
                # Para ventanas minimizadas, usar secuencia específica para evitar errores de QPainter
                chat_window.showNormal()
                # Asegurar que la ventana esté completamente restaurada antes de continuar
                QTimer.singleShot(100, lambda: chat_window.activateWindow())
                QTimer.singleShot(150, lambda: chat_window.raise_())
                if hasattr(chat_window, 'message_input'):
                    QTimer.singleShot(200, lambda: chat_window.message_input.setFocus())
                return
            
            # Para ventanas ocultas, usar timing normal
            def delayed_activation():
                try:
                    if chat_window.isVisible():
                        chat_window.activateWindow()
                        chat_window.raise_()
                        if hasattr(chat_window, 'message_input'):
                            chat_window.message_input.setFocus()
                except Exception as e:
                    logger.error(f"Error en delayed_activation: {str(e)}")
            
            QTimer.singleShot(50, delayed_activation)
            logger.info("Ventana de chat mostrada desde tray icon")
            
        except Exception as e:
            logger.error(f"Error mostrando ventana desde tray: {str(e)}")
            # Como último recurso, intentar mostrar sin verificaciones
            try:
                chat_window.show()
                chat_window.raise_()
            except Exception as e:
                logger.error(f"Error showing chat window: {e}")
                pass

    # Conectar señales a acciones
    tray_icon.show_window.connect(show_chat_window)
    tray_icon.hide_window.connect(chat_window.hide)
    
    def safe_exit():
        """
        Función de salida robusta que maneja tanto Python como ejecutables.
        Se encarga de cerrar correctamente todos los recursos antes de salir.
        """
        logger.info("=== Iniciando secuencia de cierre controlado ===")
        is_frozen = getattr(sys, 'frozen', False)
        
        try:
            # 1. Deshabilitar más interacciones del usuario
            app.setQuitOnLastWindowClosed(False)
            
            # 2. Cerrar la ventana principal de forma segura
            if hasattr(chat_window, 'close'):
                try:
                    logger.info("Cerrando ventana principal...")
                    chat_window.hide()  # Ocultar primero para mejor experiencia de usuario
                    chat_window.close()
                    chat_window.deleteLater()
                    logger.info("Ventana principal cerrada")
                except Exception as e:
                    logger.error(f"Error cerrando ventana principal: {e}")
            
            # 3. Procesar eventos pendientes
            logger.info("Procesando eventos pendientes...")
            app.processEvents()
            
            # 4. Cerrar todas las ventanas restantes
            logger.info("Cerrando ventanas restantes...")
            for widget in app.topLevelWidgets():
                try:
                    if widget != chat_window:  # Ya cerramos la ventana principal
                        widget.close()
                        widget.deleteLater()
                except Exception as e:
                    logger.warning(f"Error cerrando widget {widget}: {e}")
            
            # 5. Limpieza de recursos
            try:
                logger.info("Realizando limpieza de recursos...")
                
                # Limpiar temporales de la sesión
                if TEMP_DIR and os.path.exists(TEMP_DIR):
                    try:
                        shutil.rmtree(TEMP_DIR, ignore_errors=True)
                        logger.info("Directorio temporal de sesión eliminado")
                    except Exception as e:
                        logger.warning(f"Error eliminando directorio temporal: {e}")
                
                # Limpiar temporales antiguos
                temp_dir = Path(tempfile.gettempdir()) / 'eva'
                if temp_dir.exists():
                    cleanup_old_files(temp_dir, days=1)
                
            except Exception as e:
                logger.error(f"Error en limpieza de recursos: {e}")
            
            # 6. Forzar recolección de basura
            logger.info("Limpiando memoria...")
            import gc
            gc.collect()
            
            # 7. Notificar cierre a la aplicación
            logger.info("Notificando cierre a la aplicación...")
            if hasattr(app, 'aboutToQuit'):
                app.aboutToQuit.emit()
            
            # 8. Manejo diferente para modo ejecutable vs desarrollo
            if is_frozen:
                logger.info("Modo ejecutable - Iniciando cierre forzado...")
                # Para ejecutables, usar un enfoque más directo
                try:
                    # Cerrar el ícono de la bandeja primero
                    tray_icon.hide()
                    tray_icon.deleteLater()
                    
                    # Dar tiempo para que se procesen los eventos
                    QTimer.singleShot(100, lambda: None)
                    app.processEvents()
                    
                    # Forzar cierre después de un breve retraso
                    def force_quit():
                        try:
                            app.quit()
                        except Exception as e:
                            logger.error(f"Error forzando cierre de app: {e}")
                        os._exit(0)
                    
                    QTimer.singleShot(500, force_quit)
                    
                except Exception as e:
                    logger.error(f"Error en cierre forzado: {e}")
                    os._exit(1)
            else:
                # Modo desarrollo - cierre normal
                logger.info("Modo desarrollo - Cerrando aplicación...")
                app.quit()
            
        except Exception as e:
            logger.critical(f"ERROR CRÍTICO durante el cierre: {e}")
            logger.exception("Detalles del error:")
            try:
                if is_frozen:
                    os._exit(1)
                else:
                    app.quit()
            except Exception as e:
                logger.error(f"Error final de cierre: {e}")
                if is_frozen:
                    os._exit(1)
        finally:
            if is_frozen:
                os._exit(0)
    
    tray_icon.exit_requested.connect(safe_exit)

    tray_icon.show()

    # Notificación inicial de presencia usando language manager
    background_title = tray_icon._get_text("ui.tray.background_message", "EVA en segundo plano")
    background_desc = tray_icon._get_text("ui.tray.background_description", "EVA está activa. Haz clic derecho en el icono para más opciones.")
    
    tray_icon.showMessage(
        background_title,
        background_desc,
        QSystemTrayIcon.Information,
        3000
    )

    return tray_icon
