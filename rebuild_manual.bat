@echo off

cd /d "%~dp0"

echo Eliminando EVA.exe anterior...
if exist "dist\EVA.exe" del /f /q "dist\EVA.exe"

echo Recompilando EVA...
"_internal\python-embed\python.exe" -m PyInstaller --clean --noconfirm "EVA_new.spec"

echo Verificando resultado...
if exist "dist\EVA.exe" (
    echo EXITO: EVA.exe recompilado
    echo PRUEBA: dist\EVA.exe
) else (
    echo ERROR: No se genero EVA.exe
)

pause