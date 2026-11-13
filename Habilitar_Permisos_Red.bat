@echo off
title Configurar Permisos de Red y Firewall - Auditor DIGEMID
cd /d "%~dp0"

:: Verificar si tiene permisos de administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Solicitando permisos de administrador...
    powershell -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
    exit /b
)

echo ===============================================================================
echo   HABILITAR PERMISOS DE RED Y FIREWALL DE WINDOWS
echo   Auditor Forense Documental DIGEMID - Aporte Medico Peru S.A.C.
echo ===============================================================================
echo.
echo 1. Limpiando reglas previas si existieran...
netsh advfirewall firewall delete rule name="Auditor DIGEMID - Aporte Medico (TCP 8501)" >nul 2>&1

echo 2. Habilitando regla de entrada para el Puerto 8501 (Red Privada y de Oficina)...
netsh advfirewall firewall add rule name="Auditor DIGEMID - Aporte Medico (TCP 8501)" dir=in action=allow protocol=TCP localport=8501 profile=private,domain description="Permite el acceso web al Auditor Documental DIGEMID de Aporte Medico"

echo.
echo ===============================================================================
echo   LISTO: Permisos de red habilitados exitosamente.
echo   La aplicacion podra recibir conexiones sin bloqueos del Firewall de Windows.
echo ===============================================================================
timeout /t 5
exit /b 0
