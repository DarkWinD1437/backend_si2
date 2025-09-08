# Script de Prueba de Auditoria en PowerShell

# Configuracion
$baseUrl = "http://127.0.0.1:8000/api"
$email = "admin@example.com"
$password = "admin123"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "SISTEMA DE AUDITORIA BASICA - PRUEBAS" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Funcion para hacer requests HTTP
function Invoke-ApiRequest {
    param(
        [string]$Method,
        [string]$Url,
        [hashtable]$Headers = @{},
        [string]$Body = $null
    )
    
    try {
        $defaultHeaders = @{
            "Content-Type" = "application/json"
        }
        
        # Combinar headers
        $allHeaders = $defaultHeaders + $Headers
        
        if ($Body) {
            $response = Invoke-RestMethod -Uri $Url -Method $Method -Headers $allHeaders -Body $Body
        } else {
            $response = Invoke-RestMethod -Uri $Url -Method $Method -Headers $allHeaders
        }
        
        return @{
            Success = $true
            Data = $response
            StatusCode = 200
        }
    }
    catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
            StatusCode = $_.Exception.Response.StatusCode.value__
        }
    }
}

# Test 1: Login Fallido
Write-Host "1. Probando LOGIN FALLIDO..." -ForegroundColor Yellow
$loginFailData = @{
    email = $email
    password = "password_incorrecto"
} | ConvertTo-Json

$result = Invoke-ApiRequest -Method "POST" -Url "$baseUrl/token/" -Body $loginFailData

if (-not $result.Success) {
    Write-Host "   [OK] Login fallo como esperado (genera log de auditoria)" -ForegroundColor Green
    Write-Host "   Error: $($result.Error)" -ForegroundColor Gray
} else {
    Write-Host "   [ERROR] Login no deberia haber sido exitoso" -ForegroundColor Red
}

Write-Host ""

# Test 2: Login Exitoso
Write-Host "2. Probando LOGIN EXITOSO..." -ForegroundColor Yellow
$loginData = @{
    email = $email
    password = $password
} | ConvertTo-Json

$loginResult = Invoke-ApiRequest -Method "POST" -Url "$baseUrl/token/" -Body $loginData

if ($loginResult.Success) {
    $token = $loginResult.Data.access
    Write-Host "   [OK] Login exitoso" -ForegroundColor Green
    Write-Host "   Token obtenido: $($token.Substring(0, 50))..." -ForegroundColor Gray
} else {
    Write-Host "   [ERROR] Login fallo inesperadamente" -ForegroundColor Red
    Write-Host "   Error: $($loginResult.Error)" -ForegroundColor Gray
    return
}

Write-Host ""

# Test 3: Crear Usuario
Write-Host "3. Probando CREAR USUARIO..." -ForegroundColor Yellow
$newUserData = @{
    email = "usuario_prueba_$(Get-Random)@example.com"
    password = "password123"
    first_name = "Usuario"
    last_name = "Prueba"
} | ConvertTo-Json

$headers = @{
    "Authorization" = "Bearer $token"
}

$createResult = Invoke-ApiRequest -Method "POST" -Url "$baseUrl/usuarios/" -Headers $headers -Body $newUserData

if ($createResult.Success) {
    Write-Host "   [OK] Usuario creado exitosamente" -ForegroundColor Green
    Write-Host "   ID del usuario: $($createResult.Data.id)" -ForegroundColor Gray
    $userId = $createResult.Data.id
} else {
    Write-Host "   [ERROR] Error creando usuario" -ForegroundColor Red
    Write-Host "   Error: $($createResult.Error)" -ForegroundColor Gray
}

Write-Host ""

# Test 4: Actualizar Usuario (si se creo)
if ($userId) {
    Write-Host "4. Probando ACTUALIZAR USUARIO..." -ForegroundColor Yellow
    $updateData = @{
        first_name = "Nombre Actualizado"
        last_name = "Apellido Actualizado"
    } | ConvertTo-Json

    $updateResult = Invoke-ApiRequest -Method "PATCH" -Url "$baseUrl/usuarios/$userId/" -Headers $headers -Body $updateData

    if ($updateResult.Success) {
        Write-Host "   [OK] Usuario actualizado exitosamente" -ForegroundColor Green
    } else {
        Write-Host "   [ERROR] Error actualizando usuario" -ForegroundColor Red
        Write-Host "   Error: $($updateResult.Error)" -ForegroundColor Gray
    }
    Write-Host ""
}

# Test 5: Consultar Logs de Auditoria
Write-Host "5. Consultando LOGS DE AUDITORIA..." -ForegroundColor Yellow
$logsResult = Invoke-ApiRequest -Method "GET" -Url "$baseUrl/auditoria/logs/" -Headers $headers

if ($logsResult.Success) {
    Write-Host "   [OK] Logs obtenidos exitosamente" -ForegroundColor Green
    Write-Host "   Total de logs: $($logsResult.Data.count)" -ForegroundColor Gray
    
    Write-Host "   Ultimos 5 logs:" -ForegroundColor Gray
    $logsResult.Data.results | Select-Object -First 5 | ForEach-Object {
        Write-Host "      - $($_.timestamp) - $($_.usuario_email) - $($_.accion_display)" -ForegroundColor White
    }
} else {
    Write-Host "   [ERROR] Error obteniendo logs" -ForegroundColor Red
    Write-Host "   Error: $($logsResult.Error)" -ForegroundColor Gray
}

Write-Host ""

# Test 6: Consultar Estadisticas
Write-Host "6. Consultando ESTADISTICAS..." -ForegroundColor Yellow
$statsResult = Invoke-ApiRequest -Method "GET" -Url "$baseUrl/auditoria/logs/estadisticas/" -Headers $headers

if ($statsResult.Success) {
    Write-Host "   [OK] Estadisticas obtenidas exitosamente" -ForegroundColor Green
    Write-Host "   Total de eventos: $($statsResult.Data.total_eventos)" -ForegroundColor Gray
    Write-Host "   Periodo: $($statsResult.Data.periodo_dias) dias" -ForegroundColor Gray
    
    Write-Host "   Eventos por accion:" -ForegroundColor Gray
    $statsResult.Data.estadisticas_por_accion | ForEach-Object {
        Write-Host "      - $($_.accion): $($_.total)" -ForegroundColor White
    }
} else {
    Write-Host "   [ERROR] Error obteniendo estadisticas" -ForegroundColor Red
    Write-Host "   Error: $($statsResult.Error)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "PRUEBAS COMPLETADAS" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Para ver los logs en el admin de Django:" -ForegroundColor Yellow
Write-Host "   URL: http://127.0.0.1:8000/admin/auditoria/auditorialog/" -ForegroundColor White
Write-Host "   Usuario: admin@example.com" -ForegroundColor White
Write-Host "   Password: admin123" -ForegroundColor White
Write-Host ""
Write-Host "Para usar Swagger UI:" -ForegroundColor Yellow
Write-Host "   URL: http://127.0.0.1:8000/api/swagger/" -ForegroundColor White
Write-Host ""
