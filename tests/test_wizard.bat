@echo off
echo ========================================
echo    EVA Wizard Test - Prueba Independiente
echo ========================================
echo.
echo Este script ejecuta el wizard de configuracion
echo inicial de EVA de forma independiente.
echo.
echo Presiona cualquier tecla para continuar...
pause >nul

echo.
echo Ejecutando wizard...
echo.

python test_wizard.py

echo.
echo ========================================
echo Prueba completada. Presiona cualquier tecla para salir...
pause >nul