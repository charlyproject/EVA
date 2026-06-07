@echo off
chcp 65001 > nul

:: Configurar rutas
set PROJECT_ROOT=%cd%
set PYTHON_EMBED=%PROJECT_ROOT%\_internal\python-embed\python.exe
set INNO_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
set SETUP_ISS=%PROJECT_ROOT%\installer\inno\setup.iss

:: Exportar PROJECT_ROOT para Inno Setup
set PROJECT_ROOT=%PROJECT_ROOT%

echo ====================================================
echo CONSTRUYENDO INSTALADOR DE EVA
echo ====================================================
echo Directorio del proyecto: %PROJECT_ROOT%
echo Python embebido: %PYTHON_EMBED%
echo Inno Setup: %INNO_PATH%
echo ====================================================

:: Verificar archivos esenciales
echo [1/5] Verificando archivos esenciales...
if not exist "%PROJECT_ROOT%\main.py" (
    echo ERROR: main.py no encontrado en %PROJECT_ROOT%
    pause
    exit /b 1
)

if not exist "%PYTHON_EMBED%" (
    echo ERROR: Python embebido no encontrado en %PYTHON_EMBED%
    pause
    exit /b 1
)

if not exist "%PROJECT_ROOT%\installer\inno\setup.iss" (
    echo ERROR: setup.iss no encontrado
    pause
    exit /b 1
)

echo Archivos esenciales verificados correctamente.

:: Limpiar builds anteriores
echo [2/5] Limpiando builds anteriores...
echo Eliminando directorios de build...
if exist "%PROJECT_ROOT%\dist" (
    echo - Eliminando dist\
    rmdir /s /q "%PROJECT_ROOT%\dist" 2>nul
)
if exist "%PROJECT_ROOT%\build" (
    echo - Eliminando build\
    rmdir /s /q "%PROJECT_ROOT%\build" 2>nul
)
if exist "%PROJECT_ROOT%\build_uninstall" (
    echo - Eliminando build_uninstall\
    rmdir /s /q "%PROJECT_ROOT%\build_uninstall" 2>nul
)

echo Eliminando archivos temporales de PyInstaller...
if exist "%PROJECT_ROOT%\*.spec~" del /q "%PROJECT_ROOT%\*.spec~" 2>nul
if exist "%PROJECT_ROOT%\__pycache__" rmdir /s /q "%PROJECT_ROOT%\__pycache__" 2>nul

echo Eliminando logs anteriores...
if exist "%PROJECT_ROOT%\*.log" del /q "%PROJECT_ROOT%\*.log" 2>nul
if exist "%PROJECT_ROOT%\installer\*.log" del /q "%PROJECT_ROOT%\installer\*.log" 2>nul

echo Eliminando archivos de instalador anteriores...
if exist "%PROJECT_ROOT%\EVA_Setup.exe" del /q "%PROJECT_ROOT%\EVA_Setup.exe" 2>nul
if exist "%PROJECT_ROOT%\Output" rmdir /s /q "%PROJECT_ROOT%\Output" 2>nul

echo Creando directorio dist limpio...
mkdir "%PROJECT_ROOT%\dist" 2>nul

echo Limpieza completada.

:: Construir wizard de configuracion
echo [3/5] Construyendo wizard de configuracion...
"%PYTHON_EMBED%" -m PyInstaller --noconfirm "%PROJECT_ROOT%\EVA_Wizard.spec"

if errorlevel 1 (
    echo WARNING: Fallo al construir wizard de configuracion
    echo Continuando sin wizard...
) else (
    echo Wizard de configuracion construido exitosamente.
)

:: Construir aplicacion principal EVA
echo [4/5] Construyendo EVA principal...
"%PYTHON_EMBED%" -m PyInstaller --noconfirm "%PROJECT_ROOT%\EVA_new.spec"

if errorlevel 1 (
    echo ERROR: Fallo al construir EVA principal
    pause
    exit /b 1
)
echo EVA principal construido exitosamente.

:: Construir desinstalador
echo Construyendo desinstalador...
"%PYTHON_EMBED%" -m PyInstaller ^
  --noconfirm ^
  --onefile ^
  --console ^
  --distpath "%PROJECT_ROOT%\dist" ^
  --workpath "%PROJECT_ROOT%\build_uninstall" ^
  --name "UninstallEVA" ^
  --icon "%PROJECT_ROOT%\resources\icon.ico" ^
  "%PROJECT_ROOT%\installer\scripts\uninstall.py"

if errorlevel 1 (
    echo WARNING: Fallo al construir desinstalador
) else (
    echo Desinstalador construido exitosamente.
)

:: Construir instalador con Inno Setup
echo [5/5] Construyendo instalador (setup.exe)...
if exist %INNO_PATH% (
    %INNO_PATH% /O"%PROJECT_ROOT%\dist" /F"EVA_Setup" "%SETUP_ISS%"
    if errorlevel 1 (
        echo ERROR: Fallo al crear el instalador con Inno Setup
        pause
        exit /b 1
    )
    echo.
    echo ====================================================
    echo INSTALADOR CREADO EXITOSAMENTE
    echo ====================================================
    echo Ubicacion: %PROJECT_ROOT%\dist\EVA_Setup.exe
    echo ====================================================
) else (
    echo.
    echo ERROR: Inno Setup no encontrado en la ubicacion predeterminada.
    echo Por favor instale Inno Setup desde:
    echo https://jrsoftware.org/isdl.php
    echo.
    echo O ejecute este comando manualmente desde la carpeta de Inno Setup:
    echo ISCC /O"%PROJECT_ROOT%\dist" /F"EVA_Setup" "%SETUP_ISS%"
    echo.
    pause
    exit /b 1
)

echo Proceso completado exitosamente.
pause