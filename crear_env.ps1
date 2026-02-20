# Script para crear el archivo .env desde .env.example
# Ejecuta este script en PowerShell: .\crear_env.ps1

Write-Host "🚀 Creando archivo .env para desarrollo local..." -ForegroundColor Green

if (Test-Path .env) {
    Write-Host "⚠️  El archivo .env ya existe." -ForegroundColor Yellow
    $respuesta = Read-Host "¿Quieres sobrescribirlo? (s/N)"
    if ($respuesta -ne "s" -and $respuesta -ne "S") {
        Write-Host "❌ Operación cancelada." -ForegroundColor Red
        exit
    }
}

if (-not (Test-Path .env.example)) {
    Write-Host "❌ Error: No se encuentra el archivo .env.example" -ForegroundColor Red
    Write-Host "   Asegúrate de que el archivo existe en el directorio actual." -ForegroundColor Yellow
    exit 1
}

Copy-Item .env.example .env
Write-Host "✅ Archivo .env creado exitosamente desde .env.example" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Próximos pasos:" -ForegroundColor Cyan
Write-Host "   1. Abre el archivo .env con tu editor de texto" -ForegroundColor White
Write-Host "   2. Completa las variables con tus valores reales:" -ForegroundColor White
Write-Host "      - DATABASE_URL: URL de tu base de datos PostgreSQL local" -ForegroundColor White
Write-Host "      - TWILIO_ACCOUNT_SID: Tu Account SID de Twilio" -ForegroundColor White
Write-Host "      - TWILIO_AUTH_TOKEN: Tu Auth Token de Twilio" -ForegroundColor White
Write-Host "      - TWILIO_WHATSAPP_NUMBER: Número de WhatsApp (usa whatsapp:+14155238886 para Sandbox)" -ForegroundColor White
Write-Host "      - SECRET_KEY: Genera una con: python -c `"import secrets; print(secrets.token_hex(32))`"" -ForegroundColor White
Write-Host ""
Write-Host "📖 Para más información, consulta LEERME_ENV.md" -ForegroundColor Cyan


