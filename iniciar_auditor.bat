@echo off
title AUDITOR DOCUMENTAL DIGEMID - APORTE MEDICO PERU S.A.C.
cd /d "%~dp0"
echo ===============================================================================
echo   SISTEMA AUDITOR FORENSE DOCUMENTAL DIGEMID (PERU)
echo   Titular: APORTE MEDICO PERU S.A.C.
echo   Caso Base: Cateteres Ureterales Doble J y Set (ACE Medical Devices)
echo ===============================================================================
echo.
echo Iniciando aplicacion web en su navegador...
python -m streamlit run app.py
pause
