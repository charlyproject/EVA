@echo off
REM Script rapido para construir solo EVA sin instalador
chcp 65001 > nul

set PROJECT_ROOT=%cd%
set PYTHON_EMBED=%PROJECT_ROOT%\_internal\python-embed\python.exe

echo ====================================================
echo CONSTRUCCION RAPIDA DE EVA - WIZARD CORREGIDO
echo ====================================================
echo - Error de LicenseManager corregido
echo - Consola deshabilitada para GUI
echo - Wizard SOLO en primera ejecucion (sin app principal)
echo - Logica de ventana principal corregida
echo - Deteccion de primera ejecucion ARREGLADA
echo - Proteccion contra procesos duplicados agregada
echo - Tray icon restaurado y funcionando
echo - Error de acceso directo en escritorio corregido
echo - Configuracion inicial duplicada eliminada
echo - Consistencia de idioma en mensajes del sistema corregida
echo ====================================================

:: Verificar archivos esenciales
if not exist "%PROJECT_ROOT%\main.py" (
    echo ERROR: main.py no encontrado
    pause
    exit /b 1
)

if not exist "%PYTHON_EMBED%" (
    echo ERROR: Python embebido no encontrado
    pause
    exit /b 1
)

:: Limpiar build anterior completamente
echo Limpiando builds anteriores...
if exist "%PROJECT_ROOT%\dist\EVA.exe" del "%PROJECT_ROOT%\dist\EVA.exe" 2>nul
if exist "%PROJECT_ROOT%\build" rmdir /s /q "%PROJECT_ROOT%\build" 2>nul

:: Construir solo EVA
echo Construyendo EVA con correcciones del wizard...
"%PYTHON_EMBED%" -m PyInstaller --noconfirm "%PROJECT_ROOT%\EVA_new.spec"

if errorlevel 1 (
    echo ERROR: Fallo al construir EVA
    echo Revisa los logs para mas detalles
    pause
    exit /b 1
)

echo ====================================================
echo EVA CONSTRUIDO EXITOSAMENTE CON CORRECCIONES
echo ====================================================
echo Ubicacion: %PROJECT_ROOT%\dist\EVA.exe
echo.
echo CAMBIOS APLICADOS:
echo - Sin consola CMD (aplicacion GUI pura)
echo - Error de licencia corregido
echo - Wizard SOLO en primera ejecucion (no abre app principal)
echo - Ventana principal se crea DESPUES del wizard
echo - Primera ejecucion se marca correctamente como completada
echo - Wizard usa aplicacion existente (no crea procesos duplicados)
echo - Acceso directo usa userdesktop (sin permisos admin)
echo - Solo wizard integrado (sin post_install duplicado)
echo - Mensajes del sistema respetan idioma configurado
echo ====================================================

echo.
echo OPCIONES DE PRUEBA:
echo ==================
echo 1. Probar sistema de primera ejecucion:
echo    python test_first_run.py
echo.
echo 2. Limpiar configuracion y probar wizard:
echo    del "%USERPROFILE%\.eva\config.json"
echo    "%PROJECT_ROOT%\dist\EVA.exe"
echo.
echo 3. Ejecutar EVA normalmente:
echo    "%PROJECT_ROOT%\dist\EVA.exe"
echo ==================

echo.
echo Ejecutando EVA para probar...
start "" "%PROJECT_ROOT%\dist\EVA.exe"

pause