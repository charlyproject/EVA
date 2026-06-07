@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

:: ============================================================
::  EVA — Enhanced Voice Assistant
::  download_models.bat
::
::  Descarga automática de binarios y modelos externos:
::    - Vosk  (modelos de reconocimiento de voz)
::    - Piper (motor TTS + voces neuronales)
::    - FFmpeg (procesamiento de audio)
::
::  Uso: Ejecutar desde la raíz del proyecto EVA
::       (doble clic o: cd EVA && download_models.bat)
:: ============================================================

echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║        EVA — Descarga de modelos y binarios          ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: ── Verificar que PowerShell esté disponible ──────────────
where powershell >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PowerShell no está disponible. Instálalo o descarga manualmente.
    echo         Ver: requirements_extra.md
    pause
    exit /b 1
)

:: ── Verificar directorio de trabajo ───────────────────────
if not exist "main.py" (
    echo [ERROR] Ejecuta este script desde la raíz del proyecto EVA.
    echo         Ejemplo:  cd "C:\ruta\al\proyecto\EVA"
    echo                   download_models.bat
    pause
    exit /b 1
)

echo  Directorio de destino: %CD%
echo.

:: ============================================================
::  FUNCIÓN DE DESCARGA CON PROGRESO
::  Usa Invoke-WebRequest de PowerShell (nativo en Win10/11)
:: ============================================================

:: ── 1. VOSK — Modelos de reconocimiento de voz ────────────
echo  [1/3] VOSK — Modelos de voz offline
echo  ─────────────────────────────────────────────────────

if not exist "models\vosk" mkdir "models\vosk"

:: Modelo español (es) — vosk-model-small-es-0.42 (~40 MB)
set VOSK_ES_URL=https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip
set VOSK_ES_ZIP=models\vosk\vosk-model-small-es-0.42.zip
set VOSK_ES_DIR=models\vosk\vosk-model-small-es-0.42

if exist "%VOSK_ES_DIR%" (
    echo  [OK] Modelo español ya existe: %VOSK_ES_DIR%
) else (
    echo  Descargando modelo español (~40 MB)...
    echo  Fuente: %VOSK_ES_URL%
    powershell -NoProfile -Command ^
        "Invoke-WebRequest -Uri '%VOSK_ES_URL%' -OutFile '%VOSK_ES_ZIP%' -UseBasicParsing"
    if errorlevel 1 (
        echo  [ERROR] Fallo al descargar el modelo español.
        goto vosk_en
    )
    echo  Extrayendo modelo español...
    powershell -NoProfile -Command ^
        "Expand-Archive -Path '%VOSK_ES_ZIP%' -DestinationPath 'models\vosk' -Force"
    del /q "%VOSK_ES_ZIP%" 2>nul
    echo  [OK] Modelo español instalado.
)

:vosk_en
:: Modelo inglés (en-US) — vosk-model-small-en-us-0.15 (~40 MB)
set VOSK_EN_URL=https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
set VOSK_EN_ZIP=models\vosk\vosk-model-small-en-us-0.15.zip
set VOSK_EN_DIR=models\vosk\vosk-model-small-en-us-0.15

if exist "%VOSK_EN_DIR%" (
    echo  [OK] Modelo inglés ya existe: %VOSK_EN_DIR%
) else (
    echo  Descargando modelo inglés (~40 MB)...
    echo  Fuente: %VOSK_EN_URL%
    powershell -NoProfile -Command ^
        "Invoke-WebRequest -Uri '%VOSK_EN_URL%' -OutFile '%VOSK_EN_ZIP%' -UseBasicParsing"
    if errorlevel 1 (
        echo  [ERROR] Fallo al descargar el modelo inglés.
        goto piper_section
    )
    echo  Extrayendo modelo inglés...
    powershell -NoProfile -Command ^
        "Expand-Archive -Path '%VOSK_EN_ZIP%' -DestinationPath 'models\vosk' -Force"
    del /q "%VOSK_EN_ZIP%" 2>nul
    echo  [OK] Modelo inglés instalado.
)

:: ── 2. PIPER TTS — Motor y voces neuronales ───────────────
:piper_section
echo.
echo  [2/3] PIPER TTS — Motor de síntesis de voz
echo  ─────────────────────────────────────────────────────

if not exist "piper" mkdir "piper"
if not exist "piper\models" mkdir "piper\models"

:: Piper binario para Windows (x64) — ~5 MB
set PIPER_URL=https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip
set PIPER_ZIP=piper\piper_windows_amd64.zip

if exist "piper\piper.exe" (
    echo  [OK] Piper.exe ya existe.
) else (
    echo  Descargando Piper TTS para Windows (~5 MB)...
    echo  Fuente: %PIPER_URL%
    powershell -NoProfile -Command ^
        "Invoke-WebRequest -Uri '%PIPER_URL%' -OutFile '%PIPER_ZIP%' -UseBasicParsing"
    if errorlevel 1 (
        echo  [ERROR] Fallo al descargar Piper.
        goto piper_voices
    )
    echo  Extrayendo Piper...
    powershell -NoProfile -Command ^
        "Expand-Archive -Path '%PIPER_ZIP%' -DestinationPath 'piper' -Force"
    :: El zip de Piper extrae en subcarpeta 'piper/' — mover contenido un nivel arriba
    if exist "piper\piper\piper.exe" (
        powershell -NoProfile -Command ^
            "Move-Item 'piper\piper\*' 'piper\' -Force"
        rmdir "piper\piper" 2>nul
    )
    del /q "%PIPER_ZIP%" 2>nul
    echo  [OK] Piper instalado.
)

:piper_voices
:: Voz español MX — es_MX-claude-high (~60 MB)
set VOICE_ES_BASE=https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/es/es_MX/claude/high
set VOICE_ES_ONNX=piper\models\es_MX-claude-high.onnx
set VOICE_ES_JSON=piper\models\es_MX-claude-high.onnx.json

if exist "%VOICE_ES_ONNX%" (
    echo  [OK] Voz español (es_MX-claude-high) ya existe.
) else (
    echo  Descargando voz español es_MX-claude-high (~60 MB)...
    powershell -NoProfile -Command ^
        "Invoke-WebRequest -Uri '%VOICE_ES_BASE%/es_MX-claude-high.onnx' -OutFile '%VOICE_ES_ONNX%' -UseBasicParsing"
    powershell -NoProfile -Command ^
        "Invoke-WebRequest -Uri '%VOICE_ES_BASE%/es_MX-claude-high.onnx.json' -OutFile '%VOICE_ES_JSON%' -UseBasicParsing"
    echo  [OK] Voz español instalada.
)

:: Voz inglés US — en_US-kristin-medium (~60 MB)
set VOICE_EN_BASE=https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/kristin/medium
set VOICE_EN_ONNX=piper\models\en_US-kristin-medium.onnx
set VOICE_EN_JSON=piper\models\en_US-kristin-medium.onnx.json

if exist "%VOICE_EN_ONNX%" (
    echo  [OK] Voz inglés (en_US-kristin-medium) ya existe.
) else (
    echo  Descargando voz inglés en_US-kristin-medium (~60 MB)...
    powershell -NoProfile -Command ^
        "Invoke-WebRequest -Uri '%VOICE_EN_BASE%/en_US-kristin-medium.onnx' -OutFile '%VOICE_EN_ONNX%' -UseBasicParsing"
    powershell -NoProfile -Command ^
        "Invoke-WebRequest -Uri '%VOICE_EN_BASE%/en_US-kristin-medium.onnx.json' -OutFile '%VOICE_EN_JSON%' -UseBasicParsing"
    echo  [OK] Voz inglés instalada.
)

:: ── 3. FFMPEG — Procesamiento de audio ───────────────────
echo.
echo  [3/3] FFMPEG — Procesamiento de audio
echo  ─────────────────────────────────────────────────────

if exist "ffmpeg\bin\ffmpeg.exe" (
    echo  [OK] FFmpeg ya existe.
    goto done
)

if not exist "ffmpeg" mkdir "ffmpeg"

:: FFmpeg builds (BtbN) — GPL build para Windows x64 (~75 MB ZIP)
set FFMPEG_URL=https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip
set FFMPEG_ZIP=ffmpeg\ffmpeg-master-latest-win64-gpl.zip

echo  Descargando FFmpeg para Windows (~75 MB)...
echo  Fuente: %FFMPEG_URL%
powershell -NoProfile -Command ^
    "Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile '%FFMPEG_ZIP%' -UseBasicParsing"
if errorlevel 1 (
    echo  [ERROR] Fallo al descargar FFmpeg.
    echo          Descárgalo manualmente desde: https://ffmpeg.org/download.html
    echo          Extrae los binarios en: ffmpeg\bin\
    goto done
)
echo  Extrayendo FFmpeg...
powershell -NoProfile -Command ^
    "Expand-Archive -Path '%FFMPEG_ZIP%' -DestinationPath 'ffmpeg\_tmp' -Force"
:: Mover la carpeta bin/ desde el subdirectorio del ZIP
powershell -NoProfile -Command ^
    "$src = Get-ChildItem 'ffmpeg\_tmp' -Directory | Select-Object -First 1;" ^
    "if ($src) { Move-Item ($src.FullName + '\bin') 'ffmpeg\bin' -Force }"
rmdir /s /q "ffmpeg\_tmp" 2>nul
del /q "%FFMPEG_ZIP%" 2>nul
echo  [OK] FFmpeg instalado en ffmpeg\bin\

:: ── RESUMEN ───────────────────────────────────────────────
:done
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║                   RESUMEN FINAL                      ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

if exist "models\vosk\vosk-model-small-es-0.42"  (echo  [OK] Vosk ES) else (echo  [!!] Vosk ES — FALTA)
if exist "models\vosk\vosk-model-small-en-us-0.15" (echo  [OK] Vosk EN) else (echo  [!!] Vosk EN — FALTA)
if exist "piper\piper.exe"                        (echo  [OK] Piper TTS) else (echo  [!!] Piper TTS — FALTA)
if exist "piper\models\es_MX-claude-high.onnx"   (echo  [OK] Voz ES) else (echo  [!!] Voz ES — FALTA)
if exist "piper\models\en_US-kristin-medium.onnx" (echo  [OK] Voz EN) else (echo  [!!] Voz EN — FALTA)
if exist "ffmpeg\bin\ffmpeg.exe"                  (echo  [OK] FFmpeg) else (echo  [!!] FFmpeg — FALTA)

echo.
echo  Si algún recurso falta, consulta: requirements_extra.md
echo  para instrucciones de descarga manual.
echo.
pause
