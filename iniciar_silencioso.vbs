Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strPath = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath

' Inicia launcher.py con pythonw.exe (sin ventana de consola) para abrir el navegador limpiamente
WshShell.Run "pythonw.exe launcher.py", 0, False
