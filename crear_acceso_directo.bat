@echo off
cd /d "%~dp0"
echo Creando acceso directo en el Escritorio con icono corporativo...
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
echo Acceso directo creado exitosamente en tu Escritorio: "Auditor DIGEMID - Aporte Medico"
timeout /t 3
exit /b 0
