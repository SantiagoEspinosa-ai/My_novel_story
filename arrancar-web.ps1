# Levanta la API (8000) y la web (5173) en segundo plano, y deja los registros en
# backend\salida\. Uso, desde la raiz del repositorio:
#
#   powershell -ExecutionPolicy Bypass -File .\arrancar-web.ps1 [-Base backend\web.db]
#
# Si no hay `node` en el PATH, usa el Node que trae VS Code (Electron con
# ELECTRON_RUN_AS_NODE=1): no instala nada. Necesita `frontend\node_modules` (npm ci, una vez).
# Para generar de verdad necesita `claude` con la sesion iniciada: lo busca en el PATH o en la
# extension de VS Code. Generar gasta dinero y solo lo lanza la confirmacion de la web.
param([string]$Base = "backend\web.db")

$raiz = $PSScriptRoot
$logs = Join-Path $raiz "backend\salida"
New-Item -ItemType Directory -Force $logs | Out-Null

$claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
if (-not $claude) {
    $ext = Get-ChildItem "$env:USERPROFILE\.vscode\extensions" -Directory -Filter "anthropic.claude-code-*" -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending | Select-Object -First 1
    if ($ext) { $claude = Join-Path $ext.FullName "resources\native-binary\claude.exe" }
}
if ($claude) { $env:HARNESS_CLAUDE_BIN = $claude } else { Write-Warning "sin claude: se puede leer y entrevistar la ficha, pero ningun turno ni generacion llamara al modelo" }

$env:HARNESS_BASE = (Resolve-Path (Join-Path $raiz $Base)).Path
$api = Start-Process -FilePath python -ArgumentList "-X","utf8","-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" `
    -WorkingDirectory (Join-Path $raiz "backend") -RedirectStandardOutput "$logs\api.log" -RedirectStandardError "$logs\api.err.log" -WindowStyle Hidden -PassThru

$node = (Get-Command node -ErrorAction SilentlyContinue).Source
if (-not $node) {
    $node = "$env:LOCALAPPDATA\Programs\Microsoft VS Code\Code.exe"
    $env:ELECTRON_RUN_AS_NODE = "1"
}
$env:HARNESS_API = "http://127.0.0.1:8000"
$web = Start-Process -FilePath $node -ArgumentList "node_modules\vite\bin\vite.js","--port","5173","--strictPort","--host","127.0.0.1" `
    -WorkingDirectory (Join-Path $raiz "frontend") -RedirectStandardOutput "$logs\web.log" -RedirectStandardError "$logs\web.err.log" -WindowStyle Hidden -PassThru

Write-Output "API  pid $($api.Id)  http://127.0.0.1:8000  (base: $env:HARNESS_BASE)"
Write-Output "Web  pid $($web.Id)  http://127.0.0.1:5173"
Write-Output "claude: $claude"
Write-Output "Para pararlas: Stop-Process -Id $($api.Id),$($web.Id)"
