Set objShell = CreateObject("Wscript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")
strDesktop = objShell.SpecialFolders("Desktop")
strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
strExe = strPath & "\AndroidMirror.exe"
strShortcut = strDesktop & "\Android Mirror.lnk"

Set objShortcut = objShell.CreateShortcut(strShortcut)
objShortcut.TargetPath = strExe
objShortcut.WorkingDirectory = strPath
objShortcut.Description = "Android Mirror"
objShortcut.IconLocation = strExe & ", 0"
objShortcut.WindowStyle = 7
objShortcut.Save()

MsgBox "Shortcut created on Desktop!", 64, "Android Mirror"
