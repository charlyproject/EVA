# 🚀 GUÍA DE TRABAJO - BUILD AUTOMATIZADO EVA

## 📋 OBJETIVO
Crear script automatizado que:
1. Compile EVA usando Python embebido (_internal)
2. Genere instalador Inno Setup básico para AppData
3. NO descargue nada - todo offline desde _internal

## 🎯 PASOS A SEGUIR

### PASO 1: Crear EVA_FAST_CORRECTO.spec
**Archivo:** `EVA_FAST_CORRECTO.spec`
**Configuración:**
```python
# Usar Python embebido
python_exe = "_internal/python-embed/python.exe"

# Incluir TODO desde _internal
datas=[
    ('_internal', '_internal'),           # Python completo + PyTorch CPU
    ('config', 'config'),                 # Configuración
    ('models', 'models'),                 # Modelos Vosk
    ('piper', 'piper'),                   # Sistema TTS
    ('ffmpeg', 'ffmpeg'),                 # Multimedia
    ('resources', 'resources'),           # Iconos
],

# Usar hooks personalizados
hookspath=['hooks'],

# Optimizaciones
upx=False,                               # Sin compresión (más rápido)
optimize=0,                              # Sin optimización bytecode
```

### PASO 2: Crear build_automatizado.bat
**Archivo:** `build_automatizado.bat`
**Funciones:**
- Limpiar compilaciones anteriores
- Usar `_internal/python-embed/python.exe` DIRECTAMENTE
- Ejecutar PyInstaller con EVA_FAST_CORRECTO.spec
- Verificar resultado

### PASO 3: Crear EVA_INSTALLER_SIMPLE.iss
**Archivo:** `EVA_INSTALLER_SIMPLE.iss`
**Configuración básica:**
```ini
[Setup]
AppName=EVA
DefaultDirName={localappdata}\EVA
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "Crear icono en escritorio"; Flags: unchecked

[Files]
Source: "dist\EVA_FAST\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\EVA"; Filename: "{app}\EVA_FAST.exe"
Name: "{autodesktop}\EVA"; Filename: "{app}\EVA_FAST.exe"; Tasks: desktopicon
```

### PASO 4: Crear script_completo.bat
**Archivo:** `script_completo.bat`
**Flujo:**
1. Ejecutar build_automatizado.bat
2. Compilar instalador con Inno Setup
3. Verificar archivos generados

## ✅ VERIFICACIONES NECESARIAS

### Pre-compilación:
- [ ] _internal/python-embed/python.exe existe
- [ ] _internal/python-embed/Lib/site-packages/torch existe
- [ ] models/vosk/ tiene modelos
- [ ] piper/ tiene ejecutables y modelos
- [ ] ffmpeg/bin/ tiene ejecutables

### Post-compilación:
- [ ] dist/EVA_FAST/EVA_FAST.exe generado
- [ ] dist/EVA_FAST/_internal/ incluido
- [ ] dist/EVA_FAST/models/ incluido
- [ ] dist/EVA_FAST/piper/ incluido
- [ ] dist/EVA_FAST/ffmpeg/ incluido

### Post-instalador:
- [ ] installer/EVA_Setup.exe generado
- [ ] Instalador funciona sin permisos admin
- [ ] EVA ejecuta desde instalación

## 🔧 CONFIGURACIÓN CRÍTICA

### PyTorch CPU desde _internal:
- ✅ torch-2.8.0+cpu ya está en _internal/python-embed/Lib/site-packages/
- ✅ NO descargar - usar el embebido
- ✅ Hooks personalizados manejan la inclusión

### Rutas dinámicas:
- ✅ dynamic_path_resolver.py maneja detección automática
- ✅ Busca en _internal/ como fallback
- ✅ Funciona tanto en desarrollo como en EXE

### Dependencias offline:
- ✅ TODO está en _internal/python-embed/Lib/site-packages/
- ✅ Modelos en models/vosk/
- ✅ TTS en piper/
- ✅ Multimedia en ffmpeg/

## 📁 ARCHIVOS A CREAR

1. **EVA_FAST_CORRECTO.spec** - Configuración PyInstaller corregida
2. **build_automatizado.bat** - Script compilación
3. **EVA_INSTALLER_SIMPLE.iss** - Configuración Inno Setup básica
4. **script_completo.bat** - Script maestro completo

## 🎯 RESULTADO ESPERADO

**Ejecutar:** `script_completo.bat`
**Resultado:** `installer/EVA_Setup.exe` listo para distribuir
**Funcionalidad:** Instalación en AppData, EVA funcional offline

---

## 🚀 COMENZAR IMPLEMENTACIÓN

**SIGUIENTE PASO:** Crear EVA_FAST_CORRECTO.spec con configuración corregida