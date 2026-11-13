@echo off
cd /d "%~dp0"
echo Generando paquete ZIP para enviar por WhatsApp o correo...
python package_dist.py
echo.
echo ===============================================================================
echo Archivo listo en tu Escritorio:
echo "Auditor_DIGEMID_Instalador_AporteMedico.zip"
echo ===============================================================================
timeout /t 5
exit /b 0
