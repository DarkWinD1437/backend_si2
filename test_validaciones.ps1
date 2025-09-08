# Script para probar validaciones de duplicados CI/NIT
# Ejecutar desde el directorio raíz del proyecto Django

param(
    [switch]$CrearDatos,
    [switch]$ProbarValidaciones,
    [switch]$MostrarEstadisticas,
    [switch]$LimpiarDatos,
    [switch]$TodoCompleto,
    [switch]$Ayuda
)

# Función para mostrar ayuda
function Show-Help {
    Write-Host "=== SCRIPT DE PRUEBAS DE VALIDACIÓN DE DUPLICADOS ===" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "USO:" -ForegroundColor Yellow
    Write-Host "  .\test_validaciones.ps1 [OPCIONES]"
    Write-Host ""
    Write-Host "OPCIONES:" -ForegroundColor Yellow
    Write-Host "  -CrearDatos          Crear datos de prueba"
    Write-Host "  -ProbarValidaciones  Ejecutar pruebas de validación"
    Write-Host "  -MostrarEstadisticas Mostrar estadísticas actuales"
    Write-Host "  -LimpiarDatos        Limpiar datos de prueba"
    Write-Host "  -TodoCompleto        Ejecutar secuencia completa"
    Write-Host "  -Ayuda               Mostrar esta ayuda"
    Write-Host ""
    Write-Host "EJEMPLOS:" -ForegroundColor Green
    Write-Host "  .\test_validaciones.ps1 -TodoCompleto"
    Write-Host "  .\test_validaciones.ps1 -CrearDatos -ProbarValidaciones"
    Write-Host "  .\test_validaciones.ps1 -MostrarEstadisticas"
    Write-Host ""
}

# Función para ejecutar comando Django con manejo de errores
function Invoke-DjangoCommand {
    param(
        [string]$Command,
        [string]$Description
    )
    
    Write-Host "`n>>> $Description" -ForegroundColor Cyan
    Write-Host "Ejecutando: python manage.py $Command" -ForegroundColor Gray
    Write-Host ("="*60) -ForegroundColor DarkGray
    
    try {
        $result = python manage.py $Command
        if ($LASTEXITCODE -eq 0) {
            Write-Host $result
            Write-Host "`n✅ $Description completado exitosamente" -ForegroundColor Green
        } else {
            Write-Host "❌ Error ejecutando: $Command" -ForegroundColor Red
            Write-Host $result -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Excepción ejecutando: $Command" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Función para probar endpoints API
function Test-ApiEndpoints {
    Write-Host "`n>>> PROBANDO ENDPOINTS DE VALIDACIÓN VÍA API" -ForegroundColor Cyan
    Write-Host ("="*60) -ForegroundColor DarkGray
    
    # Verificar si el servidor está corriendo
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/" -Method GET -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✅ Servidor Django está activo" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Servidor Django no está activo en http://localhost:8000" -ForegroundColor Red
        Write-Host "   Ejecuta: python manage.py runserver" -ForegroundColor Yellow
        return
    }
    
    # Test 1: Validar email nuevo
    Write-Host "`n1. Probando validación de email nuevo..."
    try {
        $body = @{
            email = "test.api@example.com"
        } | ConvertTo-Json
        
        $headers = @{
            "Content-Type" = "application/json"
        }
        
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/usuarios/validacion/validar-duplicados/" -Method POST -Body $body -Headers $headers -TimeoutSec 10
        Write-Host "   ✅ Email válido - Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "   Respuesta: $($response.Content)" -ForegroundColor Gray
    }
    catch {
        Write-Host "   ❌ Error validando email: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test 2: Validar documento nuevo
    Write-Host "`n2. Probando validación de documento nuevo..."
    try {
        $body = @{
            tipo_documento = "CI"
            numero_documento = "99887766"
            extension_documento = "5X"
        } | ConvertTo-Json
        
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/usuarios/validacion/validar-duplicados/" -Method POST -Body $body -Headers $headers -TimeoutSec 10
        Write-Host "   ✅ Documento válido - Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "   Respuesta: $($response.Content)" -ForegroundColor Gray
    }
    catch {
        Write-Host "   ❌ Error validando documento: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test 3: Obtener estadísticas de documentos
    Write-Host "`n3. Obteniendo estadísticas de documentos..."
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/usuarios/documentos/estadisticas/" -Method GET -TimeoutSec 10
        Write-Host "   ✅ Estadísticas obtenidas - Status: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "   Respuesta: $($response.Content)" -ForegroundColor Gray
    }
    catch {
        Write-Host "   ❌ Error obteniendo estadísticas: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Test 4: Listar documentos
    Write-Host "`n4. Listando documentos existentes..."
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/usuarios/documentos/" -Method GET -TimeoutSec 10
        Write-Host "   ✅ Lista obtenida - Status: $($response.StatusCode)" -ForegroundColor Green
        $documentos = $response.Content | ConvertFrom-Json
        Write-Host "   Total documentos: $($documentos.count)" -ForegroundColor Gray
    }
    catch {
        Write-Host "   ❌ Error listando documentos: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Función principal
function Main {
    Write-Host "=== PRUEBAS DE VALIDACIÓN DE DUPLICADOS CI/NIT ===" -ForegroundColor Cyan
    Write-Host "Cooperativa SI2 - Sistema de Auditoría" -ForegroundColor Gray
    Write-Host ("="*60) -ForegroundColor DarkGray
    
    # Verificar que estamos en el directorio correcto
    if (-not (Test-Path "manage.py")) {
        Write-Host "❌ Error: No se encontró manage.py" -ForegroundColor Red
        Write-Host "   Ejecuta este script desde el directorio raíz del proyecto Django" -ForegroundColor Yellow
        exit 1
    }
    
    # Verificar que el comando existe
    $commandExists = python manage.py help | Select-String "test_validaciones"
    if (-not $commandExists) {
        Write-Host "❌ Error: Comando test_validaciones no encontrado" -ForegroundColor Red
        Write-Host "   Verifica que el archivo de comando esté en la ruta correcta" -ForegroundColor Yellow
        exit 1
    }
    
    # Ejecutar según parámetros
    if ($Ayuda) {
        Show-Help
        return
    }
    
    if ($TodoCompleto) {
        Write-Host "🚀 EJECUTANDO SECUENCIA COMPLETA DE PRUEBAS" -ForegroundColor Magenta
        
        # 1. Mostrar estadísticas iniciales
        Invoke-DjangoCommand "test_validaciones --mostrar-estadisticas" "Estadísticas iniciales"
        
        # 2. Crear datos de prueba
        if (Invoke-DjangoCommand "test_validaciones --crear-datos-prueba" "Creación de datos de prueba") {
            
            # 3. Probar validaciones
            Invoke-DjangoCommand "test_validaciones --probar-validaciones" "Pruebas de validación"
            
            # 4. Mostrar estadísticas finales
            Invoke-DjangoCommand "test_validaciones --mostrar-estadisticas" "Estadísticas finales"
            
            # 5. Probar API (opcional)
            $respuesta = Read-Host "`n¿Probar endpoints de API? (y/N)"
            if ($respuesta -eq "y" -or $respuesta -eq "Y") {
                Test-ApiEndpoints
            }
            
            # 6. Limpiar datos
            $respuesta = Read-Host "`n¿Limpiar datos de prueba? (y/N)"
            if ($respuesta -eq "y" -or $respuesta -eq "Y") {
                Invoke-DjangoCommand "test_validaciones --limpiar-datos" "Limpieza de datos de prueba"
            }
        }
        
        Write-Host "`n🎉 SECUENCIA COMPLETA FINALIZADA" -ForegroundColor Magenta
        return
    }
    
    # Ejecutar comandos individuales
    if ($CrearDatos) {
        Invoke-DjangoCommand "test_validaciones --crear-datos-prueba" "Creación de datos de prueba"
    }
    
    if ($ProbarValidaciones) {
        Invoke-DjangoCommand "test_validaciones --probar-validaciones" "Pruebas de validación"
    }
    
    if ($MostrarEstadisticas) {
        Invoke-DjangoCommand "test_validaciones --mostrar-estadisticas" "Estadísticas de documentos"
    }
    
    if ($LimpiarDatos) {
        Invoke-DjangoCommand "test_validaciones --limpiar-datos" "Limpieza de datos de prueba"
    }
    
    # Si no se especificó ningún parámetro, mostrar ayuda
    if (-not ($CrearDatos -or $ProbarValidaciones -or $MostrarEstadisticas -or $LimpiarDatos -or $TodoCompleto)) {
        Show-Help
    }
}

# Ejecutar función principal
Main
