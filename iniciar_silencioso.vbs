Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strPath = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath
' Inicia Streamlit sin ventana negra de consola y abre el navegador automáticamente
WshShell.Run "cmd /c python -m streamlit run app.py", 0, False
