# EVA — Enhanced Voice Assistant

![License](https://img.shields.io/badge/license-MIT-blue.svg) ![Python](https://img.shields.io/badge/python-3.11+-blue.svg) ![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg) ![Status](https://img.shields.io/badge/status-active-brightgreen.svg) ![Offline](https://img.shields.io/badge/core-100%25%20offline-success.svg)

[![Donar en Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/charlyproject)

> **Asistente de voz local para Windows** — reconocimiento de voz offline (Vosk), síntesis de voz natural (Piper TTS) e IA local (Ollama), todo desde una interfaz de chat moderna construida con PySide6.

📖 [English version → README_EN.md](README_EN.md)

---

## ✨ Características principales

| Módulo | Tecnología | Descripción |
| - | - | - |
| 🗣️ Reconocimiento de voz | Vosk + VAD | 100 % offline, español e inglés |
| 🔊 Síntesis de voz | Piper TTS | Voces neurales optimizadas para CPU |
| 🤖 IA conversacional | Ollama | Modelos locales, sin API externa |
| 🌍 Bilingüe | — | Interfaz y comandos ES / EN |
| 📁 Gestión de archivos | — | Detección de carpeta activa, apertura, listado |
| 🎮 Control del sistema | — | Volumen, brillo, energía, WiFi, Bluetooth |
| 🎵 Control multimedia | — | VLC, MPC-HC, Kodi |
| 📅 Citas | — | Creación conversacional guiada |
| 🌐 Búsqueda web | DuckDuckGo / Tavily / Google | **Opcional** — requiere internet y/o API key |
| 🎤 Dictado por voz | Vosk | Conversión voz → texto en tiempo real |

> **Nota sobre el modo offline:** el núcleo de EVA (voz, IA, comandos de sistema, citas, archivos) funciona **sin conexión a internet**. Las búsquedas web (comandos `busca`, `web`, `ddg`, `internet`) son opcionales y usan DuckDuckGo (sin clave), Tavily (requiere API key gratuita) o Google. OpenRouter es también opcional para acceder a modelos en la nube.

---

## 📋 Requisitos del sistema

- **Windows 10 / 11** (64-bit)
- **Python 3.11+**
- **Ollama** instalado y ejecutándose → [https://ollama.com](https://ollama.com)
- **Micrófono** funcional
- **4 GB RAM** mínimo (8 GB recomendado)
- GPU NVIDIA — opcional (Ollama la detecta automáticamente)

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone [https://github.com/charlyproject/EVA.git](https://github.com/charlyproject/EVA.git)
cd EVA
2. Crear entorno virtual e instalar dependenciasBashpython -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
Nota: PyAudio puede requerir tener instalado el Visual C++ Redistributable.3. Descargar modelos y binarios externosLos binarios de Vosk, Piper y FFmpeg no están incluidos en el repositorio por su tamaño y licencias propias. Descárgalos de forma automática ejecutando:DOSdownload_models.bat
O de forma manual siguiendo las instrucciones en requirements_extra.md.4. Instalar Ollama y descargar un modelo de IABash# Descargar Ollama desde [https://ollama.com](https://ollama.com) e instalarlo, luego:
ollama pull qwen3:4b
EVA detecta automáticamente todos los modelos disponibles en Ollama al arrancar.5. EjecutarBashpython main.py
En la primera ejecución aparece un asistente de configuración para seleccionar idioma, hardware y modelo de IA.🎯 ComandosTodos los comandos funcionan por voz y por texto. Son bilingües (ES / EN).IA y conversaciónESENDescripcióneva [pregunta]eva [question]Conversar con la IA localmodelomodelVer y cambiar modelo Ollama1, 2, 3...1, 2, 3...Seleccionar modelo por númeroSistemaESENDescripciónsube volumenvolume upSubir volumen del sistemabaja volumenvolume downBajar volumensilenciamuteSilenciar / activarvolumen [0-100]volume [0-100]Volumen específicoapagashutdownApagar PC (pide confirmación)reiniciarestartReiniciar (pide confirmación)captura pantallascreenshotCaptura de pantallasalirexitCerrar EVAArchivosESENDescripciónlista archivoslist filesListar carpeta activaabre [nombre]open [name]Abrir programa, carpeta, web o archivoabre archivo [N]open file [N]Abrir archivo por númeroMultimedia (VLC, MPC-HC, Kodi)ESENDescripciónpausapausePausar / reanudarsiguientenextSiguiente pistaanteriorpreviousAnteriorpantalla completafullscreenToggle pantalla completaWindowsESENDescripciónactiva wifienable wifiActivar WiFidesactiva wifidisable wifiDesactivar WiFiactiva bluetoothenable bluetoothActivar Bluetoothsube brillobrightness upSubir brillobrillo [0-100]brightness [0-100]Brillo específicoBúsqueda web (opcional, requiere internet)ESENDescripciónbusca [término]search [term]Googleddg [término]ddg [term]DuckDuckGo (sin clave)web [término]web [term]Tavily (requiere API key)internet [término]internet [term]Tavily con fallback a DDGCitasESENDescripcióncitaappointmentCrear cita (proceso guiado)citasappointmentsVer citas de hoycitas [fecha]appointments [date]Ver citas por fechaDictado y ayudaESENDescripcióndictadodictationIniciar dictado por vozayudahelpMenú de ayuda interactivocomandoscommandsLista completa de comandoswizardsetupAbrir asistente de configuración🏗️ Arquitectura del proyectoEVA/
├── main.py                          # Punto de entrada principal
├── __version__.py                   # Versión de la aplicación
├── requirements.txt                 # Dependencias Python
├── styles.qss                       # Estilos Qt (tema visual)
├── download_models.bat              # Descarga binarios/modelos externos
├── requirements_extra.md            # Guía de recursos externos
│
├── config/                          # Configuración
│   ├── paths.example.json           # Plantilla de configuración (copiar a paths.json)
│   ├── lang_es.json                 # Textos en español
│   ├── lang_en.json                 # Textos en inglés
│   └── eva_knowledge_base.json      # Base de conocimiento
│
├── core/                            # Núcleo del sistema
├── commands/                        # Procesamiento de comandos
├── voice/                           # Sistema de voz (Vosk + Piper)
├── ui/                              # Interfaz de usuario (PySide6)
├── utils/                           # Utilidades
├── help_system/                     # Sistema de ayuda integrado
├── hooks/                           # Hooks PyInstaller
├── resources/                       # Iconos y recursos visuales
├── tests/                           # Tests
│
│   ── Descarga separada (download_models.bat) ──
├── piper/                           # Piper TTS (binario + modelos)
├── ffmpeg/                          # FFmpeg (binarios)
└── models/vosk/                     # Modelos de reconocimiento de voz
⚙️ ConfiguraciónEl panel de configuración es accesible desde el botón ⚙️ en la ventana principal:Apariencia: Tema oscuro/claro, fuente, tamañoVoz: Sensibilidad del micrófono, VAD, idiomaIA: Modelo Ollama, temperaturaIdioma: Español / Inglés (cambio en tiempo real)Comandos personalizados: Programas, carpetas, sitios webEjemplo de config/paths.json:JSON{
  "paths": {
    "programs": { "chrome": "C:\\Program Files\\Google\\Chrome\\chrome.exe" },
    "folders":  { "documentos": "C:\\Users\\Usuario\\Documents" },
    "websites": { "youtube": "[https://youtube.com](https://youtube.com)" }
  }
}
🐛 Solución de problemasEl reconocimiento de voz no funcionaVerifica que el micrófono funciona en Windows.Comprueba que los modelos Vosk existen en models/vosk/ (ejecuta download_models.bat).Ajusta la sensibilidad en Configuración → Voz.Piper TTS no hablaVerifica que piper/piper.exe existe.Verifica que los modelos existen en piper/models/ (ejecuta download_models.bat).Comprueba que el audio no está silenciado en EVA (botón 🔇).Ollama no respondeollama --version — verifica instalación.ollama list — verifica que hay algún modelo.Si no hay modelo: ollama pull qwen3:4b.Reinicia EVA.🔨 Compilar el ejecutable (.exe)DOS# Build rápido (para pruebas)
build_quick.bat

# Build con instalador completo
build_installer.bat
🤝 ContribuirHaz fork del repositorio.Crea una rama: git checkout -b feature/mi-mejora.Haz commit: git commit -m "feat: descripción".Abre un Pull Request.📸 Captura de pantallaPróximamente — haz una captura con Win+Shift+S y guárdala en docs/screenshot.png.☕ Apoyar el proyectoSi EVA te resulta útil, puedes invitarme a un café:📄 LicenciaMIT © 2025 cHArLy — ver LICENSE.txtLos componentes de terceros (Vosk, Piper, FFmpeg) tienen sus propias licencias. Ver LICENSE.txt y requirements_extra.md para más detalles.