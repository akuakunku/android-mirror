$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$exePath = Join-Path $scriptPath "AndroidMirror.exe"
Start-Process -FilePath $exePath -WindowStyle Hidden
