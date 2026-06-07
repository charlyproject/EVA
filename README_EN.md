# EVA — Enhanced Voice Assistant

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)
![Offline](https://img.shields.io/badge/core-100%25%20offline-success.svg)

[![Support on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/charlyproject)

> **Local voice assistant for Windows** — offline speech recognition (Vosk), natural text-to-speech (Piper TTS), and local AI (Ollama), all from a modern chat interface built with PySide6.

📖 [Versión en español → README.md](README.md)

---

## ✨ Key Features

| Module | Technology | Description |
|--------|-----------|-------------|
| 🗣️ Speech recognition | Vosk + VAD | 100% offline, Spanish & English |
| 🔊 Text-to-speech | Piper TTS | Neural voices optimised for CPU |
| 🤖 AI chat | Ollama | Local models, no external API required |
| 🌍 Bilingual | — | UI and commands in ES / EN |
| 📁 File management | — | Active folder detection, open, list |
| 🎮 System control | — | Volume, brightness, power, WiFi, Bluetooth |
| 🎵 Media control | — | VLC, MPC-HC, Kodi |
| 📅 Appointments | — | Guided conversational creation |
| 🌐 Web search | DuckDuckGo / Tavily / Google | **Optional** — requires internet and/or API key |
| 🎤 Voice dictation | Vosk | Real-time voice → text |

> **Offline note:** EVA's core (voice, AI, system commands, appointments, files) works **without an internet connection**. Web search commands (`search`, `web`, `ddg`, `internet`) are optional and use DuckDuckGo (no key required), Tavily (free API key), or Google. OpenRouter is also optional for cloud model access.

---

## 📋 System Requirements

- **Windows 10 / 11** (64-bit)
- **Python 3.11+**
- **Ollama** installed and running → https://ollama.com
- Functional **microphone**
- **4 GB RAM** minimum (8 GB recommended)
- NVIDIA GPU — optional (Ollama auto-detects)

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/charlyproject/EVA.git
cd EVA
```

### 2. Create virtual environment and install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> **Note:** PyAudio may require the [Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe).

### 3. Download external binaries and models

Vosk, Piper and FFmpeg binaries are **not included** in the repository due to their size and individual licences. Download them automatically:

```bat
download_models.bat
```

Or manually, following the instructions in [`requirements_extra.md`](requirements_extra.md).

### 4. Install Ollama and pull an AI model

```bash
# Download Ollama from https://ollama.com, install it, then:
ollama pull qwen3:4b
```

EVA auto-detects all models available in Ollama at startup.

### 5. Run

```bash
python main.py
```

On first launch, a setup wizard will appear to select language, hardware, and AI model.

---

## 🎯 Commands

All commands work **by voice and by text**. They are bilingual (ES / EN).

### AI & conversation

| EN | ES | Description |
|---|---|---|
| `eva [question]` | `eva [pregunta]` | Chat with local AI |
| `model` | `modelo` | View and switch Ollama model |
| `1`, `2`, `3`... | `1`, `2`, `3`... | Select model by number |

### System

| EN | ES | Description |
|---|---|---|
| `volume up` | `sube volumen` | Increase system volume |
| `volume down` | `baja volumen` | Decrease volume |
| `mute` | `silencia` | Toggle mute |
| `volume [0-100]` | `volumen [0-100]` | Set specific volume |
| `shutdown` | `apaga` | Shut down PC (asks confirmation) |
| `restart` | `reinicia` | Restart (asks confirmation) |
| `screenshot` | `captura pantalla` | Take a screenshot |
| `exit` | `salir` | Close EVA |

### Files

| EN | ES | Description |
|---|---|---|
| `list files` | `lista archivos` | List active folder |
| `open [name]` | `abre [nombre]` | Open app, folder, website, or file |
| `open file [N]` | `abre archivo [N]` | Open file by list number |

### Media (VLC, MPC-HC, Kodi)

| EN | ES | Description |
|---|---|---|
| `pause` | `pausa` | Pause / resume |
| `next` | `siguiente` | Next track |
| `previous` | `anterior` | Previous track |
| `fullscreen` | `pantalla completa` | Toggle fullscreen |

### Windows

| EN | ES | Description |
|---|---|---|
| `enable wifi` | `activa wifi` | Enable WiFi |
| `disable wifi` | `desactiva wifi` | Disable WiFi |
| `enable bluetooth` | `activa bluetooth` | Enable Bluetooth |
| `brightness up` | `sube brillo` | Increase brightness |
| `brightness [0-100]` | `brillo [0-100]` | Set specific brightness |

### Web search (optional, requires internet)

| EN | ES | Description |
|---|---|---|
| `search [term]` | `busca [término]` | Google search |
| `ddg [term]` | `ddg [término]` | DuckDuckGo (no key required) |
| `web [term]` | `web [término]` | Tavily (requires API key) |
| `internet [term]` | `internet [término]` | Tavily with DDG fallback |

### Appointments

| EN | ES | Description |
|---|---|---|
| `appointment` | `cita` | Create appointment (guided) |
| `appointments` | `citas` | View today's appointments |
| `appointments [date]` | `citas [fecha]` | View by date |

### Dictation & help

| EN | ES | Description |
|---|---|---|
| `dictation` | `dictado` | Start voice dictation |
| `help` | `ayuda` | Interactive help menu |
| `commands` | `comandos` | Full command list |
| `setup` | `wizard` | Open setup wizard |

---

## 🏗️ Project Architecture

```
EVA/
├── main.py                    # Application entry point
├── __version__.py             # Version info
├── requirements.txt           # Python dependencies
├── styles.qss                 # Qt stylesheet
├── download_models.bat        # Downloads external binaries/models
├── requirements_extra.md      # External resources guide
│
├── config/                    # Configuration
│   ├── paths.json             # Custom paths (programs, websites)
│   ├── lang_es.json           # Spanish strings
│   ├── lang_en.json           # English strings
│   └── eva_knowledge_base.json
│
├── core/                      # System core
├── commands/                  # Command processing
├── voice/                     # Voice subsystem (Vosk + Piper)
├── ui/                        # PySide6 interface
├── utils/                     # Utilities
├── help_system/               # Built-in help system
├── hooks/                     # PyInstaller hooks
├── resources/                 # Icons and assets
├── tests/                     # Tests
├── screenshots/               # Screenshots
│
│   ── Downloaded separately (download_models.bat) ──
├── piper/                     # Piper TTS binary + voice models
├── ffmpeg/                    # FFmpeg binaries
└── models/vosk/               # Vosk speech models
```

---

## ⚙️ Configuration

The settings panel is accessible via the ⚙️ button in the main window:

- **Appearance:** Dark/light theme, font, size
- **Voice:** Microphone sensitivity, VAD, language
- **AI:** Ollama model, temperature
- **Language:** Spanish / English (live switch)
- **Custom commands:** Programs, folders, websites

Example `config/paths.json`:

```json
{
  "paths": {
    "programs": { "chrome": "C:\\Program Files\\Google\\Chrome\\chrome.exe" },
    "folders":  { "documents": "C:\\Users\\User\\Documents" },
    "websites": { "youtube": "https://youtube.com" }
  }
}
```

---

## 🐛 Troubleshooting

**Speech recognition not working**
1. Verify your microphone works in Windows.
2. Check that Vosk models exist in `models/vosk/` (run `download_models.bat`).
3. Adjust sensitivity in Settings → Voice.

**Piper TTS not speaking**
1. Verify `piper/piper.exe` exists.
2. Verify voice models exist in `piper/models/` (run `download_models.bat`).
3. Check EVA is not muted (🔇 button).

**Ollama not responding**
1. `ollama --version` — verify installation.
2. `ollama list` — verify a model is downloaded.
3. Pull a model: `ollama pull qwen3:4b`.
4. Restart EVA.

---

## 🔨 Build Executable (.exe)

```bat
:: Quick build (for testing)
build_quick.bat

:: Full installer build
build_installer.bat
```

---

## 🤝 Contributing

1. Fork the repository.
2. Create a branch: `git checkout -b feature/my-improvement`.
3. Commit: `git commit -m "feat: description"`.
4. Open a Pull Request.

---

## 📸 Screenshot

![EVA screenshot](screenshots/EVA.Chat.png)

---

## ☕ Support the project

If EVA is useful to you, you can buy me a coffee:

[![Support on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/charlyproject)

---

## 📄 License

MIT © 2025 cHArLy — see [LICENSE.txt](LICENSE.txt)

Third-party components (Vosk, Piper, FFmpeg) carry their own licences.
See [LICENSE.txt](LICENSE.txt) and [requirements_extra.md](requirements_extra.md) for details.
