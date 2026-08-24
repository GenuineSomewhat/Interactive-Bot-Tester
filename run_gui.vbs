' VBScript to launch GUI without showing console window
' Save this as run_gui.vbs and double-click to run silently
Set objShell = CreateObject("WScript.Shell")
strBatchPath = objShell.CurrentDirectory & "\run_gui.bat"
' Run hidden (0 = hidden window, False = wait for completion)
objShell.Run chr(34) & strBatchPath & chr(34), 0, False
