# Lanzador del ciclo /semis-ciclo para el Programador de tareas de Windows.
# Copia este fichero FUERA del repo (p. ej. C:\Users\<tú>\semis-ciclo\) y ajusta $Repo y $LogDir.
# El log también va fuera del repo: si quedara dentro como fichero sin commit, el paso 0.1 del ciclo pararía.
#
# Registro de la tarea (PowerShell, una vez; martes a sábado a las 8:00 y, si el equipo estaba apagado,
# en cuanto se encienda):
#   $a = New-ScheduledTaskAction -Execute "powershell.exe" -Argument '-NoProfile -ExecutionPolicy Bypass -File "C:\Users\<tú>\semis-ciclo\semis-ciclo.ps1"'
#   $t = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Tuesday,Wednesday,Thursday,Friday,Saturday -At 8:00
#   $s = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 3)
#   Register-ScheduledTask -TaskName "semis-ciclo" -Action $a -Trigger $t -Settings $s

$Repo   = "C:\ruta\a\Trading-AI-Growth"
$LogDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Log = Join-Path $LogDir ("semis-ciclo_{0:yyyy-MM-dd_HHmm}.log" -f (Get-Date))

if (-not $env:SEC_USER_AGENT) { "SEC_USER_AGENT no definida" | Out-File $Log -Encoding utf8; exit 1 }

# UTF-8 de extremo a extremo: el prompt va por la entrada estándar (no como argumento) para que
# PowerShell 5.1 no rompa las comillas dobles ni las tildes del .md.
[Console]::InputEncoding  = [Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding           = [Text.UTF8Encoding]::new($false)

Set-Location $Repo
$prompt = Get-Content -Raw -Encoding UTF8 ".claude\commands\semis-ciclo.md"
$prompt | claude -p --permission-mode acceptEdits `
  --allowedTools "Bash(py:*)" "Bash(python3:*)" "Bash(git:*)" "Bash(curl:*)" "WebSearch" "WebFetch" `
  *>&1 | Out-File $Log -Encoding utf8
exit $LASTEXITCODE
