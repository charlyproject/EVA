# EVA — Recursos Externos (requirements_extra.md)

Este documento describe los binarios y modelos que **no están incluidos** en el repositorio por su tamaño y/o licencias propias. Puedes descargarlos automáticamente con `download_models.bat` o manualmente siguiendo esta guía.

---

## ¿Por qué no están en el repositorio?

| Razón | Detalle |
|-------|---------|
| **Tamaño** | Los modelos superan los límites recomendados para Git (~100 MB por archivo) |
| **Licencias propias** | Vosk (Apache 2.0), Piper (MIT), FFmpeg (LGPL/GPL) tienen distribución independiente |
| **Actualizaciones independientes** | Piper y Vosk se actualizan con frecuencia; desacoplaros facilita el mantenimiento |

---

## 1. Vosk — Reconocimiento de voz offline

**Licencia:** Apache 2.0  
**Página oficial:** https://alphacephei.com/vosk/models

EVA usa los modelos "small" (ligeros, buenos para uso en tiempo real):

| Modelo | Idioma | Tamaño | URL de descarga |
|--------|--------|--------|-----------------|
| `vosk-model-small-es-0.42` | Español | ~40 MB | https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip |
| `vosk-model-small-en-us-0.15` | Inglés (US) | ~40 MB | https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip |

**Destino tras descomprimir:**
```
EVA/
└── models/
    └── vosk/
        ├── vosk-model-small-es-0.42/
        └── vosk-model-small-en-us-0.15/
```

**Nota:** Si quieres mayor precisión (a costa de más RAM y CPU), puedes sustituir por modelos grandes (`vosk-model-es-*`), pero el reconocimiento será más lento.

---

## 2. Piper TTS — Síntesis de voz neural

**Licencia:** MIT  
**GitHub:** https://github.com/rhasspy/piper

### 2a. Binario Piper (motor)

| Plataforma | URL |
|-----------|-----|
| Windows x64 | https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip |

Descomprime de forma que `piper.exe` quede en `EVA/piper/piper.exe`.

**Estructura esperada:**
```
EVA/
└── piper/
    ├── piper.exe
    ├── onnxruntime.dll
    ├── espeak-ng.dll
    ├── espeak-ng-data/
    └── models/
```

### 2b. Voces / modelos de voz

Las voces se descargan desde HuggingFace. EVA usa por defecto:

| Voz | Idioma | Calidad | Tamaño | ONNX URL | Config JSON URL |
|-----|--------|---------|--------|----------|-----------------|
| `es_MX-claude-high` | Español MX | High | ~60 MB | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_MX/claude/high/es_MX-claude-high.onnx) | [.json](https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_MX/claude/high/es_MX-claude-high.onnx.json) |
| `en_US-kristin-medium` | Inglés US | Medium | ~60 MB | [.onnx](https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/kristin/medium/en_US-kristin-medium.onnx) | [.json](https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/kristin/medium/en_US-kristin-medium.onnx.json) |

Cada voz necesita **dos archivos**: el `.onnx` (modelo) y el `.onnx.json` (configuración).

**Destino:**
```
EVA/
└── piper/
    └── models/
        ├── es_MX-claude-high.onnx
        ├── es_MX-claude-high.onnx.json
        ├── en_US-kristin-medium.onnx
        └── en_US-kristin-medium.onnx.json
```

**¿Quieres otra voz?** Busca en https://huggingface.co/rhasspy/piper-voices y descarga los dos archivos correspondientes. Puedes configurar la voz activa desde Configuración → Voz en EVA.

---

## 3. FFmpeg — Procesamiento de audio

**Licencia:** LGPL v2.1+ (build estática GPL también disponible)  
**Web oficial:** https://ffmpeg.org/download.html

EVA usa FFmpeg para la reproducción y conversión de audio.

| Build recomendado | URL |
|-------------------|-----|
| BtbN Windows x64 (GPL, última versión) | https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip |
| gyan.dev (builds estables) | https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip |

**Destino:**
```
EVA/
└── ffmpeg/
    └── bin/
        ├── ffmpeg.exe
        ├── ffprobe.exe
        └── ffplay.exe   (opcional)
```

Solo `ffmpeg.exe` y `ffprobe.exe` son necesarios.

---

## 4. Ollama — Inferencia de IA local

**Licencia:** MIT  
**Web:** https://ollama.com

Ollama **no** forma parte del proyecto EVA; es un servicio independiente que debes instalar en el sistema.

```bash
# 1. Instala Ollama desde https://ollama.com

# 2. Descarga un modelo (ejemplos):
ollama pull qwen3:4b        # Buena relación calidad/velocidad (~2.5 GB)
ollama pull phi3:mini        # Más ligero (~1.8 GB)
ollama pull mistral:7b-instruct-q4_0  # Mayor capacidad (~4 GB)

# 3. Verifica que está corriendo:
ollama list
```

EVA detecta automáticamente todos los modelos disponibles al arrancar.

---

## 5. Resumen de tamaños totales

| Componente | Tamaño aproximado |
|-----------|-------------------|
| Vosk ES | ~40 MB |
| Vosk EN | ~40 MB |
| Piper binario | ~20 MB |
| Voz ES (claude-high) | ~60 MB |
| Voz EN (kristin-medium) | ~60 MB |
| FFmpeg | ~75 MB |
| **Total descarga** | **~295 MB** |
| Ollama + modelo IA | 2–5 GB (dependiendo del modelo) |

---

## 6. Verificar instalación

Tras descargar todo, ejecuta EVA y comprueba:

```bash
python main.py
```

Si hay recursos faltantes, EVA lo indicará en el log de inicio. También puedes revisar `logs/eva_debug.log`.
