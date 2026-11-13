@echo off
title AUDITOR DOCUMENTAL DIGEMID - AUDITORIA CLI
cd /d "%~dp0"
echo ===============================================================================
echo   EJECUTANDO AUDITORIA SOBRE BANCO DE PRUEBAS REAL
echo ===============================================================================
python cli.py --test-suite
echo.
echo Presione cualquier tecla para salir...
pause
