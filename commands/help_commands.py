"""
Comandos de ayuda unificados para EVA
Optimizado para chat con comandos naturales únicos
Filosofía: 1 comando = 1 función
"""

import logging

from utils.bilingual_command import BilingualCommand

logger = logging.getLogger("EVA")


class HelpCommandHandler:
    """Handler unificado para comandos de ayuda (optimizado para chat)"""
    
    def __init__(self, processor):
        self.processor = processor
        self.config = processor.config
        self.language_manager = processor.language_manager
        
        # Comandos de ayuda unificados - ÚNICOS Y NATURALES (para chat)
        self.commands = {
            # Ayuda general - menú principal
            BilingualCommand("ayuda", "help"): self._show_help_menu,
            
            # Lista completa de comandos disponibles
            BilingualCommand("comandos", "commands"): self._show_all_commands,
            
            # Manual completo/documentación
            BilingualCommand("manual", "manual"): self._show_full_manual,
        }
    
    @property
    def lang(self) -> str:
        """Obtiene el idioma actual"""
        language = self.config.get("language", "es")
        if isinstance(language, str) and language in ["es", "en"]:
            return language
        return "es"
    
    def can_handle(self, text: str) -> bool:
        """Verifica si puede manejar el comando"""
        text_lower = text.lower().strip()
        
        # Verificar comandos de ayuda
        for bilingual_cmd in self.commands.keys():
            if bilingual_cmd.matches(text_lower):
                return True
        
        # Verificar ayuda específica (ej: "ayuda volumen", "help wifi")
        if text_lower.startswith("ayuda ") or text_lower.startswith("help "):
            return True
        
        # Verificar navegación numérica del menú de ayuda (1-10)
        if text_lower in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
            return True
        
        return False
    
    def handle(self, text: str, chat_window) -> bool:
        """Maneja el comando de ayuda"""
        try:
            text_lower = text.lower().strip()
            
            # Verificar navegación numérica del menú (1-10)
            if text_lower in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
                return self._handle_menu_navigation(text_lower, chat_window)
            
            # Verificar ayuda específica
            if text_lower.startswith("ayuda ") or text_lower.startswith("help "):
                topic = text_lower.split(" ", 1)[1] if len(text_lower.split()) > 1 else ""
                return self._show_specific_help(topic, chat_window)
            
            # Buscar comando coincidente
            for bilingual_cmd, handler_func in self.commands.items():
                if bilingual_cmd.matches(text_lower):
                    logger.info(f"📚 Ejecutando comando de ayuda: {bilingual_cmd}")
                    return handler_func(chat_window)
            
            return False
            
        except Exception as e:
            logger.error(f"Error en comando de ayuda: {str(e)}")
            error_msg = self.language_manager.get_text("responses.help_system_error")
            chat_window.add_message(error_msg, is_user=False)
            return True
    
    def _show_help_menu(self, chat_window) -> bool:
        """Muestra el menú principal de ayuda interactivo"""
        try:
            if self.lang == "es":
                help_menu = """
🏠 **EVA - Centro de Ayuda Interactivo**
═══════════════════════════════════════

**📋 MENÚ PRINCIPAL - Selecciona una opción:**

**1️⃣ Gestión de Archivos** 📁
   • Lista, ordena y abre archivos
   • Comando: `ayuda archivos`

**2️⃣ Control Multimedia** 🎵
   • Controla VLC, MPC-HC, Kodi
   • Comando: `ayuda multimedia`

**3️⃣ Control de Volumen** 🔊
   • Volumen del sistema y aplicaciones
   • Comando: `ayuda volumen`

**4️⃣ Control del Sistema** 🖥️
   • Apagar, reiniciar, cerrar sesión
   • Comando: `ayuda sistema`

**5️⃣ Control de Windows** 🪟
   • WiFi, Bluetooth, brillo
   • Comando: `ayuda windows`

**6️⃣ IA y Conversación** 🤖
   • Chat con IA, modelos, documentos
   • Comando: `ayuda ia`

**7️⃣ Gestión de Citas** 📅
   • Crear, listar, cancelar citas
   • Comando: `ayuda citas`

**8️⃣ Búsqueda y Web** 🔍
   • Búsquedas en Google
   • Comando: `ayuda busqueda`

**9️⃣ Dictado** 🎤
   • Sistema de dictado inteligente
   • Comando: `ayuda dictado`

**🔟 Configuración** ⚙️
   • Actualizaciones y ajustes
   • Comando: `ayuda config`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📖 COMANDOS RÁPIDOS:**
• `comandos` - Lista completa de comandos
• `manual` - Manual detallado completo
• `ayuda [tema]` - Ayuda específica
• `ayuda ejemplos` - Ejemplos prácticos

**💡 NAVEGACIÓN:**
• Escribe el **número** (1-10) para ir a esa sección
• Escribe el **comando** específico (ej: `ayuda archivos`)
• Todos los comandos funcionan en **español** e **inglés**
"""
            else:
                help_menu = """
🏠 **EVA - Interactive Help Center**
═══════════════════════════════════

**📋 MAIN MENU - Select an option:**

**1️⃣ File Management** 📁
   • List, sort and open files
   • Command: `help files`

**2️⃣ Multimedia Control** 🎵
   • Control VLC, MPC-HC, Kodi
   • Command: `help multimedia`

**3️⃣ Volume Control** 🔊
   • System and application volume
   • Command: `help volume`

**4️⃣ System Control** 🖥️
   • Shutdown, restart, logout
   • Command: `help system`

**5️⃣ Windows Control** 🪟
   • WiFi, Bluetooth, brightness
   • Command: `help windows`

**6️⃣ AI and Conversation** 🤖
   • AI chat, models, documents
   • Command: `help ai`

**7️⃣ Appointment Management** 📅
   • Create, list, cancel appointments
   • Command: `help appointments`

**8️⃣ Search and Web** 🔍
   • Google searches
   • Command: `help search`

**9️⃣ Dictation** 🎤
   • Intelligent dictation system
   • Command: `help dictation`

**🔟 Configuration** ⚙️
   • Updates and settings
   • Command: `help config`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📖 QUICK COMMANDS:**
• `commands` - Complete command list
• `manual` - Detailed manual
• `help [topic]` - Specific help
• `help examples` - Practical examples

**💡 NAVIGATION:**
• Type the **number** (1-10) to go to that section
• Type the **specific command** (e.g., `help files`)
• All commands work in **Spanish** and **English**
"""
            
            chat_window.add_message(help_menu, is_user=False)
            logger.info("📚 Menú de ayuda mostrado")
            return True
            
        except Exception as e:
            logger.error(f"Error mostrando menú de ayuda: {str(e)}")
            return False
    
    def _show_all_commands(self, chat_window) -> bool:
        """Muestra lista completa de comandos disponibles"""
        try:
            if self.lang == "es":
                commands_list = """
📋 **EVA - Lista Completa de Comandos**
======================================

**ARCHIVOS:**
• lista archivos, ordena archivos

**MULTIMEDIA:**
• pausa, reproduce, siguiente, anterior, para
• sube volumen multimedia, baja volumen multimedia
• silencia multimedia, pantalla completa

**SISTEMA:**
• sube volumen, baja volumen, silencia, volumen [N]
• apaga, reinicia, cierra sesión

**WINDOWS:**
• activa wifi, desactiva wifi, estado wifi
• activa bluetooth, desactiva bluetooth, estado bluetooth
• sube brillo, baja brillo, brillo [N]

**BÚSQUEDA:**
• busca [término]

**IA:**
• eva [pregunta], modelo

**AYUDA:**
• ayuda, comandos, manual, ayuda [tema]

💡 **Todos los comandos también funcionan en inglés**
"""
            else:
                commands_list = """
📋 **EVA - Complete Command List**
=================================

**FILES:**
• list files, sort files

**MULTIMEDIA:**
• pause, play, next, previous, stop
• volume up multimedia, volume down multimedia
• mute multimedia, fullscreen

**SYSTEM:**
• volume up, volume down, mute, volume [N]
• shutdown, restart, logout

**WINDOWS:**
• enable wifi, disable wifi, wifi status
• enable bluetooth, disable bluetooth, bluetooth status
• brightness up, brightness down, brightness [N]

**SEARCH:**
• search [term]

**AI:**
• eva [question], model

**HELP:**
• help, commands, manual, help [topic]

💡 **All commands also work in Spanish**
"""
            
            chat_window.add_message(commands_list, is_user=False)
            logger.info("📚 Lista completa de comandos mostrada")
            return True
            
        except Exception as e:
            logger.error(f"Error mostrando lista de comandos: {str(e)}")
            return False
    
    def _show_full_manual(self, chat_window) -> bool:
        """Muestra manual completo/documentación"""
        try:
            if self.lang == "es":
                manual = """
📖 **EVA - Manual Completo**
===========================

**¿Qué es EVA?**
EVA es un asistente de voz inteligente que funciona 100% offline.
Controla tu sistema, archivos y aplicaciones con comandos naturales.

**Filosofía de Comandos:**
• 1 comando = 1 función específica
• Comandos naturales en español e inglés
• Sin variantes confusas o duplicadas

**Categorías de Comandos:**

🔊 **VOLUMEN DEL SISTEMA:**
- Comandos exactos: "sube volumen", "baja volumen", "silencia"
- Volumen específico: "volumen 50" (0-100)
- Funciona con cualquier aplicación

🎵 **MULTIMEDIA:**
- Control universal para VLC, MPC-HC, Kodi
- "pausa" funciona como play/pause toggle
- "siguiente"/"anterior" para navegación
- "pantalla completa" para modo fullscreen

📁 **ARCHIVOS:**
- "lista archivos" muestra archivos numerados
- "ordena archivos" configura ordenamiento
- Recuerda la última carpeta abierta

🖥️ **SISTEMA:**
- Comandos peligrosos requieren confirmación
- "apaga" → confirmación → ejecución
- Tiempo de espera de 5 segundos

🪟 **WINDOWS:**
- Control de WiFi y Bluetooth via PowerShell
- Control de brillo para laptops
- Comandos ejecutados en segundo plano

🤖 **IA:**
- Conversación natural con "eva [pregunta]"
- Modelos locales via Ollama
- Funciona completamente offline

**Consejos de Uso:**
• Los comandos son exactos: "apaga" funciona, "apagar" NO
• Usa confirmación para comandos peligrosos
• Todos los comandos son bilingües
• El sistema recuerda configuraciones

**Solución de Problemas:**
• Si un comando no funciona, verifica la sintaxis exacta
• Usa "comandos" para ver la lista completa
• Usa "ayuda [tema]" para ayuda específica
"""
            else:
                manual = """
📖 **EVA - Complete Manual**
===========================

**What is EVA?**
EVA is an intelligent voice assistant that works 100% offline.
Control your system, files and applications with natural commands.

**Command Philosophy:**
• 1 command = 1 specific function
• Natural commands in Spanish and English
• No confusing or duplicate variants

**Command Categories:**

🔊 **SYSTEM VOLUME:**
- Exact commands: "volume up", "volume down", "mute"
- Specific volume: "volume 50" (0-100)
- Works with any application

🎵 **MULTIMEDIA:**
- Universal control for VLC, MPC-HC, Kodi
- "pause" works as play/pause toggle
- "next"/"previous" for navigation
- "fullscreen" for fullscreen mode

📁 **FILES:**
- "list files" shows numbered files
- "sort files" configures sorting
- Remembers last opened folder

🖥️ **SYSTEM:**
- Dangerous commands require confirmation
- "shutdown" → confirmation → execution
- 5-second wait time

🪟 **WINDOWS:**
- WiFi and Bluetooth control via PowerShell
- Brightness control for laptops
- Commands executed in background

🤖 **AI:**
- Natural conversation with "eva [question]"
- Local models via Ollama
- Works completely offline

**Usage Tips:**
• Commands are exact: "shutdown" works, "shut down" does NOT
• Use confirmation for dangerous commands
• All commands are bilingual
• System remembers configurations

**Troubleshooting:**
• If a command doesn't work, check exact syntax
• Use "commands" to see complete list
• Use "help [topic]" for specific help
"""
            
            chat_window.add_message(manual, is_user=False)
            logger.info("📚 Manual completo mostrado")
            return True
            
        except Exception as e:
            logger.error(f"Error mostrando manual: {str(e)}")
            return False
    
    def _handle_menu_navigation(self, number: str, chat_window) -> bool:
        """Maneja la navegación numérica del menú de ayuda"""
        try:
            # Mapeo de números a temas
            navigation_map = {
                "1": "archivos" if self.lang == "es" else "files",
                "2": "multimedia",
                "3": "volumen" if self.lang == "es" else "volume", 
                "4": "sistema" if self.lang == "es" else "system",
                "5": "windows",
                "6": "ia" if self.lang == "es" else "ai",
                "7": "citas" if self.lang == "es" else "appointments",
                "8": "busqueda" if self.lang == "es" else "search",
                "9": "dictado" if self.lang == "es" else "dictation",
                "10": "config"
            }
            
            topic = navigation_map.get(number)
            if topic:
                logger.info(f"📚 Navegación del menú: {number} → {topic}")
                return self._show_specific_help(topic, chat_window)
            else:
                error_msg = "Opción no válida" if self.lang == "es" else "Invalid option"
                chat_window.add_message(error_msg, is_user=False)
                return True
                
        except Exception as e:
            logger.error(f"Error en navegación del menú: {str(e)}")
            return False
    
    def _show_specific_help(self, topic: str, chat_window) -> bool:
        """Muestra ayuda específica para un tema"""
        try:
            topic_lower = topic.lower().strip()
            
            # Mapeo de temas a ayuda específica
            help_topics = {
                # Volumen
                "volumen": self._help_volume,
                "volume": self._help_volume,
                "audio": self._help_volume,
                
                # Multimedia
                "multimedia": self._help_multimedia,
                "musica": self._help_multimedia,
                "music": self._help_multimedia,
                "video": self._help_multimedia,
                
                # Archivos
                "archivos": self._help_files,
                "files": self._help_files,
                "carpeta": self._help_files,
                "folder": self._help_files,
                
                # Sistema
                "sistema": self._help_system,
                "system": self._help_system,
                "apagar": self._help_system,
                "shutdown": self._help_system,
                
                # Windows
                "windows": self._help_windows,
                "wifi": self._help_windows,
                "bluetooth": self._help_windows,
                "brillo": self._help_windows,
                "brightness": self._help_windows,
                
                # IA
                "ia": self._help_ai,
                "ai": self._help_ai,
                "eva": self._help_ai,
                "ollama": self._help_ai,
                
                # Citas (NUEVO)
                "citas": self._help_appointments,
                "appointments": self._help_appointments,
                "cita": self._help_appointments,
                "appointment": self._help_appointments,
                "calendario": self._help_appointments,
                "calendar": self._help_appointments,
                
                # Búsqueda (NUEVO)
                "busqueda": self._help_search,
                "search": self._help_search,
                "buscar": self._help_search,
                "google": self._help_search,
                
                # Dictado (NUEVO)
                "dictado": self._help_dictation,
                "dictation": self._help_dictation,
                "voz": self._help_dictation,
                "voice": self._help_dictation,
                
                # Configuración (NUEVO)
                "config": self._help_config,
                "configuracion": self._help_config,
                "configuration": self._help_config,
                "actualizaciones": self._help_config,
                "updates": self._help_config,
                
                # Wizard de configuración inicial
                "wizard": self._show_setup_wizard,
                "asistente": self._show_setup_wizard,
                "configuracion inicial": self._show_setup_wizard,
                "setup": self._show_setup_wizard,
                
                # Ejemplos (NUEVO)
                "ejemplos": self._help_examples,
                "examples": self._help_examples,
            }
            
            # Buscar tema
            if topic_lower in help_topics:
                return help_topics[topic_lower](chat_window)
            else:
                # Tema no encontrado
                if self.lang == "es":
                    msg = f"❓ No encontré ayuda específica para '{topic}'. Usa 'ayuda' para ver todos los temas disponibles."
                else:
                    msg = f"❓ No specific help found for '{topic}'. Use 'help' to see all available topics."
                
                chat_window.add_message(msg, is_user=False)
                return True
            
        except Exception as e:
            logger.error(f"Error en ayuda específica: {str(e)}")
            return False
    
    def _help_volume(self, chat_window) -> bool:
        """Ayuda específica para comandos de volumen"""
        if self.lang == "es":
            help_text = """
🔊 **Ayuda: Control de Volumen**
===============================

**Comandos de Volumen del Sistema:**
• 'sube volumen' - Aumenta volumen del sistema
• 'baja volumen' - Disminuye volumen del sistema  
• 'silencia' - Silencia/activa audio del sistema
• 'volumen [número]' - Establece volumen específico (0-100)

**Comandos de Volumen Multimedia:**
• 'sube volumen multimedia' - Solo para reproductores
• 'baja volumen multimedia' - Solo para reproductores
• 'silencia multimedia' - Solo para reproductores

**Ejemplos:**
• "volumen 50" - Establece volumen al 50%
• "volumen 0" - Silencia completamente
• "volumen 100" - Volumen máximo

💡 **Tip:** Los comandos de sistema afectan todo el audio, los multimedia solo a reproductores.
"""
        else:
            help_text = """
🔊 **Help: Volume Control**
==========================

**System Volume Commands:**
• 'volume up' - Increase system volume
• 'volume down' - Decrease system volume
• 'mute' - Mute/unmute system audio
• 'volume [number]' - Set specific volume (0-100)

**Multimedia Volume Commands:**
• 'volume up multimedia' - For players only
• 'volume down multimedia' - For players only
• 'mute multimedia' - For players only

**Examples:**
• "volume 50" - Set volume to 50%
• "volume 0" - Completely mute
• "volume 100" - Maximum volume

💡 **Tip:** System commands affect all audio, multimedia commands only affect players.
"""
        
        chat_window.add_message(help_text, is_user=False)
        return True
    
    def _help_multimedia(self, chat_window) -> bool:
        """Ayuda específica para comandos multimedia"""
        if self.lang == "es":
            help_text = """
🎵 **Ayuda: Control Multimedia**
===============================

**Comandos de Reproducción:**
• 'pausa' - Pausa/reanuda reproducción (toggle)
• 'reproduce' - Igual que pausa (toggle)
• 'para' - Detiene reproducción completamente
• 'siguiente' - Siguiente pista/video
• 'anterior' - Pista/video anterior
• 'pantalla completa' - Activa/desactiva pantalla completa

**Reproductores Compatibles:**
• VLC Media Player
• MPC-HC (Media Player Classic)
• Kodi
• Otros reproductores estándar

**Ejemplos de Uso:**
• Reproduciendo música → "pausa" → se pausa
• En pausa → "reproduce" → se reanuda
• Viendo video → "pantalla completa" → modo fullscreen

💡 **Tip:** Los comandos funcionan con el reproductor que esté activo en primer plano.
"""
        else:
            help_text = """
🎵 **Help: Multimedia Control**
==============================

**Playback Commands:**
• 'pause' - Pause/resume playback (toggle)
• 'play' - Same as pause (toggle)
• 'stop' - Stop playback completely
• 'next' - Next track/video
• 'previous' - Previous track/video
• 'fullscreen' - Toggle fullscreen mode

**Compatible Players:**
• VLC Media Player
• MPC-HC (Media Player Classic)
• Kodi
• Other standard players

**Usage Examples:**
• Playing music → "pause" → pauses
• Paused → "play" → resumes
• Watching video → "fullscreen" → fullscreen mode

💡 **Tip:** Commands work with the player that's active in the foreground.
"""
        
        chat_window.add_message(help_text, is_user=False)
        return True
    
    def _help_files(self, chat_window) -> bool:
        """Ayuda específica para comandos de archivos"""
        if self.lang == "es":
            help_text = """
📁 **Ayuda: Gestión de Archivos**
================================

**Comandos Disponibles:**
• 'lista archivos' - Muestra archivos de la carpeta activa
• 'ordena archivos' - Configura ordenamiento (nombre, creación, modificación)

**Ordenamiento:**
1. Por nombre (alfabético)
2. Por fecha de creación (más reciente primero)
3. Por fecha de modificación (más reciente primero)

**Funcionamiento:**
• EVA recuerda la última carpeta que abriste
• Los archivos se muestran numerados (1, 2, 3...)
• Puedes usar "abre archivo [número]" para abrir uno específico

**Ejemplos:**
• "lista archivos" → Muestra archivos numerados
• "ordena archivos" → Opciones 1, 2, 3
• "2" → Selecciona ordenamiento por fecha de creación

💡 **Tip:** La configuración de ordenamiento se guarda permanentemente.
"""
        else:
            help_text = """
📁 **Help: File Management**
===========================

**Available Commands:**
• 'list files' - Show files in active folder
• 'sort files' - Configure sorting (name, creation, modification)

**Sorting Options:**
1. By name (alphabetical)
2. By creation date (newest first)
3. By modification date (newest first)

**How it Works:**
• EVA remembers the last folder you opened
• Files are shown numbered (1, 2, 3...)
• You can use "open file [number]" to open a specific one

**Examples:**
• "list files" → Shows numbered files
• "sort files" → Options 1, 2, 3
• "2" → Selects sorting by creation date

💡 **Tip:** Sorting configuration is saved permanently.
"""
        
        chat_window.add_message(help_text, is_user=False)
        return True
    
    def _help_system(self, chat_window) -> bool:
        """Ayuda específica para comandos de sistema"""
        if self.lang == "es":
            help_text = """
🖥️ **Ayuda: Control del Sistema**
=================================

**Comandos Disponibles:**
• 'apaga' - Apagar el sistema
• 'reinicia' - Reiniciar el sistema
• 'cierra sesión' - Cerrar sesión del usuario

**Sistema de Confirmación:**
1. Dices el comando (ej: "apaga")
2. EVA pide confirmación
3. Respondes "sí" para confirmar o "no" para cancelar
4. EVA ejecuta la acción con 5 segundos de espera

**Respuestas de Confirmación:**
• ✅ Confirmar: "sí", "si", "yes", "y"
• ❌ Cancelar: "no", "n", "cancel", "cancelar"

**Seguridad:**
• Todos los comandos peligrosos requieren confirmación
• Tiempo de espera de 5 segundos antes de ejecutar
• Puedes cancelar en cualquier momento

💡 **Tip:** Los comandos son exactos: "apaga" funciona, "apagar" NO funciona.
"""
        else:
            help_text = """
🖥️ **Help: System Control**
===========================

**Available Commands:**
• 'shutdown' - Shutdown the system
• 'restart' - Restart the system
• 'logout' - Logout current user

**Confirmation System:**
1. Say the command (e.g., "shutdown")
2. EVA asks for confirmation
3. Reply "yes" to confirm or "no" to cancel
4. EVA executes with 5-second wait

**Confirmation Responses:**
• ✅ Confirm: "yes", "y", "sí", "si"
• ❌ Cancel: "no", "n", "cancel", "cancelar"

**Safety:**
• All dangerous commands require confirmation
• 5-second wait time before execution
• You can cancel at any time

💡 **Tip:** Commands are exact: "shutdown" works, "shut down" does NOT work.
"""
        
        chat_window.add_message(help_text, is_user=False)
        return True
    
    def _help_windows(self, chat_window) -> bool:
        """Ayuda específica para comandos de Windows"""
        if self.lang == "es":
            help_text = """
🪟 **Ayuda: Control de Windows**
===============================

**WiFi:**
• 'activa wifi' - Activa adaptador WiFi
• 'desactiva wifi' - Desactiva adaptador WiFi
• 'estado wifi' - Muestra estado y red conectada

**Bluetooth:**
• 'activa bluetooth' - Activa Bluetooth
• 'desactiva bluetooth' - Desactiva Bluetooth
• 'estado bluetooth' - Muestra estado del Bluetooth

**Brillo (Laptops):**
• 'sube brillo' - Aumenta brillo de pantalla
• 'baja brillo' - Disminuye brillo de pantalla
• 'brillo [número]' - Establece brillo específico (0-100)

**Funcionamiento:**
• Los comandos usan PowerShell y netsh
• Se ejecutan en segundo plano
• Requieren permisos de administrador para algunas funciones

**Ejemplos:**
• "brillo 70" - Establece brillo al 70%
• "estado wifi" - Muestra red WiFi actual

💡 **Tip:** Algunos comandos pueden tardar unos segundos en ejecutarse.
"""
        else:
            help_text = """
🪟 **Help: Windows Control**
============================

**WiFi:**
• 'enable wifi' - Enable WiFi adapter
• 'disable wifi' - Disable WiFi adapter
• 'wifi status' - Show status and connected network

**Bluetooth:**
• 'enable bluetooth' - Enable Bluetooth
• 'disable bluetooth' - Disable Bluetooth
• 'bluetooth status' - Show Bluetooth status

**Brightness (Laptops):**
• 'brightness up' - Increase screen brightness
• 'brightness down' - Decrease screen brightness
• 'brightness [number]' - Set specific brightness (0-100)

**How it Works:**
• Commands use PowerShell and netsh
• Executed in background
• Some functions require administrator permissions

**Examples:**
• "brightness 70" - Set brightness to 70%
• "wifi status" - Show current WiFi network

💡 **Tip:** Some commands may take a few seconds to execute.
"""
        
        chat_window.add_message(help_text, is_user=False)
        return True
    
    def _help_ai(self, chat_window) -> bool:
        """Ayuda específica para comandos de IA"""
        if self.lang == "es":
            help_text = """
🤖 **Ayuda: IA y Conversación**
==============================

**Comandos Disponibles:**
• 'eva [pregunta]' - Conversación con IA
• 'modelo' - Ver modelos disponibles y cambiar

**Funcionamiento:**
• EVA usa Ollama para IA local (100% offline)
• Los modelos se ejecutan en tu computadora
• No se envía información a internet

**Ejemplos de Uso:**
• "eva explícame qué es Python"
• "eva ayúdame con matemáticas"
• "eva resume este texto: [texto]"
• "modelo" → Ver opciones → "2" → Cambiar modelo

**Modelos Disponibles:**
• Modelo 1: Llama (general)
• Modelo 2: CodeLlama (programación)
• Modelo 3: Mistral (conversación)

**Requisitos:**
• Ollama instalado y funcionando
• Al menos 8GB de RAM recomendado
• Modelos descargados localmente

💡 **Tip:** Usa "eva" al inicio para activar la conversación con IA.
"""
        else:
            help_text = """
🤖 **Help: AI and Conversation**
===============================

**Available Commands:**
• 'eva [question]' - AI conversation
• 'model' - View available models and switch

**How it Works:**
• EVA uses Ollama for local AI (100% offline)
• Models run on your computer
• No information sent to internet

**Usage Examples:**
• "eva explain what Python is"
• "eva help me with math"
• "eva summarize this text: [text]"
• "model" → View options → "2" → Switch model

**Available Models:**
• Model 1: Llama (general)
• Model 2: CodeLlama (programming)
• Model 3: Mistral (conversation)

**Requirements:**
• Ollama installed and running
• At least 8GB RAM recommended
• Models downloaded locally

💡 **Tip:** Use "eva" at the beginning to activate AI conversation.
"""
        
        chat_window.add_message(help_text, is_user=False)
        return True
    
    def _help_appointments(self, chat_window) -> bool:
        """Ayuda específica para comandos de citas"""
        if self.lang == "es":
            help_text = """
📅 **Ayuda: Gestión de Citas**
=============================

**Crear Citas:**
• 'cita' - Proceso guiado paso a paso
• 'cita [tema] [fecha] [hora]' - Creación directa

**Consultar Citas:**
• 'citas' - Ver citas de hoy
• 'citas [fecha]' - Ver citas de fecha específica

**Cancelar Citas:**
• 'citas cancelar' - Ver opciones para cancelar
• 'citas cancelar [número]' - Cancelar por número
• 'citas cancelar [nombre]' - Cancelar por tema

**Formatos de Fecha:**
• 'hoy', 'mañana', 'viernes'
• '22/02' (día/mes)
• '22 de febrero'

**Formato de Hora:**
• '12:30', '09:15', '18:45' (formato 24h)

**Ejemplos:**
• "cita médico mañana 12:30"
• "citas cancelar médico"
• "citas viernes"

💡 **Tip:** El proceso guiado te ayuda paso a paso si solo dices 'cita'
"""
        else:
            help_text = """
📅 **Help: Appointment Management**
==================================

**Create Appointments:**
• 'appointment' - Step-by-step guided process
• 'appointment [topic] [date] [time]' - Direct creation

**Check Appointments:**
• 'appointments' - View today's appointments
• 'appointments [date]' - View appointments for specific date

**Cancel Appointments:**
• 'appointments cancel' - View cancellation options
• 'appointments cancel [number]' - Cancel by number
• 'appointments cancel [name]' - Cancel by topic

**Date Formats:**
• 'today', 'tomorrow', 'friday'
• '22/02' (day/month)
• 'february 22'

**Time Format:**
• '12:30', '09:15', '18:45' (24h format)

**Examples:**
• "appointment doctor tomorrow 12:30"
• "appointments cancel doctor"
• "appointments friday"

💡 **Tip:** The guided process helps you step by step if you just say 'appointment'
"""
        
        chat_window.add_message(help_text, is_user=False)
        return True
    
    def _help_search(self, chat_window) -> bool:
        """Ayuda específica para comandos de búsqueda"""
        if self.lang == "es":
            help_text = """
🔍 **Ayuda: Búsqueda y Web**
===========================

**Búsqueda en Google:**
• 'busca [término]' - Búsqueda directa en Google

**Ejemplos:**
• "busca python programming"
• "busca recetas de cocina"
• "busca noticias madrid"

**Sitios Web Personalizados:**
• 'abre [sitio]' - Abre sitios web configurados
• Configurable en Panel → Comandos Personalizados

**Funcionamiento:**
• Se abre automáticamente en tu navegador predeterminado
• Búsquedas se realizan en Google
• Puedes configurar sitios web favoritos

💡 **Tip:** Configura tus sitios web favoritos para acceso rápido
"""
        else:
            help_text = """
🔍 **Help: Search and Web**
==========================

**Google Search:**
• 'search [term]' - Direct Google search

**Examples:**
• "search python programming"
• "search cooking recipes"
• "search madrid news"

**Custom Websites:**
• 'open [site]' - Open configured websites
• Configurable in Panel → Custom Commands

**How it Works:**
• Automatically opens in your default browser
• Searches are performed on Google
• You can configure favorite websites

💡 **Tip:** Configure your favorite websites for quick access
"""
        
        chat_window.add_message(help_text, is_user=False)
        return True
    
    def _help_dictation(self, chat_window) -> bool:
        """Ayuda específica para comandos de dictado"""
        if self.lang == "es":
            help_text = """
🎤 **Ayuda: Sistema de Dictado**
===============================

**Iniciar Dictado:**
• 'dictado' - Inicia sistema de dictado inteligente

**Funcionamiento:**
• Convierte tu voz a texto en tiempo real
• Funciona con cualquier aplicación
• Reconocimiento inteligente de puntuación

**Finalizar Dictado:**
• "finalizar dictado" - Termina la sesión de dictado

**Características:**
• Reconocimiento de voz avanzado
• Corrección automática de gramática
• Soporte bilingüe (español/inglés)
• Funciona offline

**Ejemplos de Uso:**
• Escribir documentos
• Redactar emails
• Tomar notas rápidas
• Crear contenido

💡 **Tip:** Habla de forma clara y natural para mejores resultados
"""
        else:
            help_text = """
🎤 **Help: Dictation System**
============================

**Start Dictation:**
• 'dictation' - Start intelligent dictation system

**How it Works:**
• Converts your voice to text in real-time
• Works with any application
• Intelligent punctuation recognition

**End Dictation:**
• "finish dictation" - End dictation session

**Features:**
• Advanced voice recognition
• Automatic grammar correction
• Bilingual support (Spanish/English)
• Works offline

**Usage Examples:**
• Writing documents
• Composing emails
• Taking quick notes
• Creating content

💡 **Tip:** Speak clearly and naturally for best results
"""
        
        chat_window.add_message(help_text, is_user=False)
        return True
    
    def _help_config(self, chat_window) -> bool:
        """Ayuda específica para comandos de configuración"""
        if self.lang == "es":
            help_text = """
⚙️ **Ayuda: Configuración y Actualizaciones**
=============================================

**Actualizaciones:**
• 'verificar actualizaciones' - Busca nuevas versiones
• 'buscar actualizaciones' - Busca nuevas versiones
• 'comprobar actualizaciones' - Busca nuevas versiones

**Panel de Configuración:**
• Accesible desde la interfaz gráfica
• 'wizard' o 'setup' - Abre el asistente de configuración inicial
• 'configuracion inicial' - Abre el asistente de configuración
• Configurar comandos personalizados
• Ajustar voces y modelos de IA
• Gestionar licencias

**Comandos Personalizables:**
• Sitios web favoritos
• Programas frecuentes
• Carpetas de trabajo
• Atajos de teclado

**Configuración de IA:**
• Seleccionar modelos Ollama
• Ajustar configuración TTS
• Gestionar memoria y rendimiento

**Base de Conocimiento:**
• Personalizar comportamiento de EVA
• Configurar atajos personalizados
• Ajustar preferencias de usuario

💡 **Tip:** Explora el panel de configuración para personalizar EVA
"""
        else:
            help_text = """
⚙️ **Help: Configuration and Updates**
=====================================

**Updates:**
• 'check updates' - Check for new versions
• 'check for updates' - Check for new versions
• 'update eva' - Check for new versions

**Configuration Panel:**
• Accessible from graphical interface
• Configure custom commands
• Adjust voices and AI models
• Manage licenses

**Customizable Commands:**
• Favorite websites
• Frequent programs
• Working folders
• Keyboard shortcuts

**AI Configuration:**
• Select Ollama models
• Adjust TTS settings
• Manage memory and performance

**Knowledge Base:**
• Customize EVA behavior
• Configure custom shortcuts
• Adjust user preferences

💡 **Tip:** Explore the configuration panel to customize EVA
"""
        
        chat_window.add_message(help_text, is_user=False)
        return True
    
    def _help_examples(self, chat_window) -> bool:
        """Ayuda con ejemplos prácticos"""
        if self.lang == "es":
            help_text = """
💡 **Ejemplos Prácticos de EVA**
===============================

**🎯 CASOS DE USO COMUNES:**

**Trabajo con Archivos:**
• "lista archivos" → Ve archivos numerados
• "abre archivo 3" → Abre el tercer archivo
• "ordena archivos" → Configura ordenamiento

**Control del Sistema:**
• "volumen 50" → Volumen al 50%
• "apaga" → "sí" → Apaga el PC
• "activa wifi" → Activa WiFi

**IA y Productividad:**
• "eva explícame Python" → Conversación con IA
• "resume documento.pdf" → Resume un PDF
• "modelo" → "2" → Cambia modelo de IA

**Multimedia:**
• "pausa" → Pausa/reanuda música
• "siguiente" → Siguiente canción
• "pantalla completa" → Modo fullscreen

**Gestión de Citas:**
• "cita" → Proceso guiado
• "cita médico mañana 12:30" → Cita directa
• "citas" → Ver citas de hoy

**Búsqueda y Web:**
• "busca recetas pasta" → Búsqueda en Google
• "abre youtube" → Abre sitio configurado

**🔄 FLUJOS DE TRABAJO:**

**Sesión de Trabajo:**
1. "lista archivos" → Ver documentos
2. "abre archivo 1" → Abrir documento
3. "eva resume este texto: [contenido]" → Analizar
4. "cita reunión viernes 15:00" → Programar

**Control Multimedia:**
1. "abre vlc" → Abrir reproductor
2. "pausa" → Controlar reproducción
3. "volumen 70" → Ajustar audio
4. "pantalla completa" → Modo cine

💡 **Tip:** Combina comandos para flujos de trabajo eficientes
"""
        else:
            help_text = """
💡 **EVA Practical Examples**
============================

**🎯 COMMON USE CASES:**

**File Management:**
• "list files" → See numbered files
• "open file 3" → Open third file
• "sort files" → Configure sorting

**System Control:**
• "volume 50" → Set volume to 50%
• "shutdown" → "yes" → Shutdown PC
• "enable wifi" → Enable WiFi

**AI and Productivity:**
• "eva explain Python" → AI conversation
• "resume document.pdf" → Summarize PDF
• "model" → "2" → Change AI model

**Multimedia:**
• "pause" → Pause/resume music
• "next" → Next song
• "fullscreen" → Fullscreen mode

**Appointment Management:**
• "appointment" → Guided process
• "appointment doctor tomorrow 12:30" → Direct appointment
• "appointments" → View today's appointments

**Search and Web:**
• "search pasta recipes" → Google search
• "open youtube" → Open configured site

**🔄 WORKFLOWS:**

**Work Session:**
1. "list files" → View documents
2. "open file 1" → Open document
3. "eva summarize this text: [content]" → Analyze
4. "appointment meeting friday 15:00" → Schedule

**Multimedia Control:**
1. "open vlc" → Open player
2. "pause" → Control playback
3. "volume 70" → Adjust audio
4. "fullscreen" → Cinema mode

💡 **Tip:** Combine commands for efficient workflows
"""
        
        chat_window.add_message(help_text, is_user=False)
        return True

    def _show_setup_wizard(self, chat_window) -> bool:
        """Muestra el wizard de configuración inicial"""
        try:
            # Verificar si tenemos acceso a la instancia EVA
            if hasattr(self, 'eva') and self.eva:
                # Llamar al método del wizard en la instancia principal
                self.eva.show_setup_wizard_manually()
                return True
            elif hasattr(self, 'processor') and hasattr(self.processor, 'eva') and self.processor.eva:
                # Alternativa: acceder a través del procesador
                self.processor.eva.show_setup_wizard_manually()
                return True
            else:
                # Fallback: mostrar mensaje informativo
                wizard_info = self.language_manager.get_text(
                    "help.wizard_info",
                    """🧙‍♂️ **ASISTENTE DE CONFIGURACIÓN INICIAL**

El wizard de configuración te permite:

• **Hardware:** Configurar CPU o GPU
• **Modelo de IA:** Seleccionar el modelo de lenguaje
• **Voz:** Elegir la voz del asistente
• **Idioma:** Configurar el idioma de la interfaz

💡 **Para acceder al wizard:**
1. Ve al menú de configuración
2. Busca "Configuración inicial" o "Setup"
3. O reinicia EVA para que aparezca automáticamente

🔧 **Comandos alternativos:**
• "abrir configuración" - Panel completo de configuración
• "configurar voz" - Solo configuración de voz"""
                )
                
                chat_window.add_message(wizard_info, is_user=False)
                return True
                
        except Exception as e:
            logger.error(f"Error mostrando wizard de configuración: {str(e)}")
            error_msg = self.language_manager.get_text(
                "errors.wizard_error",
                "❌ Error abriendo el asistente de configuración. Intenta con 'abrir configuración' para acceder al panel completo."
            )
            chat_window.add_message(error_msg, is_user=False)
            return False