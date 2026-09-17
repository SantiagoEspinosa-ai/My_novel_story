# telemetria-langfuse.ps1 — monta la cabecera de autenticacion de Langfuse.
#
# QUE HACE Y POR QUE EXISTE
# -------------------------
# El resto de la configuracion de telemetria (activarla, el exportador, la URL)
# vive en .claude/settings.json, que va a git. Lo unico que NO puede vivir ahi
# es la credencial. Este script la lee de una variable de entorno de tu maquina
# y arma con ella la cabecera que Claude Code enviara a Langfuse.
#
# La credencial nunca se escribe en ningun archivo del proyecto: ni aqui, ni en
# settings.json, ni en un .env. Este script la lee, la usa y no la guarda.
#
# QUIEN HABLA CON LANGFUSE
# ------------------------
# Claude Code, no el harness. El CLI exporta sus propias trazas por OTLP. Ningun
# modulo de Python de src/ sale a la red, que es la regla del proyecto: esto se
# monta por fuera, en el entorno del proceso que ejecuta el CLI.
#
# COMO SE USA
# -----------
# Hay que ejecutarlo CON UN PUNTO DELANTE (se dice "dot-sourcing"). Sin el punto,
# el script se ejecuta en su propio ambito, las variables mueren con el, y tu
# sesion de PowerShell se queda igual que estaba:
#
#     $env:LANGFUSE_AUTH_BASIC = "<el base64 de clave_publica:clave_secreta>"
#     . .\herramientas\telemetria-langfuse.ps1
#     claude
#
# Para que la variable no haya que ponerla en cada sesion, guardala una sola vez
# en tu usuario de Windows (esto no toca el repositorio):
#
#     [Environment]::SetEnvironmentVariable("LANGFUSE_AUTH_BASIC", "<base64>", "User")
#
# y abre una terminal nueva.

[CmdletBinding()]
param(
    # Region de Langfuse. Cambia la URL a la nube europea si tu proyecto esta alli.
    [ValidateSet("us", "eu")]
    [string]$Region = "us"
)

$ErrorActionPreference = "Stop"

if ($MyInvocation.InvocationName -ne '.') {
    Write-Warning "Este script hay que ejecutarlo con un punto delante para que las variables sobrevivan:"
    Write-Warning "    . .\herramientas\telemetria-langfuse.ps1"
    Write-Warning "Sin el punto no pasa nada malo, pero tampoco pasa nada util."
}

$auth = $env:LANGFUSE_AUTH_BASIC
if ([string]::IsNullOrWhiteSpace($auth)) {
    Write-Error @'
Falta la variable de entorno LANGFUSE_AUTH_BASIC.

Es el resultado de codificar en base64 la cadena "clave_publica:clave_secreta"
de tu proyecto de Langfuse. Para generarla sin dejarla escrita en ningun archivo:

    $par = "pk-lf-...:sk-lf-..."
    $env:LANGFUSE_AUTH_BASIC = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($par))

y despues vuelve a lanzar este script con el punto delante.
'@
}

# La cabecera x-langfuse-ingestion-version: 4 no es opcional en la practica. Sin
# ella la traza se guarda, pero tarda hasta quince minutos en aparecer en los
# endpoints v2 que usa la interfaz, y da la impresion de que no ha llegado nada.
# Con ella aparece en segundos. Es la diferencia entre depurar y adivinar.
$cabeceras = "Authorization=Basic $auth,x-langfuse-ingestion-version=4"

$base = if ($Region -eq "eu") { "https://cloud.langfuse.com" } else { "https://us.cloud.langfuse.com" }

$env:OTEL_EXPORTER_OTLP_TRACES_HEADERS = $cabeceras

# Estas tres ya vienen de .claude/settings.json cuando arrancas `claude` desde la
# raiz del proyecto. Se repiten aqui para que la comprobacion de la seccion
# siguiente, y cualquier herramienta que lances a mano desde esta misma terminal,
# sepan a donde apuntan sin tener que leer settings.json.
$env:OTEL_EXPORTER_OTLP_TRACES_ENDPOINT = "$base/api/public/otel/v1/traces"
$env:OTEL_EXPORTER_OTLP_TRACES_PROTOCOL = "http/protobuf"
$env:CLAUDE_CODE_ENABLE_TELEMETRY = "1"
$env:CLAUDE_CODE_ENHANCED_TELEMETRY_BETA = "1"

Write-Host "Telemetria montada para Langfuse ($Region)." -ForegroundColor Green
Write-Host "  Endpoint: $env:OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"
Write-Host "  Cabeceras: Authorization=Basic <oculto>,x-langfuse-ingestion-version=4"
Write-Host ""
Write-Host "Siguiente paso: comprueba que llega una traza antes de gastar una generacion."
Write-Host "  .\herramientas\comprobar-langfuse.ps1"
