Set sh = CreateObject("WScript.Shell")
root = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
cmd = "cmd /k cd /d """ & root & """ && .venv\Scripts\python.exe run_whatsapp.py"
sh.Run cmd, 1, False