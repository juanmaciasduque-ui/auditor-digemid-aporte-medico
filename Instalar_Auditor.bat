@echo off
setlocal enabledelayedexpansion
title INSTALADOR OFICIAL - AUDITOR DIGEMID (APORTE MEDICO PERU)
cd /d "%~dp0"

echo ===============================================================================
echo      INSTALADOR DEL AUDITOR FORENSE DOCUMENTAL DIGEMID (PERU)
echo                  APORTE MEDICO PERU S.A.C.
echo ===============================================================================
echo.
echo Este asistente preparara el programa en tu equipo para que funcione
echo al 100%% sin configuraciones complejas.
echo.

:: 1. Comprobar si Python esta instalado
echo [Paso 1/5] Verificando instalacion de Python en el equipo...
python --version >nul 2>&1
if %errorLevel% equ 0 (
    echo     -- Python ya esta instalado en tu equipo.
    for /f "tokens=*" %%v in ('python --version') do echo     -- Version detectada: %%v
) else (
    echo     -- Python no esta instalado.
    echo     -- Descargando instalador oficial firmado de Python 3.12 desde python.org...
    curl -L -o python_setup.exe https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe
    if not exist python_setup.exe (
        echo [ERROR] No se pudo descargar Python. Verifique su conexion a Internet.
        pause
        exit /b 1
    )
    echo     -- Instalando Python 3.12 de forma silenciosa (puede tomar 1 minuto)...
    python_setup.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 SimpleInstall=1
    del /f /q python_setup.exe >nul 2>&1
    
    :: Agregar al PATH de esta sesion
    set "PATH=%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts;%PATH%"
    echo     -- Python instalado y configurado correctamente.
)

:: 2. Actualizar pip e instalar dependencias del sistema
echo.
echo [Paso 2/5] Instalando librerias y motores de auditoria (PyMuPDF, RapidOCR, Streamlit)...
python -m pip install --upgrade pip --quiet
python -m pip install -r requirements.txt --quiet
if %errorLevel% neq 0 (
    echo [AVISO] Reintentando instalacion con salida visible...
    python -m pip install -r requirements.txt
)

:: 3. Configurar credenciales silenciosas de Streamlit (Evita pantallas de bloqueo)
echo.
echo [Paso 3/5] Configurando preferencias del sistema...
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
echo [general]> "%USERPROFILE%\.streamlit\credentials.toml"
echo email = "">> "%USERPROFILE%\.streamlit\credentials.toml"

if not exist ".streamlit" mkdir ".streamlit"
echo [general]> ".streamlit\credentials.toml"
echo email = "">> ".streamlit\credentials.toml"

:: 4. Crear acceso directo en el Escritorio con icono corporativo
echo.
echo [Paso 4/5] Creando acceso directo en tu Escritorio...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Desktop = [System.Environment]::GetFolderPath('Desktop'); " ^
    "$Shortcut = $WshShell.CreateShortcut(\"$Desktop\Auditor DIGEMID - Aporte Medico.lnk\"); " ^
    "$Shortcut.TargetPath = 'wscript.exe'; " ^
    "$Shortcut.Arguments = '\"' + $PWD.Path + '\iniciar_silencioso.vbs\"'; " ^
    "$Shortcut.WorkingDirectory = $PWD.Path; " ^
    "$Shortcut.IconLocation = $PWD.Path + '\assets\logo_aporte_medico.ico'; " ^
    "$Shortcut.Description = 'Auditor Forense Documental DIGEMID - Aporte Medico Peru S.A.C.'; " ^
    "$Shortcut.Save(); "

echo     -- Acceso directo 'Auditor DIGEMID - Aporte Medico' creado en el Escritorio.

:: 5. Iniciar la aplicacion de inmediato
echo.
echo [Paso 5/5] Iniciando el Auditor y abriendo el navegador...
echo.
echo ===============================================================================
echo   INSTALACION COMPLETADA CON EXITO AL 100%%
echo   A partir de ahora puedes abrir el programa directamente desde el icono en
echo   tu Escritorio: "Auditor DIGEMID - Aporte Medico"
echo ===============================================================================
echo.

start "" pythonw.exe launcher.py
timeout /t 5
exit /b 0
