# comprobar-langfuse.ps1 — manda UNA traza de prueba y dice si Langfuse la acepta.
#
# QUE CONTESTA ESTE SCRIPT
# ------------------------
# La pregunta "esta bien montada la telemetria?" tiene dos mitades, y esta es la
# que se puede contestar en cinco segundos y sin gastar una generacion de novela:
#
#     1. El camino de red funciona: la URL es correcta, la credencial es valida,
#        Langfuse acepta lo que le mando.   <- esto es lo que comprueba el script
#     2. Claude Code produce trazas y las manda por ese camino.
#        <- eso se comprueba usando Claude Code, ver EJECUCION.md seccion 9.3
#
# Separarlas importa porque fallan por motivos distintos. Si el paso 1 falla, el
# problema es la credencial o la URL. Si el paso 1 va y las trazas del CLI no
# aparecen, el problema esta en el arranque de Claude Code, no en Langfuse.
#
# ESTE SCRIPT SI SALE A LA RED, Y ESO NO ROMPE LA REGLA DEL PROYECTO
# ------------------------------------------------------------------
# La regla de CLAUDE.md es que ningun modulo de Python del harness salga a la
# red. Esto no es el harness: es una herramienta de diagnostico que se lanza a
# mano, no la importa nadie de src/, y no participa en generar ninguna novela.
#
# COMO SE USA
# -----------
#     . .\herramientas\telemetria-langfuse.ps1
#     .\herramientas\comprobar-langfuse.ps1

[CmdletBinding()]
param(
    # Nombre con el que buscaras la traza en la interfaz de Langfuse.
    [string]$Nombre = "novela.comprobacion-telemetria"
)

$ErrorActionPreference = "Stop"

# PowerShell 5.1 negocia TLS 1.0 por defecto en algunas maquinas, y Langfuse solo
# acepta 1.2 o superior. Sin esta linea el error que sale ("conexion cerrada")
# hace pensar en un cortafuegos cuando en realidad es el protocolo.
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$auth = $env:LANGFUSE_AUTH_BASIC
if ([string]::IsNullOrWhiteSpace($auth)) {
    Write-Error "Falta LANGFUSE_AUTH_BASIC. Lanza primero: . .\herramientas\telemetria-langfuse.ps1"
}

$endpoint = $env:OTEL_EXPORTER_OTLP_TRACES_ENDPOINT
if ([string]::IsNullOrWhiteSpace($endpoint)) {
    $endpoint = "https://us.cloud.langfuse.com/api/public/otel/v1/traces"
}

# Un identificador de traza son 32 digitos hexadecimales y uno de span, 16. Se
# generan al azar: cada ejecucion de este script es una traza distinta, para que
# no se confunda con la de la vez anterior.
function Nuevo-Id([int]$bytes) {
    $b = New-Object byte[] $bytes
    [Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
    return (($b | ForEach-Object { $_.ToString("x2") }) -join "")
}

$ahora = [DateTimeOffset]::UtcNow
$finNano = [long]($ahora.ToUnixTimeMilliseconds()) * 1000000
$inicioNano = $finNano - 1000000  # un milisegundo de duracion, suficiente

$cuerpo = @{
    resourceSpans = @(
        @{
            resource = @{
                attributes = @(
                    @{ key = "service.name"; value = @{ stringValue = "my-novel-story" } }
                )
            }
            scopeSpans = @(
                @{
                    scope = @{ name = "comprobar-langfuse.ps1" }
                    spans = @(
                        @{
                            traceId           = (Nuevo-Id 16)
                            spanId            = (Nuevo-Id 8)
                            name              = $Nombre
                            kind              = 1
                            startTimeUnixNano = "$inicioNano"
                            endTimeUnixNano   = "$finNano"
                            attributes        = @(
                                @{ key = "comprobacion"; value = @{ stringValue = "manual" } }
                            )
                        }
                    )
                }
            )
        }
    )
} | ConvertTo-Json -Depth 12 -Compress

# Nota: aqui se manda OTLP en JSON, no en protobuf. Langfuse acepta los dos. El
# CLI usa protobuf (es lo que dice settings.json); JSON es lo que se puede
# construir a mano desde PowerShell sin dependencias.
$cabeceras = @{
    "Authorization"                = "Basic $auth"
    "x-langfuse-ingestion-version" = "4"
}

Write-Host "Mandando una traza de prueba a:" -ForegroundColor Cyan
Write-Host "  $endpoint"
Write-Host "  nombre del span: $Nombre"
Write-Host ""

try {
    $respuesta = Invoke-WebRequest -Uri $endpoint -Method Post -Headers $cabeceras `
        -ContentType "application/json" -Body $cuerpo -UseBasicParsing
    Write-Host "Langfuse respondio $($respuesta.StatusCode) $($respuesta.StatusDescription)." -ForegroundColor Green
    Write-Host ""
    Write-Host "El camino de red funciona. Ahora abre Langfuse y busca la traza:"
    Write-Host "  Tracing -> Traces, filtra por el nombre '$Nombre'."
    Write-Host "Deberia aparecer en segundos. Si tarda minutos, falta la cabecera"
    Write-Host "x-langfuse-ingestion-version: 4 en alguna parte del montaje."
}
catch {
    $codigo = $null
    if ($_.Exception.Response) { $codigo = [int]$_.Exception.Response.StatusCode }
    Write-Host "La traza NO se acepto." -ForegroundColor Red
    switch ($codigo) {
        401 { Write-Host "  401: la credencial no vale. Revisa LANGFUSE_AUTH_BASIC: tiene que ser el base64 de 'clave_publica:clave_secreta', de ESE proyecto de Langfuse." }
        403 { Write-Host "  403: la credencial es valida pero no tiene permiso sobre ese proyecto." }
        404 { Write-Host "  404: la URL no es la correcta. Comprueba la region (us o eu) y que termina en /api/public/otel/v1/traces." }
        default { Write-Host "  Detalle: $($_.Exception.Message)" }
    }
    exit 1
}
