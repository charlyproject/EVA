@echo off
REM Este script prepara la estructura para el instalador
REM Ejecutar como administrador antes de compilar

set PROJECT_ROOT=%~dp0
set INSTALLER_DIR=%PROJECT_ROOT%installer

REM Crear directorio de recursos del instalador
if not exist "%INSTALLER_DIR%\resources" mkdir "%INSTALLER_DIR%\resources"
if not exist "%INSTALLER_DIR%\resources\themes" mkdir "%INSTALLER_DIR%\resources\themes"

REM Copiar iconos
copy "%PROJECT_ROOT%resources\icon.ico" "%INSTALLER_DIR%\resources\themes\installer_icon.ico"

REM Generar banners si no existen
if not exist "%INSTALLER_DIR%\resources\themes\installer_banner.bmp" (
    echo Creando banner del instalador...
    python -c "from PIL import Image, ImageDraw, ImageFont; img = Image.new('RGB', (164,314), 'black'); d = ImageDraw.Draw(img); d.text((10,150), 'EVA', fill='cyan'); img.save(r'%INSTALLER_DIR%\resources\themes\installer_banner.bmp')"
)

if not exist "%INSTALLER_DIR%\resources\themes\installer_small.bmp" (
    echo Creando banner pequeño...
    python -c "from PIL import Image, ImageDraw, ImageFont; img = Image.new('RGB', (55,58), 'black'); d = ImageDraw.Draw(img); d.text((5,15), 'E', fill='cyan'); img.save(r'%INSTALLER_DIR%\resources\themes\installer_small.bmp')"
)

REM Verificar estructura
echo Verificando estructura de proyecto...
dir "%PROJECT_ROOT%main.py" || exit /b 1
dir "%PROJECT_ROOT%resources\icon.ico" || exit /b 1
dir "%PROJECT_ROOT%ffmpeg\bin\ffmpeg.exe" || exit /b 1
dir "%PROJECT_ROOT%piper\piper.exe" || exit /b 1

echo Preparación completada! Ahora compila el instalador.
pause