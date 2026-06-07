#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WIZARD DE PRIMERA EJECUCIÓN COMPLETO PARA EVA
Implementación según especificaciones WIZARD NUEVO COMPLETO.txt

Flujo: Idioma → Licencia → Bienvenida → Ollama → Usuario → CUDA → Modelos → Finalización

Características:
- Estilo cyberpunk consistente (negro/cyan)
- Integración con sistemas existentes
- Funcionalidad real (descarga modelos, validación licencias)
- Soporte bilingüe completo
"""

import logging
import subprocess
import webbrowser

from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QButtonGroup, QCheckBox, 
    QProgressBar, QGroupBox, QFrame, QSpacerItem, QSizePolicy,
    QMessageBox, QApplication, QWidget, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer

logger = logging.getLogger("EVA")

# ============================================================================
# ESTILO CYBERPUNK CONSISTENTE CON EVA
# ============================================================================

CYBERPUNK_STYLE = """
/* Estilo base del wizard */
QWizard {
    background-color: rgb(25, 25, 35);
    color: #ffffff;
    border: 2px solid #4db6ac;
    border-radius: 10px;
    font-family: 'Segoe UI', Arial, sans-serif;
}

QWizardPage {
    background-color: rgb(25, 25, 35);
    color: #ffffff;
    padding: 20px;
}

/* Títulos principales */
QLabel[class="title"] {
    color: #bb86fc;
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 10px;
    padding: 8px;
}

/* Subtítulos */
QLabel[class="subtitle"] {
    color: #4db6ac;
    font-size: 14px;
    margin-bottom: 12px;
    font-weight: 500;
}

/* Texto descriptivo */
QLabel[class="description"] {
    color: #ffffff;
    font-size: 12px;
    line-height: 1.4;
    margin-bottom: 10px;
}

/* Labels normales */
QLabel {
    color: #ffffff;
    background-color: transparent;
    font-size: 12px;
}

/* Inputs y campos de texto */
QLineEdit {
    background-color: rgb(30, 30, 40);
    border: 2px solid rgba(77, 182, 172, 0.3);
    border-radius: 8px;
    padding: 8px;
    color: #ffffff;
    font-size: 14px;
    min-height: 20px;
}

QLineEdit:focus {
    border: 2px solid #00bcd4;
    background-color: rgba(30, 30, 40, 0.9);
    box-shadow: 0 0 10px rgba(0, 188, 212, 0.3);
}

/* ComboBox */
QComboBox {
    background-color: rgb(30, 30, 40);
    border: 2px solid rgba(77, 182, 172, 0.3);
    border-radius: 8px;
    padding: 8px;
    color: #ffffff;
    min-height: 20px;
    font-size: 14px;
}

QComboBox:hover {
    border: 2px solid #00bcd4;
}

QComboBox::drop-down {
    border: none;
    background-color: transparent;
    width: 30px;
}

QComboBox::down-arrow {
    border: none;
    background-color: #00bcd4;
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: rgb(30, 30, 40);
    border: 2px solid rgba(77, 182, 172, 0.3);
    selection-background-color: rgba(0, 188, 212, 0.3);
    color: #ffffff;
    font-size: 14px;
}

/* Radio buttons */
QRadioButton {
    color: #ffffff;
    font-size: 14px;
    spacing: 10px;
    margin: 8px 0;
}

QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid rgba(77, 182, 172, 0.5);
    background-color: transparent;
}

QRadioButton::indicator:checked {
    background-color: #00bcd4;
    border: 2px solid #00bcd4;
}

QRadioButton::indicator:hover {
    border: 2px solid #00bcd4;
}

/* Checkboxes */
QCheckBox {
    color: #ffffff;
    font-size: 14px;
    spacing: 10px;
    margin: 8px 0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(77, 182, 172, 0.5);
    border-radius: 4px;
    background-color: transparent;
}

QCheckBox::indicator:checked {
    background-color: #00bcd4;
    border: 2px solid #00bcd4;
}

QCheckBox::indicator:hover {
    border: 2px solid #00bcd4;
}

/* Botones */
QPushButton {
    background-color: rgba(77, 182, 172, 0.2);
    border: 2px solid #4db6ac;
    border-radius: 8px;
    color: #ffffff;
    font-size: 14px;
    font-weight: 500;
    padding: 12px 24px;
    min-width: 120px;
}

QPushButton:hover {
    background-color: rgba(0, 188, 212, 0.3);
    border: 2px solid #00bcd4;
}

QPushButton:pressed {
    background-color: rgba(0, 188, 212, 0.5);
}

QPushButton:disabled {
    background-color: rgba(77, 182, 172, 0.1);
    border: 2px solid rgba(77, 182, 172, 0.2);
    color: rgba(255, 255, 255, 0.5);
}

/* Progress bar */
QProgressBar {
    background-color: rgb(30, 30, 40);
    border: 2px solid rgba(77, 182, 172, 0.3);
    border-radius: 8px;
    text-align: center;
    color: #ffffff;
    font-size: 12px;
    font-weight: bold;
    min-height: 25px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                               stop:0 #00bcd4, stop:1 #4db6ac);
    border-radius: 6px;
}

/* Group boxes */
QGroupBox {
    color: #bb86fc;
    font-size: 16px;
    font-weight: bold;
    border: 2px solid rgba(77, 182, 172, 0.3);
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 15px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 10px 0 10px;
}

/* Text areas */
QTextEdit {
    background-color: rgb(30, 30, 40);
    border: 2px solid rgba(77, 182, 172, 0.3);
    border-radius: 8px;
    color: #ffffff;
    font-size: 12px;
    padding: 10px;
}

/* Frames */
QFrame {
    background-color: transparent;
    border: none;
}

/* Scrollbars */
QScrollBar:vertical {
    background-color: rgb(30, 30, 40);
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #4db6ac;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #00bcd4;
}
"""

# ============================================================================
# CONFIGURACIÓN DE MODELOS Y LICENCIAS
# ============================================================================

# Modelos disponibles según licencia (según especificaciones)
MODELS_CONFIG = {
    "FREE": {
        "phi3:mini": {
            "name": "Phi-3 Mini",
            "size": "2.2 GB",
            "description_key": "phi3_description",
            "recommended": True
        }
    },
    "PREMIUM": {
        "phi3:mini": {
            "name": "Phi-3 Mini", 
            "size": "2.2 GB",
            "description_key": "phi3_description",
            "recommended": False
        },
        "qwen3:4b": {
            "name": "qwen3 4b",
            "size": "1.7 GB", 
            "description_key": "qwen3_description",
            "recommended": True
        },
        "mistral:7b": {
            "name": "Mistral 7B",
            "size": "4.1 GB",
            "description_key": "mistral_description",
            "recommended": False
        }
    }
}

# Textos multiidioma
TEXTS = {
    "es": {
        "wizard_title": "EVA - Configuración Inicial",
        "language_title": "Selección de Idioma",
        "language_subtitle": "Elige tu idioma preferido para EVA",
        "language_description": "EVA soporta completamente español e inglés. Puedes cambiar el idioma en cualquier momento desde la configuración.",
        "license_title": "Activación de Licencia",
        "license_subtitle": "Configura tu tipo de licencia",
        "license_free": "Licencia FREE",
        "license_premium": "Licencia PREMIUM",
        "license_free_radio": "Usar licencia gratuita",
        "license_premium_radio": "Activar licencia premium",
        "about_ollama": "ℹ️ Acerca de Ollama",
        "available_models": "🤖 Modelos Disponibles",
        "download_progress": "📥 Progreso de Descarga",
        "results": "📊 Resultados",
        "license_key_placeholder": "Ingresa tu clave de licencia premium...",
        "checking_ollama_status": "🔍 Verificando Ollama...",
        "ollama_found": "Ollama encontrado: {version}",
        "ollama_timeout": "Timeout verificando Ollama",
        "ollama_error": "Error verificando Ollama: {error}",
        "downloading_model": "Downloading: {model_name}",
        "download_error_model": "❌ Error downloading {model_name}: {error}",
        "license_free_desc": "• Modelo Phi-3 Mini incluido\n• Funcionalidad completa básica\n• Soporte comunitario",
        "license_premium_desc": "• Todos los modelos disponibles\n• Funciones avanzadas\n• Soporte prioritario\n• Actualizaciones tempranas",
        "welcome_title": "¡Bienvenido a EVA!",
        "welcome_subtitle": "Tu Asistente Virtual Mejorado",
        "ollama_title": "Verificación de Ollama",
        "ollama_subtitle": "EVA requiere Ollama para funcionar correctamente",
        "user_title": "Información del Usuario",
        "user_subtitle": "Personaliza tu experiencia con EVA",
        "cuda_title": "Detección de Hardware",
        "cuda_subtitle": "Optimizando EVA para tu sistema",
        "models_title": "Descarga de Modelos",
        "models_subtitle": "Configurando modelos de IA",
        "completion_title": "¡Configuración Completada!",
        "completion_subtitle": "EVA está listo para usar",
        "next": "Siguiente",
        "back": "Atrás", 
        "finish": "Finalizar",
        "cancel": "Cancelar",
        "detecting_hardware": "🔍 Detectando hardware...",
        "checking_ollama": "🔍 Verificando Ollama...",
        "downloading": "Descargando:",
        "download_completed": "✅ Descarga completada",
        "download_error": "❌ Error en descarga",
        "no_models_selected": "Sin modelos seleccionados",
        "select_model_warning": "Por favor selecciona al menos un modelo para descargar.",
        "ollama_required": "Ollama requerido",
        "ollama_required_msg": "Ollama debe estar instalado para descargar modelos.",
        "name_required": "Nombre requerido",
        "name_required_msg": "Por favor ingresa un nombre de al menos 2 caracteres.",
        "license_required": "Licencia requerida",
        "license_required_msg": "Por favor ingresa una clave de licencia premium válida.",
        "download_models_btn": "📥 Descargar Modelos Seleccionados",
        "download_ollama_btn": "📥 Descargar Ollama",
        "check_again_btn": "🔄 Verificar de nuevo",
        "get_license_btn": "🛒 Obtener Licencia Premium",
        "spanish_option": "🇪🇸 Español",
        "english_option": "🇺🇸 Inglés",
        "main_features": "🚀 Características Principales",
        "personal_information": "👤 Información Personal",
        "how_to_call_you": "¿Cómo te gustaría que EVA te llame?",
        "name_placeholder": "Ingresa tu nombre...",
        "personalization_info": "EVA utilizará tu nombre para personalizar las conversaciones y crear una experiencia más natural. Puedes cambiarlo en cualquier momento desde la configuración.",
        "hardware_acceleration": "🚀 Aceleración por Hardware",
        "cuda_available": "✅ CUDA disponible - Aceleración habilitada",
        "cuda_not_available": "ℹ️ CUDA no disponible - Usando modo CPU",
        "gpu_recommendation": "🎯 Recomendación: EVA utilizará aceleración GPU para mejor rendimiento",
        "cpu_recommendation": "✅ EVA funcionará perfectamente usando CPU",
        "cpu_mode": "🖥️ Modo: Solo CPU",
        "reason_label": "📝 Razón:",
        "gpu_not_detected": "GPU NVIDIA no detectada",
        "configuration_summary": "📋 Resumen de Configuración",
        "next_steps": "🚀 Próximos Pasos",
        "congratulations_premium": "¡Felicidades {name}! Has configurado EVA exitosamente. Tu asistente virtual está listo para ayudarte con tareas diarias, conversaciones y mucho más. ¡Disfruta de tu nueva experiencia con IA!",
        "congratulations_free": "¡Felicidades {name}! Has configurado EVA exitosamente. Tu asistente virtual está listo para ayudarte con tareas diarias, conversaciones y mucho más. ¡Disfruta de tu nueva experiencia con IA!",
        "language_config": "🌍 Idioma: Español",
        "license_config": "🔑 Licencia: {license_type}",
        "user_config": "👤 Usuario: {user_name}",
        "cuda_config": "⚡ CUDA: {cuda_status}",
        "models_config": "🤖 Modelos: {models_count} descargados",
        "start_conversation": "💬 Inicia una conversación escribiendo en el chat",
        "explore_settings": "⚙️ Explora la configuración para personalizar EVA",
        "adjust_voice": "🔊 Ajusta la configuración de voz según tus preferencias",
        "voice_synthesis": "🎵 Síntesis de voz de alta calidad (Piper TTS)",
        "voice_recognition": "🎤 Reconocimiento de voz avanzado",
        "bilingual_support": "🌍 Soporte bilingüe (Español/Inglés)",
        "file_processing": "📄 Procesamiento inteligente de documentos",
        "ai_conversations": "🤖 Conversaciones naturales con IA usando Ollama",
        "system_control": "🖥️ Control completo del sistema",
        "ollama_info": "Ollama es el motor de IA de EVA que permite:\n\n• ⚡ Respuestas rápidas sin conexión a internet\n• 🔒 Privacidad completa - todo funciona localmente\n• 🧠 Comprensión avanzada del lenguaje natural\n• 💾 Uso eficiente de memoria",
        "ollama_not_installed": "Ollama no está instalado",
        "ollama_available": "✅ Ollama está disponible y listo",
        "download_info": "Los modelos se descargarán usando Ollama. Asegúrate de tener suficiente espacio en disco. Puedes descargar modelos adicionales más tarde desde la configuración.",
        "language_selector": "Idioma / Language",
        "premium_ai_models": "⭐ Modelos de IA premium (qwen3, Mistral)",
        "advanced_features": "⭐ Funciones avanzadas exclusivas",
        "priority_support": "⭐ Soporte prioritario",
        "privacy_feature": "• 🔒 Privacidad total - Tus conversaciones nunca salen de tu PC",
        "fast_responses": "• ⚡ Respuestas rápidas sin conexión a internet",
        "ollama_description": "Ollama es el motor de IA que permite a EVA ejecutar modelos de lenguaje localmente en tu computadora. Esto garantiza:",
        "optimized_models": "• 🎯 Modelos optimizados para tu hardware",
        "data_control": "• 💾 Control completo sobre tus datos",
        "eva_requires_ollama": "EVA requiere Ollama para funcionar correctamente.",
        "phi3_description": "Modelo compacto y eficiente para uso general",
        "qwen3_description": "Modelo avanzado de Google, rápido y preciso",
        "mistral_description": "Modelo premium de alta calidad para tareas complejas",
        "recommended_model": "⭐ Recomendado",
        "cuda_info_compact": "EVA puede usar aceleración NVIDIA CUDA para mejor rendimiento:\n\n🚀 Beneficios:\n• ⚡ Respuestas hasta 10x más rápidas\n• 🎯 Mejor rendimiento en modelos grandes\n• 💾 Uso eficiente de memoria GPU\n\n📝 EVA funciona perfectamente sin CUDA.",
        "models_downloaded": "Modelos descargados",
        "welcome_premium_message": "¡Gracias por elegir EVA Premium! Estás a punto de configurar el asistente virtual más avanzado con acceso completo a todos los modelos de IA y características premium. Te guiaremos paso a paso para optimizar EVA según tu sistema.",
        "welcome_free_message": "¡Bienvenido a EVA! Estás a punto de configurar tu asistente virtual inteligente. EVA te ayudará con tareas diarias, control por voz, y conversaciones naturales. Te guiaremos paso a paso para configurar todo correctamente."
    },
    "en": {
        "wizard_title": "EVA - Initial Setup",
        "language_title": "Language Selection",
        "language_subtitle": "Choose your preferred language for EVA",
        "language_description": "EVA fully supports Spanish and English. You can change the language anytime from settings.",
        "license_title": "License Activation",
        "license_subtitle": "Configure your license type",
        "license_free": "FREE License",
        "license_premium": "PREMIUM License", 
        "license_free_radio": "Use free license",
        "license_premium_radio": "Activate premium license",
        "about_ollama": "ℹ️ About Ollama",
        "available_models": "🤖 Available Models",
        "download_progress": "📥 Download Progress",
        "results": "📊 Results",
        "license_key_placeholder": "Enter your premium license key...",
        "checking_ollama_status": "🔍 Checking Ollama...",
        "ollama_found": "Ollama found: {version}",
        "ollama_timeout": "Timeout checking Ollama",
        "ollama_error": "Error checking Ollama: {error}",
        "downloading_model": "Downloading: {model_name}",
        "download_error_model": "❌ Error downloading {model_name}: {error}", 
        "license_free_desc": "• Phi-3 Mini model included\n• Complete basic functionality\n• Community support",
        "license_premium_desc": "• All models available\n• Advanced features\n• Priority support\n• Early updates",
        "welcome_title": "Welcome to EVA!",
        "welcome_subtitle": "Your Enhanced Virtual Assistant",
        "ollama_title": "Ollama Verification",
        "ollama_subtitle": "EVA requires Ollama to function properly",
        "user_title": "User Information",
        "user_subtitle": "Personalize your EVA experience",
        "cuda_title": "Hardware Detection",
        "cuda_subtitle": "Optimizing EVA for your system",
        "models_title": "Model Download",
        "models_subtitle": "Setting up AI models",
        "completion_title": "Setup Complete!",
        "completion_subtitle": "EVA is ready to use",
        "next": "Next",
        "back": "Back",
        "finish": "Finish", 
        "cancel": "Cancel",
        "detecting_hardware": "🔍 Detecting hardware...",
        "checking_ollama": "🔍 Checking Ollama...",
        "downloading": "Downloading:",
        "download_completed": "✅ Download completed",
        "download_error": "❌ Download error",
        "no_models_selected": "No models selected",
        "select_model_warning": "Please select at least one model to download.",
        "ollama_required": "Ollama required",
        "ollama_required_msg": "Ollama must be installed to download models.",
        "name_required": "Name required",
        "name_required_msg": "Please enter a name with at least 2 characters.",
        "license_required": "License required",
        "license_required_msg": "Please enter a valid premium license key.",
        "download_models_btn": "📥 Download Selected Models",
        "download_ollama_btn": "📥 Download Ollama",
        "check_again_btn": "🔄 Check Again",
        "get_license_btn": "🛒 Get Premium License",
        "spanish_option": "🇪🇸 Spanish",
        "english_option": "🇺🇸 English",
        "main_features": "🚀 Main Features",
        "personal_information": "👤 Personal Information",
        "how_to_call_you": "What would you like EVA to call you?",
        "name_placeholder": "Enter your name...",
        "personalization_info": "EVA will use your name to personalize conversations and create a more natural experience. You can change it anytime from settings.",
        "hardware_acceleration": "🚀 Hardware Acceleration",
        "cuda_available": "✅ CUDA available - Acceleration enabled",
        "cuda_not_available": "ℹ️ CUDA not available - Using CPU mode",
        "gpu_recommendation": "🎯 Recommendation: EVA will use GPU acceleration for better performance",
        "cpu_recommendation": "✅ EVA will work perfectly using CPU",
        "cpu_mode": "🖥️ Mode: CPU Only",
        "reason_label": "📝 Reason:",
        "gpu_not_detected": "NVIDIA GPU not detected",
        "configuration_summary": "📋 Configuration Summary",
        "next_steps": "🚀 Next Steps",
        "congratulations_premium": "Congratulations {name}! You have successfully configured EVA. Your virtual assistant is ready to help you with daily tasks, conversations, and much more. Enjoy your new AI experience!",
        "congratulations_free": "Congratulations {name}! You have successfully configured EVA. Your virtual assistant is ready to help you with daily tasks, conversations, and much more. Enjoy your new AI experience!",
        "language_config": "🌍 Language: English",
        "license_config": "🔑 License: {license_type}",
        "user_config": "👤 User: {user_name}",
        "cuda_config": "⚡ CUDA: {cuda_status}",
        "models_config": "🤖 Models: {models_count} downloaded",
        "start_conversation": "💬 Start a conversation by typing in the chat",
        "explore_settings": "⚙️ Explore settings to customize EVA",
        "adjust_voice": "🔊 Adjust voice settings according to your preferences",
        "voice_synthesis": "🎵 High-quality voice synthesis (Piper TTS)",
        "voice_recognition": "🎤 Advanced voice recognition",
        "bilingual_support": "🌍 Bilingual support (Spanish/English)",
        "file_processing": "📄 Intelligent document processing",
        "ai_conversations": "🤖 Natural AI conversations with Ollama",
        "system_control": "🖥️ Complete system control",
        "ollama_info": "Ollama is EVA's AI engine that enables:\n\n• ⚡ Fast responses without internet connection\n• 🔒 Complete privacy - everything runs locally\n• 🧠 Advanced natural language understanding\n• 💾 Efficient memory usage",
        "ollama_not_installed": "Ollama is not installed",
        "ollama_available": "✅ Ollama is available and ready",
        "download_info": "Models will be downloaded using Ollama. Make sure you have enough disk space. You can download additional models later from settings."
    }
}

# ============================================================================
# CLASE PRINCIPAL DEL WIZARD
# ============================================================================

class NewFirstRunWizard(QWizard):
    """
    Wizard de primera ejecución completo para EVA
    Implementa el flujo especificado en WIZARD NUEVO COMPLETO.txt
    """
    
    def __init__(self, language_manager, parent=None):
        super().__init__(parent)
        
        self.language_manager = language_manager
        self.current_language = language_manager.current_lang if language_manager else "es"
        
        # Configuración del wizard
        self.wizard_config = {
            "language": self.current_language,
            "license_type": "FREE",
            "license_key": "",
            "user_name": "",
            "ollama_ready": False,
            "cuda_available": False,
            "selected_models": [],
            "wizard_completed": False
        }
        
        self.setup_wizard()
        self.setup_pages()
        
        logger.info("🧙‍♂️ Nuevo wizard de primera ejecución inicializado")
    
    def setup_wizard(self):
        """Configuración inicial del wizard"""
        # Aplicar estilo cyberpunk
        self.setStyleSheet(CYBERPUNK_STYLE)
        
        # Configuración de ventana
        self.setWindowTitle(self.get_text("wizard_title"))
        self.setWizardStyle(QWizard.ModernStyle)
        # Deshabilitar botón de ayuda si está disponible
        try:
            self.setOption(QWizard.HaveHelpButton, False)
        except AttributeError:
            # En algunas versiones de PyQt, HaveHelpButton no existe
            pass
        # Deshabilitar botones personalizados si están disponibles
        try:
            self.setOption(QWizard.HaveCustomButton1, False)
        except AttributeError:
            pass
        
        # Tamaño y posición - Optimizado para compatibilidad con 768p
        self.setMinimumSize(750, 480)
        self.resize(800, 520)
        
        # Centrar en pantalla
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        # Configurar botones
        self.setButtonText(QWizard.NextButton, self.get_text("next"))
        self.setButtonText(QWizard.BackButton, self.get_text("back"))
        self.setButtonText(QWizard.FinishButton, self.get_text("finish"))
        self.setButtonText(QWizard.CancelButton, self.get_text("cancel"))
    
    def setup_pages(self):
        """Configurar todas las páginas del wizard"""
        # Páginas según flujo especificado
        self.addPage(LanguageSelectionPage(self))      # 1. Idioma
        self.addPage(LicenseActivationPage(self))      # 2. Licencia  
        self.addPage(WelcomePage(self))                # 3. Bienvenida
        self.addPage(OllamaCheckPage(self))            # 4. Ollama
        self.addPage(UserInfoPage(self))               # 5. Usuario
        self.addPage(CudaDetectionPage(self))          # 6. CUDA
        self.addPage(ModelDownloadPage(self))          # 7. Modelos
        self.addPage(CompletionPage(self))             # 8. Finalización
        
        logger.info("✅ Páginas del wizard configuradas correctamente")
    
    def get_text(self, key):
        """Obtener texto en el idioma actual"""
        return TEXTS.get(self.current_language, TEXTS["es"]).get(key, key)
    
    def update_language(self, language):
        """Actualizar idioma del wizard"""
        self.current_language = language
        self.wizard_config["language"] = language
        
        # Actualizar título de ventana
        self.setWindowTitle(self.get_text("wizard_title"))
        
        # Actualizar botones
        self.setButtonText(QWizard.NextButton, self.get_text("next"))
        self.setButtonText(QWizard.BackButton, self.get_text("back"))
        self.setButtonText(QWizard.FinishButton, self.get_text("finish"))
        self.setButtonText(QWizard.CancelButton, self.get_text("cancel"))
        
        # Actualizar todas las páginas existentes
        self.update_all_pages()
        
        logger.info(f"🌍 Idioma del wizard actualizado a: {language}")
    
    def update_all_pages(self):
        """Actualizar textos de todas las páginas cuando cambia el idioma"""
        try:
            for page_id in self.pageIds():
                page = self.page(page_id)
                if hasattr(page, 'update_texts'):
                    page.update_texts()
        except Exception as e:
            logger.warning(f"Error actualizando páginas: {str(e)}")
    
    def get_config(self):
        """Obtener configuración final del wizard"""
        return self.wizard_config.copy()

# ============================================================================
# PÁGINA 1: SELECCIÓN DE IDIOMA
# ============================================================================

class LanguageSelectionPage(QWizardPage):
    """Primera página: Selección de idioma"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Título
        title = QLabel(self.wizard.get_text("language_title"))
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel(self.wizard.get_text("language_subtitle"))
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Descripción
        description = QLabel(self.wizard.get_text("language_description"))
        description.setProperty("class", "description")
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
        
        # Espaciador reducido para optimizar espacio
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Selector de idioma
        lang_group = QGroupBox(self.wizard.get_text("language_selector"))
        lang_layout = QVBoxLayout()
        
        self.lang_button_group = QButtonGroup()
        
        # Opción Español
        self.spanish_radio = QRadioButton(TEXTS[self.wizard.current_language]["spanish_option"])
        self.spanish_radio.setChecked(self.wizard.current_language == "es")
        self.lang_button_group.addButton(self.spanish_radio, 0)
        lang_layout.addWidget(self.spanish_radio)
        
        # Opción Inglés
        self.english_radio = QRadioButton(TEXTS[self.wizard.current_language]["english_option"])
        self.english_radio.setChecked(self.wizard.current_language == "en")
        self.lang_button_group.addButton(self.english_radio, 1)
        lang_layout.addWidget(self.english_radio)
        
        lang_group.setLayout(lang_layout)
        layout.addWidget(lang_group)
        
        # Espaciador final
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.setLayout(layout)
        
        # Conectar señales
        self.lang_button_group.buttonClicked.connect(self.on_language_changed)
    
    def on_language_changed(self, button):
        """Handle language change"""
        if button == self.spanish_radio:
            new_language = "es"
        else:
            new_language = "en"
        
        if new_language != self.wizard.current_language:
            self.wizard.update_language(new_language)
            # Actualizar textos de esta página
            self.update_texts()
    
    def update_texts(self):
        """Actualizar textos de la página cuando cambia el idioma"""
        try:
            # Actualizar título
            title_labels = self.findChildren(QLabel)
            for label in title_labels:
                if label.property("class") == "title":
                    label.setText(self.wizard.get_text("language_title"))
                elif label.property("class") == "subtitle":
                    label.setText(self.wizard.get_text("language_subtitle"))
                elif label.property("class") == "description":
                    label.setText(self.wizard.get_text("language_description"))
            
            # Actualizar radio buttons
            self.spanish_radio.setText(self.wizard.get_text("spanish_option"))
            self.english_radio.setText(self.wizard.get_text("english_option"))
            
            # Actualizar grupo de idioma
            lang_groups = self.findChildren(QGroupBox)
            for group in lang_groups:
                if "language" in group.objectName().lower() or group.title() in ["Idioma / Language", "Language / Idioma"]:
                    group.setTitle(self.wizard.get_text("language_selector"))
        except Exception as e:
            logger.warning(f"Error actualizando textos de LanguageSelectionPage: {str(e)}")
    
    def validatePage(self):
        """Validar página antes de continuar"""
        selected_lang = "es" if self.spanish_radio.isChecked() else "en"
        self.wizard.wizard_config["language"] = selected_lang
        logger.info(f"✅ Idioma seleccionado: {selected_lang}")
        return True

# ============================================================================
# PÁGINA 2: ACTIVACIÓN DE LICENCIA  
# ============================================================================

class LicenseActivationPage(QWizardPage):
    """Segunda página: Activación de licencia"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Título
        title = QLabel(self.wizard.get_text("license_title"))
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel(self.wizard.get_text("license_subtitle"))
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Espaciador
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Opciones de licencia
        license_layout = QHBoxLayout()
        
        # Licencia FREE
        free_group = QGroupBox(self.wizard.get_text("license_free"))
        free_layout = QVBoxLayout()
        
        self.free_radio = QRadioButton(self.wizard.get_text("license_free_radio"))
        self.free_radio.setChecked(True)
        free_layout.addWidget(self.free_radio)
        
        free_desc = QLabel(self.wizard.get_text("license_free_desc"))
        free_desc.setProperty("class", "description")
        free_desc.setWordWrap(True)
        free_layout.addWidget(free_desc)
        
        free_group.setLayout(free_layout)
        license_layout.addWidget(free_group)
        
        # Licencia PREMIUM
        premium_group = QGroupBox(self.wizard.get_text("license_premium"))
        premium_layout = QVBoxLayout()
        
        self.premium_radio = QRadioButton(self.wizard.get_text("license_premium_radio"))
        premium_layout.addWidget(self.premium_radio)
        
        premium_desc = QLabel(self.wizard.get_text("license_premium_desc"))
        premium_desc.setProperty("class", "description")
        premium_desc.setWordWrap(True)
        premium_layout.addWidget(premium_desc)
        
        # Campo para clave de licencia
        self.license_key_input = QLineEdit()
        self.license_key_input.setPlaceholderText(self.wizard.get_text("license_key_placeholder"))
        self.license_key_input.setEnabled(False)
        premium_layout.addWidget(self.license_key_input)
        
        # Botón para obtener licencia
        self.get_license_btn = QPushButton(self.wizard.get_text("get_license_btn"))
        self.get_license_btn.clicked.connect(self.open_license_page)
        premium_layout.addWidget(self.get_license_btn)
        
        premium_group.setLayout(premium_layout)
        license_layout.addWidget(premium_group)
        
        layout.addLayout(license_layout)
        
        # Espaciador final
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.setLayout(layout)
        
        # Conectar señales
        self.free_radio.toggled.connect(self.on_license_type_changed)
        self.premium_radio.toggled.connect(self.on_license_type_changed)
        self.license_key_input.textChanged.connect(self.validate_license_key)
    
    def on_license_type_changed(self):
        """Manejar cambio de tipo de licencia"""
        if self.premium_radio.isChecked():
            self.license_key_input.setEnabled(True)
            self.license_key_input.setFocus()
        else:
            self.license_key_input.setEnabled(False)
            self.license_key_input.clear()
    
    def validate_license_key(self, text):
        """Validar clave de licencia en tiempo real"""
        # TODO: Integrar con LicenseValidator existente
        if len(text) >= 10:  # Validación básica por ahora
            self.license_key_input.setStyleSheet("border: 2px solid #4CAF50;")
        else:
            self.license_key_input.setStyleSheet("")
    
    def open_license_page(self):
        """Abrir página para obtener licencia"""
        webbrowser.open("https://gumroad.com/eva-premium")  # URL de ejemplo
    
    def validatePage(self):
        """Validar página antes de continuar"""
        if self.premium_radio.isChecked():
            license_key = self.license_key_input.text().strip()
            if not license_key:
                QMessageBox.warning(self, "Licencia requerida", 
                                  "Por favor ingresa una clave de licencia premium válida.")
                return False
            
            # TODO: Validar con LicenseValidator real
            self.wizard.wizard_config["license_type"] = "PREMIUM"
            self.wizard.wizard_config["license_key"] = license_key
            logger.info("✅ Licencia PREMIUM configurada")
        else:
            self.wizard.wizard_config["license_type"] = "FREE"
            self.wizard.wizard_config["license_key"] = ""
            logger.info("✅ Licencia FREE seleccionada")
        
        return True
    
    def update_texts(self):
        """Actualizar textos de la página cuando cambia el idioma"""
        try:
            # Actualizar labels principales
            title_labels = self.findChildren(QLabel)
            for label in title_labels:
                if label.property("class") == "title":
                    label.setText(self.wizard.get_text("license_title"))
                elif label.property("class") == "subtitle":
                    label.setText(self.wizard.get_text("license_subtitle"))
            
            # Actualizar group boxes Y sus descripciones
            group_boxes = self.findChildren(QGroupBox)
            for group in group_boxes:
                if "FREE" in group.title() or "PREMIUM" in group.title() or "Licencia" in group.title():
                    if "FREE" in group.title() or "gratuita" in group.title():
                        group.setTitle(self.wizard.get_text("license_free"))
                        # Actualizar descripción FREE
                        desc_labels = group.findChildren(QLabel)
                        for desc_label in desc_labels:
                            if desc_label.property("class") == "description":
                                desc_label.setText(self.wizard.get_text("license_free_desc"))
                    else:
                        group.setTitle(self.wizard.get_text("license_premium"))
                        # Actualizar descripción PREMIUM
                        desc_labels = group.findChildren(QLabel)
                        for desc_label in desc_labels:
                            if desc_label.property("class") == "description":
                                desc_label.setText(self.wizard.get_text("license_premium_desc"))
            
            # Actualizar radio buttons
            if hasattr(self, 'free_radio'):
                self.free_radio.setText(self.wizard.get_text("license_free_radio"))
            if hasattr(self, 'premium_radio'):
                self.premium_radio.setText(self.wizard.get_text("license_premium_radio"))
            
            # Actualizar placeholder del input
            if hasattr(self, 'license_key_input'):
                self.license_key_input.setPlaceholderText(self.wizard.get_text("license_key_placeholder"))
            
            # Actualizar botón
            if hasattr(self, 'get_license_btn'):
                self.get_license_btn.setText(self.wizard.get_text("get_license_btn"))
                
        except Exception as e:
            logger.warning(f"Error actualizando textos de LicenseActivationPage: {str(e)}")

# ============================================================================
# PÁGINA 3: BIENVENIDA PERSONALIZADA
# ============================================================================

class WelcomePage(QWizardPage):
    """Tercera página: Bienvenida personalizada según idioma"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Título principal
        title = QLabel(self.wizard.get_text("welcome_title"))
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel(self.wizard.get_text("welcome_subtitle"))
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Espaciador
        layout.addItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Mensaje de bienvenida personalizado
        welcome_text = self.get_welcome_message()
        welcome_label = QLabel(welcome_text)
        welcome_label.setProperty("class", "description")
        welcome_label.setWordWrap(True)
        welcome_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(welcome_label)
        
        # Espaciador
        layout.addItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Características principales
        features_group = QGroupBox(TEXTS[self.wizard.current_language]["main_features"])
        features_layout = QVBoxLayout()
        
        features = self.get_features_list()
        for feature in features:
            feature_label = QLabel(f"• {feature}")
            feature_label.setProperty("class", "description")
            features_layout.addWidget(feature_label)
        
        features_group.setLayout(features_layout)
        layout.addWidget(features_group)
        
        # Espaciador final
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.setLayout(layout)
    
    def get_welcome_message(self):
        """Obtener mensaje de bienvenida personalizado"""
        license_type = self.wizard.wizard_config.get("license_type", "FREE")
        
        if license_type == "PREMIUM":
            return self.wizard.get_text("welcome_premium_message")
        else:
            return self.wizard.get_text("welcome_free_message")
    
    def get_features_list(self):
        """Obtener lista de características según idioma y licencia"""
        license_type = self.wizard.wizard_config.get("license_type", "FREE")
        
        if self.wizard.current_language == "es":
            base_features = [
                self.wizard.get_text("voice_recognition"),
                self.wizard.get_text("voice_synthesis"),
                self.wizard.get_text("ai_conversations"),
                self.wizard.get_text("bilingual_support"),
                self.wizard.get_text("file_processing"),
                self.wizard.get_text("system_control")
            ]
            
            if license_type == "PREMIUM":
                base_features.extend([
                    self.wizard.get_text("premium_ai_models"),
                    self.wizard.get_text("advanced_features"),
                    self.wizard.get_text("priority_support")
                ])
            
            return base_features
        else:
            base_features = [
                self.wizard.get_text("voice_recognition"),
                self.wizard.get_text("voice_synthesis"),
                self.wizard.get_text("ai_conversations"),
                self.wizard.get_text("bilingual_support"),
                self.wizard.get_text("file_processing"),
                self.wizard.get_text("system_control")
            ]
            
            if license_type == "PREMIUM":
                base_features.extend([
                    self.wizard.get_text("premium_ai_models"),
                    self.wizard.get_text("advanced_features"),
                    self.wizard.get_text("priority_support")
                ])
            
            return base_features
    
    def update_texts(self):
        """Actualizar textos de la página cuando cambia el idioma"""
        try:
            # Actualizar títulos
            title_labels = self.findChildren(QLabel)
            for label in title_labels:
                if label.property("class") == "title":
                    label.setText(self.wizard.get_text("welcome_title"))
                elif label.property("class") == "subtitle":
                    label.setText(self.wizard.get_text("welcome_subtitle"))
                elif label.property("class") == "description":
                    # Actualizar mensaje de bienvenida
                    welcome_text = self.get_welcome_message()
                    label.setText(welcome_text)
            
            # Actualizar group box de características
            group_boxes = self.findChildren(QGroupBox)
            for group in group_boxes:
                if "Características" in group.title() or "Features" in group.title():
                    group.setTitle(self.wizard.get_text("main_features"))
                    
                    # Actualizar lista de características
                    features = self.get_features_list()
                    feature_labels = group.findChildren(QLabel)
                    for i, feature_label in enumerate(feature_labels):
                        if i < len(features) and feature_label.property("class") == "description":
                            feature_label.setText(f"• {features[i]}")
                            
        except Exception as e:
            logger.warning(f"Error actualizando textos de WelcomePage: {str(e)}")

# ============================================================================
# PÁGINA 4: VERIFICACIÓN DE OLLAMA
# ============================================================================

class OllamaCheckPage(QWizardPage):
    """Cuarta página: Verificación de Ollama"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.ollama_status = "checking"  # checking, found, not_found, error
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Título
        title = QLabel(self.wizard.get_text("ollama_title"))
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel(self.wizard.get_text("ollama_subtitle"))
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Estado de verificación
        self.status_label = QLabel(self.wizard.get_text("checking_ollama_status"))
        self.status_label.setProperty("class", "description")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminado
        layout.addWidget(self.progress_bar)
        
        # Espaciador
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Información sobre Ollama
        info_group = QGroupBox(self.wizard.get_text("about_ollama"))
        info_layout = QVBoxLayout()
        
        ollama_info = self.get_ollama_info()
        info_label = QLabel(ollama_info)
        info_label.setProperty("class", "description")
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Guardar referencias para actualización de idioma
        self.title_label = title
        self.subtitle_label = subtitle
        self.info_group = info_group
        self.info_label = info_label
        
        # Botones de acción (inicialmente ocultos)
        self.action_frame = QFrame()
        action_layout = QHBoxLayout()
        
        self.install_button = QPushButton(self.wizard.get_text("download_ollama_btn"))
        self.install_button.clicked.connect(self.open_ollama_download)
        self.install_button.setVisible(False)
        action_layout.addWidget(self.install_button)
        
        self.retry_button = QPushButton(self.wizard.get_text("check_again_btn"))
        self.retry_button.clicked.connect(self.check_ollama)
        self.retry_button.setVisible(False)
        action_layout.addWidget(self.retry_button)
        
        self.action_frame.setLayout(action_layout)
        layout.addWidget(self.action_frame)
        
        # Espaciador final
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.setLayout(layout)
        
        # Iniciar verificación automática
        QTimer.singleShot(1000, self.check_ollama)
    
    def get_ollama_info(self):
        """Obtener información sobre Ollama"""
        if self.wizard.current_language == "es":
            return (self.wizard.get_text("ollama_description") + "\n\n" +
                   self.wizard.get_text("privacy_feature") + "\n" +
                   self.wizard.get_text("fast_responses") + "\n" +
                   self.wizard.get_text("optimized_models") + "\n" +
                   self.wizard.get_text("data_control") + "\n\n" +
                   self.wizard.get_text("eva_requires_ollama"))
        else:
            return (self.wizard.get_text("ollama_description") + "\n\n" +
                   self.wizard.get_text("privacy_feature") + "\n" +
                   self.wizard.get_text("fast_responses") + "\n" +
                   self.wizard.get_text("optimized_models") + "\n" +
                   self.wizard.get_text("data_control") + "\n\n" +
                   self.wizard.get_text("eva_requires_ollama"))
    
    def check_ollama(self):
        """Verificar si Ollama está instalado y funcionando"""
        self.status_label.setText(self.wizard.get_text("checking_ollama_status"))
        self.progress_bar.setRange(0, 0)
        self.install_button.setVisible(False)
        self.retry_button.setVisible(False)
        
        # Ejecutar verificación en hilo separado
        self.check_thread = OllamaCheckThread(self.wizard)
        self.check_thread.status_updated.connect(self.on_ollama_status_updated)
        self.check_thread.start()
    
    def on_ollama_status_updated(self, status, message):
        """Manejar actualización del estado de Ollama"""
        self.ollama_status = status
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        
        if status == "found":
            self.status_label.setText(f"✅ {message}")
            self.wizard.wizard_config["ollama_ready"] = True
        elif status == "not_found":
            self.status_label.setText(f"❌ {message}")
            self.install_button.setVisible(True)
            self.retry_button.setVisible(True)
            self.wizard.wizard_config["ollama_ready"] = False
        else:  # error
            self.status_label.setText(f"⚠️ {message}")
            self.retry_button.setVisible(True)
            self.wizard.wizard_config["ollama_ready"] = False
    
    def open_ollama_download(self):
        """Abrir página de descarga de Ollama"""
        webbrowser.open("https://ollama.ai/download")
    
    def isComplete(self):
        """Verificar si la página está completa"""
        return self.wizard.wizard_config.get("ollama_ready", False)
    
    def update_texts(self):
        """Actualizar textos de la página cuando cambia el idioma"""
        try:
            title_labels = self.findChildren(QLabel)
            for label in title_labels:
                if label.property("class") == "title":
                    label.setText(self.wizard.get_text("ollama_title"))
                elif label.property("class") == "subtitle":
                    label.setText(self.wizard.get_text("ollama_subtitle"))
            
            # Actualizar el contenido de información de Ollama
            if hasattr(self, 'info_group'):
                self.info_group.setTitle(self.wizard.get_text("about_ollama"))
            if hasattr(self, 'info_label'):
                self.info_label.setText(self.get_ollama_info())
            
            group_boxes = self.findChildren(QGroupBox)
            for group in group_boxes:
                if "Ollama" in group.title():
                    group.setTitle(self.wizard.get_text("about_ollama"))
            
            # Actualizar botones
            if hasattr(self, 'install_button'):
                self.install_button.setText(self.wizard.get_text("download_ollama_btn"))
            if hasattr(self, 'retry_button'):
                self.retry_button.setText(self.wizard.get_text("check_again_btn"))
                
        except Exception as e:
            logger.warning(f"Error actualizando textos de OllamaCheckPage: {str(e)}")

class OllamaCheckThread(QThread):
    """Hilo para verificar Ollama sin bloquear la UI"""
    status_updated = Signal(str, str)  # status, message
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
    
    def run(self):
        """Ejecutar verificación de Ollama"""
        try:
            # Intentar ejecutar ollama --version
            result = subprocess.run(["ollama", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version = result.stdout.strip()
                message = self.wizard.get_text("ollama_found").format(version=version)
                self.status_updated.emit("found", message)
            else:
                self.status_updated.emit("not_found", self.wizard.get_text("ollama_not_installed"))
                
        except subprocess.TimeoutExpired:
            self.status_updated.emit("error", self.wizard.get_text("ollama_timeout"))
        except FileNotFoundError:
            self.status_updated.emit("not_found", self.wizard.get_text("ollama_not_installed"))
        except Exception as e:
            message = self.wizard.get_text("ollama_error").format(error=str(e))
            self.status_updated.emit("error", message)

# ============================================================================
# PÁGINA 5: INFORMACIÓN DEL USUARIO
# ============================================================================

class UserInfoPage(QWizardPage):
    """Quinta página: Información del usuario"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Título
        title = QLabel(TEXTS[self.wizard.current_language]["user_title"])
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel(TEXTS[self.wizard.current_language]["user_subtitle"])
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Espaciador
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Formulario de usuario
        form_group = QGroupBox(TEXTS[self.wizard.current_language]["personal_information"])
        form_layout = QVBoxLayout()
        
        # Nombre del usuario
        name_label = QLabel(TEXTS[self.wizard.current_language]["how_to_call_you"])
        name_label.setProperty("class", "description")
        form_layout.addWidget(name_label)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(TEXTS[self.wizard.current_language]["name_placeholder"])
        self.name_input.textChanged.connect(self.on_name_changed)
        form_layout.addWidget(self.name_input)
        
        # Información adicional
        info_text = TEXTS[self.wizard.current_language]["personalization_info"]
        
        info_label = QLabel(info_text)
        info_label.setProperty("class", "description")
        info_label.setWordWrap(True)
        form_layout.addWidget(info_label)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Espaciador final
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.setLayout(layout)
        
        # Registrar campo requerido
        self.registerField("user_name*", self.name_input)
    
    def update_texts(self):
        """Actualizar textos de la página cuando cambia el idioma"""
        try:
            title_labels = self.findChildren(QLabel)
            for label in title_labels:
                if label.property("class") == "title":
                    label.setText(self.wizard.get_text("user_title"))
                elif label.property("class") == "subtitle":
                    label.setText(self.wizard.get_text("user_subtitle"))
                elif label.property("class") == "description":
                    # Actualizar textos descriptivos
                    if "llame" in label.text() or "call you" in label.text():
                        label.setText(self.wizard.get_text("how_to_call_you"))
                    elif "personalizar" in label.text() or "personalize" in label.text():
                        label.setText(self.wizard.get_text("personalization_info"))
            
            # Actualizar placeholder
            if hasattr(self, 'name_input'):
                self.name_input.setPlaceholderText(self.wizard.get_text("name_placeholder"))
            
            # Actualizar group boxes
            group_boxes = self.findChildren(QGroupBox)
            for group in group_boxes:
                if "Personal" in group.title() or "Información" in group.title():
                    group.setTitle(self.wizard.get_text("personal_information"))
        except Exception as e:
            logger.warning(f"Error actualizando textos de UserInfoPage: {str(e)}")
    
    def on_name_changed(self, text):
        """Manejar cambio en el nombre"""
        self.wizard.wizard_config["user_name"] = text.strip()
    
    def validatePage(self):
        """Validar página antes de continuar"""
        name = self.name_input.text().strip()
        if len(name) < 2:
            QMessageBox.warning(self, "Nombre requerido", 
                              "Por favor ingresa un nombre de al menos 2 caracteres.")
            return False
        
        self.wizard.wizard_config["user_name"] = name
        logger.info(f"✅ Nombre de usuario configurado: {name}")
        return True

# ============================================================================
# PÁGINA 6: DETECCIÓN DE CUDA
# ============================================================================

class CudaDetectionPage(QWizardPage):
    """Sexta página: Detección de hardware CUDA"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.cuda_status = "checking"  # checking, available, not_available, error
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interfaz de usuario - OPTIMIZADA PARA ALTURA REDUCIDA"""
        layout = QVBoxLayout()
        
        # Título compacto
        title = QLabel(TEXTS[self.wizard.current_language]["cuda_title"])
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtítulo compacto
        subtitle = QLabel(TEXTS[self.wizard.current_language]["cuda_subtitle"])
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Estado de detección compacto
        self.status_label = QLabel(TEXTS[self.wizard.current_language]["detecting_hardware"])
        self.status_label.setProperty("class", "description")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Barra de progreso compacta
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminado
        self.progress_bar.setMaximumHeight(20)  # Altura fija reducida
        layout.addWidget(self.progress_bar)
        
        # Espaciador mínimo
        layout.addItem(QSpacerItem(20, 5, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # SCROLL AREA para contenido largo
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setMaximumHeight(250)  # Altura máxima del scroll
        
        # Widget contenedor para scroll
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Información sobre CUDA - COMPACTA
        info_group = QGroupBox(TEXTS[self.wizard.current_language]["hardware_acceleration"])
        info_layout = QVBoxLayout()
        
        cuda_info = self.get_cuda_info_compact()  # Versión compacta
        info_label = QLabel(cuda_info)
        info_label.setProperty("class", "description")
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        
        info_group.setLayout(info_layout)
        scroll_layout.addWidget(info_group)
        
        # Resultados de detección (inicialmente oculto)
        self.results_group = QGroupBox(self.wizard.get_text("results"))
        self.results_layout = QVBoxLayout()
        self.results_group.setLayout(self.results_layout)
        self.results_group.setVisible(False)
        scroll_layout.addWidget(self.results_group)
        
        # Espaciador en scroll
        scroll_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Configurar scroll area
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Espaciador final mínimo
        layout.addItem(QSpacerItem(20, 5, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.setLayout(layout)
        
        # Iniciar detección automática
        QTimer.singleShot(1500, self.detect_cuda)
    
    def get_cuda_info_compact(self):
        """Obtener información compacta sobre CUDA para espacios reducidos"""
        return self.wizard.get_text("cuda_info_compact")
    
    def get_cuda_info(self):
        """Obtener información completa sobre CUDA (método legacy)"""
        if self.wizard.current_language == "es":
            return ("EVA puede aprovechar la aceleración por hardware NVIDIA CUDA para mejorar significativamente el rendimiento:\n\n"
                   "🚀 Beneficios de CUDA:\n"
                   "• ⚡ Respuestas de IA hasta 10x más rápidas\n"
                   "• 🎯 Mejor rendimiento en modelos grandes\n"
                   "• 💾 Uso eficiente de memoria GPU\n"
                   "• 🔥 Menor uso de CPU\n\n"
                   "📝 Nota: EVA funciona perfectamente sin CUDA, pero la aceleración GPU mejora la experiencia.")
        else:
            return ("EVA can leverage NVIDIA CUDA hardware acceleration to significantly improve performance:\n\n"
                   "🚀 CUDA Benefits:\n"
                   "• ⚡ AI responses up to 10x faster\n"
                   "• 🎯 Better performance on large models\n"
                   "• 💾 Efficient GPU memory usage\n"
                   "• 🔥 Lower CPU usage\n\n"
                   "📝 Note: EVA works perfectly without CUDA, but GPU acceleration enhances the experience.")
    
    def detect_cuda(self):
        """Detectar disponibilidad de CUDA"""
        self.status_label.setText(self.wizard.get_text("detecting_hardware"))
        self.progress_bar.setRange(0, 0)
        
        # Ejecutar detección en hilo separado
        self.detect_thread = CudaDetectionThread()
        self.detect_thread.detection_completed.connect(self.on_cuda_detection_completed)
        self.detect_thread.start()
    
    def on_cuda_detection_completed(self, cuda_available, gpu_info):
        """Manejar resultado de detección de CUDA"""
        self.cuda_status = "available" if cuda_available else "not_available"
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        
        # Actualizar configuración
        self.wizard.wizard_config["cuda_available"] = cuda_available
        
        # Mostrar resultados
        self.show_detection_results(cuda_available, gpu_info)
        
        if cuda_available:
            self.status_label.setText(TEXTS[self.wizard.current_language]["cuda_available"])
            logger.info("✅ CUDA detectado y disponible")
        else:
            self.status_label.setText(TEXTS[self.wizard.current_language]["cuda_not_available"])
            logger.info("ℹ️ CUDA no disponible, usando CPU")
    
    def show_detection_results(self, cuda_available, gpu_info):
        """Mostrar resultados detallados de la detección"""
        # Limpiar layout anterior
        for i in reversed(range(self.results_layout.count())):
            self.results_layout.itemAt(i).widget().setParent(None)
        
        if cuda_available:
            # GPU encontrada
            gpu_label = QLabel(f"🎮 GPU: {gpu_info.get('name', 'NVIDIA GPU')}")
            gpu_label.setProperty("class", "description")
            self.results_layout.addWidget(gpu_label)
            
            memory_label = QLabel(f"💾 VRAM: {gpu_info.get('memory', 'N/A')}")
            memory_label.setProperty("class", "description")
            self.results_layout.addWidget(memory_label)
            
            cuda_label = QLabel(f"⚡ CUDA: {gpu_info.get('cuda_version', 'Disponible')}")
            cuda_label.setProperty("class", "description")
            self.results_layout.addWidget(cuda_label)
            
            # Recomendación
            recommendation = QLabel(TEXTS[self.wizard.current_language]["gpu_recommendation"])
            recommendation.setProperty("class", "description")
            recommendation.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.results_layout.addWidget(recommendation)
        else:
            # Sin GPU o CUDA
            cpu_label = QLabel(TEXTS[self.wizard.current_language]["cpu_mode"])
            cpu_label.setProperty("class", "description")
            self.results_layout.addWidget(cpu_label)
            
            reason_text = self.wizard.get_text("reason_label") + " " + gpu_info.get('reason', self.wizard.get_text("gpu_not_detected"))
            reason_label = QLabel(reason_text)
            reason_label.setProperty("class", "description")
            self.results_layout.addWidget(reason_label)
            
            # Recomendación
            recommendation = QLabel(TEXTS[self.wizard.current_language]["cpu_recommendation"])
            recommendation.setProperty("class", "description")
            recommendation.setStyleSheet("color: #00bcd4; font-weight: bold;")
            self.results_layout.addWidget(recommendation)
        
        self.results_group.setVisible(True)
    
    def update_texts(self):
        """Actualizar textos de la página cuando cambia el idioma"""
        try:
            # Actualizar títulos
            title_labels = self.findChildren(QLabel)
            for label in title_labels:
                if label.property("class") == "title":
                    label.setText(self.wizard.get_text("cuda_title"))
                elif label.property("class") == "subtitle":
                    label.setText(self.wizard.get_text("cuda_subtitle"))
            
            # Actualizar estado de detección
            if hasattr(self, 'status_label'):
                current_text = self.status_label.text()
                if "Detectando" in current_text or "Detecting" in current_text:
                    self.status_label.setText(self.wizard.get_text("detecting_hardware"))
                elif "disponible" in current_text or "available" in current_text:
                    self.status_label.setText(self.wizard.get_text("cuda_available"))
                elif "no disponible" in current_text or "not available" in current_text:
                    self.status_label.setText(self.wizard.get_text("cuda_not_available"))
            
            # Actualizar group boxes
            group_boxes = self.findChildren(QGroupBox)
            for group in group_boxes:
                if "Hardware" in group.title() or "Aceleración" in group.title():
                    group.setTitle(self.wizard.get_text("hardware_acceleration"))
                elif "Resultados" in group.title() or "Results" in group.title():
                    group.setTitle(self.wizard.get_text("results"))
            
            # Actualizar contenido de información CUDA
            if hasattr(self, 'info_label'):
                self.info_label.setText(self.get_cuda_info_compact())
        except Exception as e:
            logger.warning(f"Error actualizando textos de CudaDetectionPage: {str(e)}")

class CudaDetectionThread(QThread):
    """Hilo para detectar CUDA sin bloquear la UI"""
    detection_completed = Signal(bool, dict)  # cuda_available, gpu_info
    
    def run(self):
        """Ejecutar detección de CUDA"""
        try:
            # Intentar importar torch para verificar CUDA
            import torch
            
            if torch.cuda.is_available():
                # CUDA disponible
                gpu_count = torch.cuda.device_count()
                gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "NVIDIA GPU"
                
                # Obtener información de memoria
                if gpu_count > 0:
                    memory_total = torch.cuda.get_device_properties(0).total_memory
                    memory_gb = memory_total / (1024**3)
                    memory_str = f"{memory_gb:.1f} GB"
                else:
                    memory_str = "N/A"
                
                cuda_version = torch.version.cuda
                
                gpu_info = {
                    "name": gpu_name,
                    "memory": memory_str,
                    "cuda_version": cuda_version,
                    "device_count": gpu_count
                }
                
                self.detection_completed.emit(True, gpu_info)
            else:
                # CUDA no disponible
                gpu_info = {
                    "reason": "CUDA no disponible en PyTorch"
                }
                self.detection_completed.emit(False, gpu_info)
                
        except ImportError:
            # PyTorch no instalado
            gpu_info = {
                "reason": "PyTorch no instalado"
            }
            self.detection_completed.emit(False, gpu_info)
        except Exception as e:
            # Error en detección
            gpu_info = {
                "reason": f"Error en detección: {str(e)}"
            }
            self.detection_completed.emit(False, gpu_info)

# ============================================================================
# PÁGINA 7: DESCARGA DE MODELOS
# ============================================================================

class ModelDownloadPage(QWizardPage):
    """Séptima página: Descarga de modelos de IA"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.download_in_progress = False
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Título
        title = QLabel(self.wizard.get_text("models_title"))
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel(self.wizard.get_text("models_subtitle"))
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Espaciador
        layout.addItem(QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Selección de modelos
        models_group = QGroupBox(self.wizard.get_text("available_models"))
        models_layout = QVBoxLayout()
        
        self.model_checkboxes = {}
        license_type = self.wizard.wizard_config.get("license_type", "FREE")
        available_models = MODELS_CONFIG.get(license_type, {})
        
        for model_id, model_info in available_models.items():
            model_frame = QFrame()
            model_frame.setFrameStyle(QFrame.Box)
            model_frame_layout = QVBoxLayout()
            
            # Checkbox del modelo
            checkbox = QCheckBox(f"{model_info['name']} ({model_info['size']})")
            checkbox.setChecked(model_info.get("recommended", False))
            self.model_checkboxes[model_id] = checkbox
            model_frame_layout.addWidget(checkbox)
            
            # Descripción del modelo
            # Obtener descripción traducida
            if "description_key" in model_info:
                description = self.wizard.get_text(model_info["description_key"])
            else:
                description = model_info.get("description", "")
            desc_label = QLabel(description)
            desc_label.setProperty("class", "description")
            desc_label.setWordWrap(True)
            model_frame_layout.addWidget(desc_label)
            
            # Etiqueta de recomendado
            if model_info.get("recommended", False):
                rec_label = QLabel(self.wizard.get_text("recommended_model"))
                rec_label.setStyleSheet("color: #FFD700; font-weight: bold;")
                model_frame_layout.addWidget(rec_label)
            
            model_frame.setLayout(model_frame_layout)
            models_layout.addWidget(model_frame)
        
        models_group.setLayout(models_layout)
        layout.addWidget(models_group)
        
        # Información de descarga
        download_info = ("Los modelos se descargarán usando Ollama. Asegúrate de tener suficiente espacio en disco. "
                        "Puedes descargar modelos adicionales más tarde desde la configuración." 
                        if self.wizard.current_language == "es"
                        else "Models will be downloaded using Ollama. Make sure you have enough disk space. "
                             "You can download additional models later from settings.")
        
        info_label = QLabel(download_info)
        info_label.setProperty("class", "description")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Progreso de descarga
        self.download_group = QGroupBox(self.wizard.get_text("download_progress"))
        download_layout = QVBoxLayout()
        
        self.current_model_label = QLabel("")
        self.current_model_label.setProperty("class", "description")
        download_layout.addWidget(self.current_model_label)
        
        self.download_progress = QProgressBar()
        download_layout.addWidget(self.download_progress)
        
        self.download_status_label = QLabel("")
        self.download_status_label.setProperty("class", "description")
        download_layout.addWidget(self.download_status_label)
        
        self.download_group.setLayout(download_layout)
        self.download_group.setVisible(False)
        layout.addWidget(self.download_group)
        
        # Botones de descarga
        buttons_layout = QHBoxLayout()
        
        self.download_button = QPushButton(self.wizard.get_text("download_models_btn"))
        self.download_button.clicked.connect(self.start_download)
        buttons_layout.addWidget(self.download_button)
        
        # Botón para saltar descarga
        self.skip_button = QPushButton(self.wizard.get_text("skip_download_btn") if hasattr(self.wizard, 'get_text') else "Saltar descarga")
        self.skip_button.clicked.connect(self.skip_download)
        self.skip_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 193, 7, 0.8);
                color: #000000;
                border: 2px solid #ffc107;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ffc107;
            }
        """)
        buttons_layout.addWidget(self.skip_button)
        
        layout.addLayout(buttons_layout)
        
        # Espaciador final
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.setLayout(layout)
    
    def start_download(self):
        """Iniciar descarga de modelos seleccionados"""
        selected_models = []
        for model_id, checkbox in self.model_checkboxes.items():
            if checkbox.isChecked():
                selected_models.append(model_id)
        
        if not selected_models:
            QMessageBox.warning(self, self.wizard.get_text("no_models_selected"), 
                              self.wizard.get_text("select_model_warning"))
            return
        
        # Verificar que Ollama esté disponible
        if not self.wizard.wizard_config.get("ollama_ready", False):
            QMessageBox.warning(self, "Ollama requerido", 
                              "Ollama debe estar instalado para descargar modelos.")
            return
        
        # Iniciar descarga
        self.download_in_progress = True
        self.download_button.setEnabled(False)
        self.skip_button.setEnabled(False)  # Deshabilitar saltar durante descarga
        self.download_group.setVisible(True)
        
        # Ejecutar descarga en hilo separado
        self.download_thread = ModelDownloadThread(selected_models)
        self.download_thread.progress_updated.connect(self.on_download_progress)
        self.download_thread.model_started.connect(self.on_model_download_started)
        self.download_thread.download_completed.connect(self.on_download_completed)
        self.download_thread.start()
        
        logger.info(f"🚀 Starting model download: {selected_models}")
    
    def skip_download(self):
        """Saltar la descarga de modelos"""
        reply = QMessageBox.question(
            self, 
            "Saltar descarga" if self.wizard.current_language == "es" else "Skip download",
            ("¿Estás seguro de que quieres saltar la descarga de modelos? "
             "Podrás descargarlos más tarde desde la configuración." 
             if self.wizard.current_language == "es" else
             "Are you sure you want to skip model download? "
             "You can download them later from settings."),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Marcar como completado sin modelos
            self.wizard.wizard_config["selected_models"] = []
            self.wizard.wizard_config["download_skipped"] = True
            
            # Mostrar mensaje informativo
            self.current_model_label.setText(
                "Descarga omitida - Podrás descargar modelos más tarde" 
                if self.wizard.current_language == "es" else
                "Download skipped - You can download models later"
            )
            self.download_group.setVisible(True)
            self.download_progress.setVisible(False)
            
            # Notificar que la página está completa
            self.completeChanged.emit()
            logger.info("📋 Model download skipped by user")
    
    def on_model_download_started(self, model_name):
        """Manejar inicio de descarga de modelo"""
        self.current_model_label.setText(self.wizard.get_text("downloading_model").format(model_name=model_name))
        self.download_progress.setRange(0, 0)  # Indeterminado
    
    def on_download_progress(self, progress, status):
        """Manejar progreso de descarga"""
        if progress >= 0:
            self.download_progress.setRange(0, 100)
            self.download_progress.setValue(progress)
        
        self.download_status_label.setText(status)
    
    def on_download_completed(self, success, downloaded_models, error_message):
        """Manejar finalización de descarga"""
        self.download_in_progress = False
        self.download_button.setEnabled(True)
        self.skip_button.setEnabled(True)  # Rehabilitar botón saltar
        
        if success:
            self.wizard.wizard_config["selected_models"] = downloaded_models
            self.current_model_label.setText(self.wizard.get_text("download_completed"))
            self.download_progress.setRange(0, 100)
            self.download_progress.setValue(100)
            self.download_status_label.setText(f"{self.wizard.get_text('models_downloaded')}: {', '.join(downloaded_models)}")
            logger.info(f"✅ Models downloaded successfully: {downloaded_models}")
            
            # CRÍTICO: Notificar al wizard que la página está completa
            self.completeChanged.emit()
        else:
            self.current_model_label.setText(self.wizard.get_text("download_error"))
            self.download_status_label.setText(error_message)
            logger.error(f"❌ Error downloading models: {error_message}")
            
            # También emitir la señal en caso de error para permitir continuar
            self.completeChanged.emit()
    
    def isComplete(self):
        """Verificar si la página está completa"""
        # Permitir continuar si:
        # 1. Se descargaron modelos exitosamente, O
        # 2. No hay descarga en progreso (permite saltarse la descarga)
        has_downloaded_models = len(self.wizard.wizard_config.get("selected_models", [])) > 0
        no_download_in_progress = not getattr(self, 'download_in_progress', False)
        
        return has_downloaded_models or no_download_in_progress
    
    def update_texts(self):
        """Actualizar textos de la página cuando cambia el idioma"""
        try:
            title_labels = self.findChildren(QLabel)
            for label in title_labels:
                if label.property("class") == "title":
                    label.setText(self.wizard.get_text("models_title"))
                elif label.property("class") == "subtitle":
                    label.setText(self.wizard.get_text("models_subtitle"))
            
            group_boxes = self.findChildren(QGroupBox)
            for group in group_boxes:
                if "Modelos" in group.title() or "Models" in group.title():
                    group.setTitle(self.wizard.get_text("available_models"))
                elif "Progreso" in group.title() or "Progress" in group.title():
                    group.setTitle(self.wizard.get_text("download_progress"))
            
            # Actualizar botón de descarga
            if hasattr(self, 'download_button'):
                self.download_button.setText(self.wizard.get_text("download_models_btn"))
                
        except Exception as e:
            logger.warning(f"Error actualizando textos de ModelDownloadPage: {str(e)}")
            
            group_boxes = self.findChildren(QGroupBox)
            for group in group_boxes:
                if "Modelos" in group.title() or "Models" in group.title():
                    group.setTitle(self.wizard.get_text("available_models"))
                elif "Progreso" in group.title() or "Progress" in group.title():
                    group.setTitle(self.wizard.get_text("download_progress"))
        except Exception as e:
            logger.warning(f"Error actualizando textos de ModelDownloadPage: {str(e)}")

class ModelDownloadThread(QThread):
    """Hilo para descargar modelos sin bloquear la UI"""
    progress_updated = Signal(int, str)  # progress, status
    model_started = Signal(str)  # model_name
    download_completed = Signal(bool, list, str)  # success, downloaded_models, error_message
    
    def __init__(self, models_to_download):
        super().__init__()
        self.models_to_download = models_to_download
    
    def run(self):
        """Ejecutar descarga de modelos"""
        downloaded_models = []
        
        try:
            for i, model_id in enumerate(self.models_to_download):
                # Obtener información del modelo
                model_info = None
                for license_models in MODELS_CONFIG.values():
                    if model_id in license_models:
                        model_info = license_models[model_id]
                        break
                
                if not model_info:
                    continue
                
                model_name = model_info["name"]
                self.model_started.emit(model_name)
                
                # Ejecutar ollama pull
                try:
                    process = subprocess.Popen(
                        ["ollama", "pull", model_id],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        universal_newlines=True
                    )
                    
                    # Monitorear progreso
                    while True:
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            # Parsear progreso de ollama (simplificado)
                            if "pulling" in output.lower():
                                progress = int((i / len(self.models_to_download)) * 100)
                                self.progress_updated.emit(progress, output.strip())
                    
                    # Verificar resultado
                    return_code = process.poll()
                    if return_code == 0:
                        downloaded_models.append(model_id)
                        final_progress = int(((i + 1) / len(self.models_to_download)) * 100)
                        self.progress_updated.emit(final_progress, f"✅ {model_name} downloaded")
                    else:
                        error_output = process.stderr.read()
                        self.progress_updated.emit(-1, f"❌ Error downloading {model_name}: {error_output}")
                        
                except Exception as e:
                    self.progress_updated.emit(-1, f"❌ Error: {str(e)}")
            
            # Finalizar
            if downloaded_models:
                self.download_completed.emit(True, downloaded_models, "")
            else:
                self.download_completed.emit(False, [], "No se pudo descargar ningún modelo")
                
        except Exception as e:
            self.download_completed.emit(False, [], f"Error general: {str(e)}")

# ============================================================================
# PÁGINA 8: FINALIZACIÓN
# ============================================================================

class CompletionPage(QWizardPage):
    """Octava página: Finalización del wizard"""
    
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        layout = QVBoxLayout()
        
        # Título
        title = QLabel(self.wizard.get_text("completion_title"))
        title.setProperty("class", "title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtítulo
        subtitle = QLabel(self.wizard.get_text("completion_subtitle"))
        subtitle.setProperty("class", "subtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        # Espaciador
        layout.addItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Mensaje de éxito
        success_message = self.get_success_message()
        success_label = QLabel(success_message)
        success_label.setProperty("class", "description")
        success_label.setWordWrap(True)
        success_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(success_label)
        
        # Espaciador
        layout.addItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed))
        
        # Resumen de configuración
        summary_group = QGroupBox(TEXTS[self.wizard.current_language]["configuration_summary"])
        summary_layout = QVBoxLayout()
        
        summary_items = self.get_configuration_summary()
        for item in summary_items:
            item_label = QLabel(f"• {item}")
            item_label.setProperty("class", "description")
            summary_layout.addWidget(item_label)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Próximos pasos
        next_steps_group = QGroupBox(TEXTS[self.wizard.current_language]["next_steps"])
        next_steps_layout = QVBoxLayout()
        
        next_steps = self.get_next_steps()
        for step in next_steps:
            step_label = QLabel(f"• {step}")
            step_label.setProperty("class", "description")
            next_steps_layout.addWidget(step_label)
        
        next_steps_group.setLayout(next_steps_layout)
        layout.addWidget(next_steps_group)
        
        # Espaciador final
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        self.setLayout(layout)
    
    def get_success_message(self):
        """Obtener mensaje de éxito personalizado"""
        user_name = self.wizard.wizard_config.get("user_name", "Usuario")
        
        license_type = self.wizard.wizard_config.get("license_type", "FREE")
        if license_type == "PREMIUM":
            return self.wizard.get_text("congratulations_premium").format(name=user_name)
        else:
            return self.wizard.get_text("congratulations_free").format(name=user_name)
    
    def get_configuration_summary(self):
        """Obtener resumen de la configuración"""
        config = self.wizard.wizard_config
        
        language_display = "Español" if config.get('language') == 'es' else "English"
        cuda_status = "✅ Disponible" if config.get('cuda_available') else "❌ No disponible"
        if self.wizard.current_language == "en":
            language_display = "Spanish" if config.get('language') == 'es' else "English"
            cuda_status = "✅ Available" if config.get('cuda_available') else "❌ Not available"
        
        summary = [
            self.wizard.get_text("user_config").format(user_name=config.get('user_name', 'N/A')),
            self.wizard.get_text("language_config").replace("English", language_display),
            self.wizard.get_text("license_config").format(license_type=config.get('license_type', 'FREE')),
            self.wizard.get_text("cuda_config").format(cuda_status=cuda_status),
            self.wizard.get_text("models_config").format(models_count=len(config.get('selected_models', [])))
        ]
        
        return summary
    
    def get_next_steps(self):
        """Obtener lista de próximos pasos"""
        return [
            self.wizard.get_text("start_conversation"),
            self.wizard.get_text("explore_settings"),
            self.wizard.get_text("adjust_voice")
        ]
    
    def initializePage(self):
        """Inicializar página al mostrarla"""
        # Marcar wizard como completado
        self.wizard.wizard_config["wizard_completed"] = True
        
        # Actualizar el estado de la licencia después del wizard
        try:
            # Actualizar el estado de la licencia en el session_manager
            from core.session_manager import SessionManager
            session_manager = SessionManager(self.wizard.parent().config)
            session_manager.update_license_status()
            logger.info("Estado de licencia actualizado después del wizard")
        except Exception as e:
            logger.error(f"Error actualizando el estado de la licencia: {str(e)}")
            # Continuar incluso si hay un error al actualizar la licencia
        logger.info("🎉 Wizard de primera ejecución completado exitosamente")
    
    def update_texts(self):
        """Actualizar textos de la página cuando cambia el idioma"""
        try:
            title_labels = self.findChildren(QLabel)
            for label in title_labels:
                if label.property("class") == "title":
                    label.setText(self.wizard.get_text("completion_title"))
                elif label.property("class") == "subtitle":
                    label.setText(self.wizard.get_text("completion_subtitle"))
            
            group_boxes = self.findChildren(QGroupBox)
            for group in group_boxes:
                if "Resumen" in group.title() or "Summary" in group.title():
                    group.setTitle(self.wizard.get_text("configuration_summary"))
                elif "Próximos" in group.title() or "Next" in group.title():
                    group.setTitle(self.wizard.get_text("next_steps"))
        except Exception as e:
            logger.warning(f"Error actualizando textos de CompletionPage: {str(e)}")