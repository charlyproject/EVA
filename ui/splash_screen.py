import os
import logging
import json
from PySide6.QtWidgets import QSplashScreen
from PySide6.QtCore import Qt, QTimer, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QPainter, QFont, QColor, QLinearGradient, QPen

logger = logging.getLogger("EVA")


class EVASplashScreen(QSplashScreen):
    """Pantalla de carga personalizada para EVA con animaciones y progreso"""
    
    progress_updated = Signal(int, str)  # progreso, mensaje
    
    def __init__(self):
        # Detectar idioma antes de inicializar
        self.language = self._detect_startup_language()
        self.messages = self._load_splash_messages()
        # Obtener dimensiones del icono original y reducir 40%
        try:
            from core.dynamic_path_resolver import dynamic_path_resolver
            icon_path = dynamic_path_resolver.get_icon_path("png")
        except ImportError:
            icon_path = os.path.join("resources", "icon.png")
        if os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path)
            if not icon_pixmap.isNull():
                # Reducir a un tamaño manejable manteniendo alta calidad
                original_width = icon_pixmap.width()
                original_height = icon_pixmap.height()
                # Usar 50% del tamaño original para balance entre calidad y tamaño
                self.splash_width = int(original_width * 0.5)
                self.splash_height = int(original_height * 0.5)
            else:
                # Fallback si no se puede cargar
                self.splash_width, self.splash_height = 240, 180  # 40% más pequeño que 400x300
        else:
            # Fallback si no existe el archivo
            self.splash_width, self.splash_height = 240, 180
        
        # Crear pixmap simple con las dimensiones del icono original
        simple_pixmap = QPixmap(self.splash_width, self.splash_height)
        simple_pixmap.fill(QColor(25, 25, 35))
        super().__init__(simple_pixmap, Qt.WindowStaysOnTopHint)
        
        # Configuración de la ventana
        self.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        # Removido WA_TranslucentBackground para evitar transparencia inicial
        
        # Variables de estado
        self.current_progress = 0
        self.current_message = self.messages.get("initializing", "Iniciando EVA...")
        self.fade_opacity = 1.0
        self.splash_pixmap = None  # Se creará después
        
        # Configurar animación de fade más rápida
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)  # Más rápido
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Timer para actualizar animaciones (menos frecuente)
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(100)  # 10 FPS para menos carga
        
        # Contador para animación de puntos
        self.dot_counter = 0
        
        # Crear pixmap complejo después de mostrar
        QTimer.singleShot(50, self._create_full_pixmap)
        
        logger.info(f"Splash screen inicializado en idioma: {self.language}")
    
    def _detect_startup_language(self):
        """Detecta el idioma que EVA va a usar al arrancar"""
        try:
            # Prioridad 1: Verificar paths.json (configuración principal)
            try:
                from core.dynamic_path_resolver import dynamic_path_resolver
                paths_config_path = dynamic_path_resolver.get_config_file('paths')
            except ImportError:
                paths_config_path = os.path.join("config", "paths.json")
            if os.path.exists(paths_config_path):
                with open(paths_config_path, "r", encoding="utf-8") as f:
                    paths_config = json.load(f)
                    if "language" in paths_config and paths_config["language"] in ["es", "en"]:
                        logger.info(f"Idioma detectado desde paths.json: {paths_config['language']}")
                        return paths_config["language"]
            
            # Prioridad 2: Verificar install_config.json
            try:
                install_config_path = dynamic_path_resolver.get_config_file('install')
            except NameError:
                install_config_path = os.path.join("config", "install_config.json")
            if os.path.exists(install_config_path):
                with open(install_config_path, "r", encoding="utf-8") as f:
                    install_config = json.load(f)
                    if "language" in install_config and install_config["language"] in ["es", "en"]:
                        logger.info(f"Idioma detectado desde install_config.json: {install_config['language']}")
                        return install_config["language"]
            
            # Prioridad 3: Verificar default_language en paths.json
            try:
                if os.path.exists(paths_config_path):
                    with open(paths_config_path, "r", encoding="utf-8") as f:
                        paths_config = json.load(f)
                        if "default_language" in paths_config and paths_config["default_language"] in ["es", "en"]:
                            logger.info(f"Idioma detectado desde default_language: {paths_config['default_language']}")
                            return paths_config["default_language"]
            except Exception as e:
                logger.warning(f"Error reading paths config: {str(e)}")
            
            # Fallback: Español por defecto
            logger.info("No se encontró configuración de idioma, usando español por defecto")
            return "es"
            
        except Exception as e:
            logger.error(f"Error detectando idioma de arranque: {str(e)}")
            return "es"
    
    def _load_splash_messages(self):
        """Carga los mensajes del splash screen según el idioma detectado"""
        messages = {
            "es": {
                "initializing": "Iniciando EVA...",
                "loading_config": "Cargando configuración",
                "init_language": "Inicializando sistema de idiomas",
                "checking_license": "Verificando licencia",
                "setting_session": "Configurando sesión",
                "creating_ui": "Creando interfaz de usuario",
                "setting_processor": "Configurando procesador de comandos",
                "preparing_voice": "Omitiendo sistemas de voz temporalmente",
                "preparing_speech": "Preparando síntesis de voz",
                "setting_voice": "Configurando sistema de voz",
                "setting_tray": "Configurando bandeja del sistema",
                "setting_hotkeys": "Configurando atajos de teclado",
                "setting_cache": "Configurando cache",
                "setting_updates": "Configurando sistema de actualizaciones",
                "optimizing_knowledge": "Optimizando base de conocimiento",
                "setting_errors": "Configurando manejo de errores",
                "eva_ready": "¡EVA listo!"
            },
            "en": {
                "initializing": "Starting EVA...",
                "loading_config": "Loading configuration",
                "init_language": "Initializing language system",
                "checking_license": "Checking license",
                "setting_session": "Setting up session",
                "creating_ui": "Creating user interface",
                "setting_processor": "Setting up command processor",
                "preparing_voice": "Skipping voice systems temporarily",
                "preparing_speech": "Preparing speech synthesis",
                "setting_voice": "Setting up voice system",
                "setting_tray": "Setting up system tray",
                "setting_hotkeys": "Setting up keyboard shortcuts",
                "setting_cache": "Setting up cache",
                "setting_updates": "Setting up update system",
                "optimizing_knowledge": "Optimizing knowledge base",
                "setting_errors": "Setting up error handling",
                "eva_ready": "EVA ready!"
            }
        }
        
        return messages.get(self.language, messages["es"])
    
    def _create_splash_pixmap(self):
        """Crea el pixmap base para el splash screen usando las dimensiones del icono original"""
        width, height = self.splash_width, self.splash_height
        
        # Crear pixmap con las dimensiones exactas del icono
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        # Activar todas las mejoras de renderizado
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setRenderHint(QPainter.LosslessImageRendering, True)
        
        # Fondo con gradiente suave
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, QColor(30, 30, 50))
        gradient.setColorAt(1, QColor(10, 10, 20))
        painter.fillRect(pixmap.rect(), gradient)
        
        # Cargar y dibujar icono de EVA escalado dejando espacio para el marco
        icon_path = os.path.join("resources", "icon.png")
        if os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path)
            if not icon_pixmap.isNull():
                # Reducir el tamaño del icono para dejar espacio al marco
                margin = 6  # Espacio para el marco
                icon_width = width - (margin * 2)
                icon_height = height - (margin * 2)
                
                scaled_icon = icon_pixmap.scaled(
                    icon_width, icon_height,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                
                # Centrar el icono con margen
                icon_x = (width - scaled_icon.width()) // 2
                icon_y = (height - scaled_icon.height()) // 2
                painter.drawPixmap(icon_x, icon_y, scaled_icon)
        
        # Marco cyan con borde redondeado - DESPUÉS del icono para que sea visible
        pen_width = 4  # Más grueso para mejor visibilidad
        border_radius = 15
        painter.setPen(QPen(QColor(0, 188, 212), pen_width))  # Cyan más vibrante
        painter.setBrush(Qt.NoBrush)  # Sin relleno para que sea solo el borde
        painter.drawRoundedRect(pixmap.rect().adjusted(2, 2, -2, -2), border_radius, border_radius)
        
        painter.end()
        return pixmap
    
    def _create_full_pixmap(self):
        """Crea el pixmap completo de forma asíncrona"""
        try:
            self.splash_pixmap = self._create_splash_pixmap()
            self.update()  # Forzar repintado con el nuevo pixmap
        except Exception as e:
            logger.error(f"Error creando pixmap completo: {str(e)}")
            # Fallback: usar pixmap simple
            self.splash_pixmap = self.pixmap()
    
    def update_progress(self, progress, message=""):
        """Actualiza el progreso y mensaje del splash screen"""
        self.current_progress = max(0, min(100, progress))
        if message:
            self.current_message = message
        
        # Forzar repintado
        self.update()
        
        # Procesar eventos para mantener la UI responsiva
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        logger.debug(f"Splash progress: {self.current_progress}% - {self.current_message}")
    
    def update_animation(self):
        """Actualiza las animaciones del splash screen"""
        self.dot_counter = (self.dot_counter + 1) % 40  # Ciclo de 2 segundos a 20 FPS
        self.update()
    
    def paintEvent(self, event):
        """Dibuja el splash screen con progreso y animaciones"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Dibujar pixmap base (usar el que esté disponible)
        if self.splash_pixmap:
            painter.drawPixmap(0, 0, self.splash_pixmap)
        else:
            # Fallback: dibujar fondo simple mientras se carga
            painter.fillRect(self.rect(), QColor(25, 25, 35))
        
        # Obtener dimensiones actuales de la ventana
        window_width = self.width()
        window_height = self.height()
        
        # Barra de progreso más visible y proporcionada
        progress_rect_width = int(window_width * 0.7)  # 70% del ancho
        progress_rect_height = max(8, int(window_height * 0.025))  # Más gruesa y visible
        progress_rect_x = (window_width - progress_rect_width) // 2
        progress_rect_y = window_height - max(80, int(window_height * 0.18))  # Más espacio desde abajo
        
        # Fondo de la barra de progreso
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(40, 40, 60))
        painter.drawRoundedRect(
            progress_rect_x, progress_rect_y, 
            progress_rect_width, progress_rect_height, 3, 3
        )
        
        # Barra de progreso activa
        if self.current_progress > 0:
            progress_width = int((progress_rect_width * self.current_progress) / 100)
            gradient = QLinearGradient(progress_rect_x, 0, progress_rect_x + progress_width, 0)
            gradient.setColorAt(0, QColor(0, 188, 212))
            gradient.setColorAt(1, QColor(77, 182, 172))
            painter.setBrush(gradient)
            painter.drawRoundedRect(
                progress_rect_x, progress_rect_y, 
                progress_width, progress_rect_height, 3, 3
            )
        
        # Mensaje de estado más visible
        painter.setPen(QColor(255, 255, 255, 240))
        status_font_size = max(10, min(14, int(window_height * 0.03)))  # Fuente más grande
        status_font = QFont("Segoe UI", status_font_size)
        status_font.setHintingPreference(QFont.PreferFullHinting)
        painter.setFont(status_font)
        
        # Añadir puntos animados al mensaje
        dots = "." * (1 + (self.dot_counter // 10) % 3)
        animated_message = f"{self.current_message}{dots}"
        
        message_rect = painter.fontMetrics().boundingRect(animated_message)
        message_x = (window_width - message_rect.width()) // 2
        message_y = window_height - max(40, int(window_height * 0.1))  # Más espacio
        painter.drawText(message_x, message_y, animated_message)
        
        # Porcentaje de progreso más visible arriba de la barra
        if self.current_progress > 0:
            painter.setPen(QColor(0, 188, 212))  # Cyan más vibrante
            progress_font_size = max(9, min(12, int(window_height * 0.025)))  # Fuente más grande
            progress_font = QFont("Segoe UI", progress_font_size, QFont.Bold)
            progress_font.setHintingPreference(QFont.PreferFullHinting)
            painter.setFont(progress_font)
            progress_text = f"{self.current_progress}%"
            progress_text_rect = painter.fontMetrics().boundingRect(progress_text)
            progress_text_x = (window_width - progress_text_rect.width()) // 2
            progress_text_y = progress_rect_y - max(15, int(window_height * 0.03))  # Más separación
            painter.drawText(progress_text_x, progress_text_y, progress_text)
    
    def fade_out(self, callback=None):
        """Desvanece el splash screen y ejecuta callback al terminar"""
        self.animation_timer.stop()
        
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        
        if callback:
            self.fade_animation.finished.connect(callback)
        
        self.fade_animation.finished.connect(self.close)
        self.fade_animation.start()
        
        logger.info("Iniciando fade out del splash screen")
    
    def show_with_fade(self):
        """Muestra el splash screen inmediatamente sin fade in"""
        self.setWindowOpacity(1.0)  # Mostrar inmediatamente
        self.show()
        
        logger.info("Splash screen mostrado inmediatamente")
    
    def closeEvent(self, event):
        """Maneja el cierre del splash screen"""
        self.animation_timer.stop()
        super().closeEvent(event)
        logger.info("Splash screen cerrado")


def create_splash_screen():
    """Factory function para crear el splash screen"""
    return EVASplashScreen()