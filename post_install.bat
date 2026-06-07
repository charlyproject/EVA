@echo off
REM ====================================================
REM POST-INSTALL SCRIPT FOR EVA - ENHANCED RELIABILITY
REM ====================================================

setlocal enabledelayedexpansion

:: Configuración de rutas
set "LOG_FILE=%TEMP%\EVA_Install_%RANDOM%.log"
set "APP_DATA=%APPDATA%\EVA"
set "CONFIG_DIR=%APP_DATA%\config"
set "LOGS_DIR=%APP_DATA%\logs"
set "TEMP_DIR=%TEMP%\EVA_Install"

:: Iniciar registro de errores
echo Iniciando proceso de post-instalación: %DATE% %TIME% > "%LOG_FILE%"

:: Función para registrar mensajes
:log
(
    echo [%TIME%] %~1
) >> "%LOG_FILE%" 2>&1
goto :eof

:: Función para manejar errores
:error_exit
call :log "ERROR: %~1"
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"
exit /b 1

:: Crear directorios necesarios
call :log "Creando directorios de configuración..."
(
    if not exist "%APP_DATA%" mkdir "%APP_DATA%"
    if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"
    if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
    if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"
) || call :error_exit "No se pudieron crear los directorios necesarios"

:: NO crear configuración inicial - se maneja por el wizard integrado
call :log "Configuración inicial se manejará por el wizard integrado en EVA.exe"

:: Verificar permisos
call :log "Verificando permisos..."
(
    echo Test de escritura > "%CONFIG_DIR%\test.tmp"
    if errorlevel 1 (
        call :error_exit "No se tienen permisos de escritura en %CONFIG_DIR%"
    )
    del "%CONFIG_DIR%\test.tmp"
)

:: Limpieza final
call :log "Realizando limpieza..."
if exist "%TEMP_DIR%" rmdir /s /q "%TEMP_DIR%"

call :log "Post-instalación completada exitosamente"
exit /b 0