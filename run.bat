@echo off
powershell -NoLogo -ExecutionPolicy Bypass -NoExit -File "%~dp0run.ps1"
echo.
echo (La ventana queda abierta para ver errores. Cierra cuando quieras.)
pause >nul
