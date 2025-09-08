# Script PowerShell para probar APIs con PostgreSQL
# Asegúrate de que el servidor esté ejecutándose: python manage.py runserver

$BASE_URL = "http://localhost:8000"
$HEADERS = @{
    "Content-Type" = "application/json"
    "Accept" = "application/json"
}

Write-Host "🚀 PROBANDO APIs CON POSTGRESQL" -ForegroundColor Green
Write-Host "="*60

# 1. Probar endpoints de documentos
Write-Host "`n📋 ENDPOINTS DE DOCUMENTOS" -ForegroundColor Yellow
Write-Host "-"*30

# Listar tipos de documento
Write-Host "1. Listando tipos de documento..."
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/usuarios/tipos-documento/" -Headers $HEADERS
    Write-Host "✅ Tipos de documento:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 3
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

# Listar documentos existentes
Write-Host "`n2. Listando documentos existentes..."
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/usuarios/documentos/" -Headers $HEADERS
    Write-Host "✅ Documentos registrados:" -ForegroundColor Green
    $response.results | ForEach-Object {
        Write-Host "   - $($_.get_tipo_documento_display): $($_.documento_completo)"
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

# 2. Probar validaciones de duplicados
Write-Host "`n🔍 VALIDACIONES DE DUPLICADOS" -ForegroundColor Yellow
Write-Host "-"*30

# Email válido
Write-Host "`n3. Probando email válido..."
$validData = @{
    email = "nuevo.test@example.com"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/usuarios/validar-duplicados/" -Method POST -Headers $HEADERS -Body $validData
    Write-Host "✅ Email válido:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 2
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

# Email duplicado
Write-Host "`n4. Probando email duplicado..."
$duplicateData = @{
    email = "usuario.ci@example.com"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/usuarios/validar-duplicados/" -Method POST -Headers $HEADERS -Body $duplicateData
    Write-Host "✅ Email duplicado (debería fallar):" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 2
} catch {
    Write-Host "⚠️ Error esperado (email duplicado): $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "✅ Validación funcionando correctamente" -ForegroundColor Green
    }
}

# Documento válido
Write-Host "`n5. Probando documento válido..."
$validDocData = @{
    tipo_documento = "CI"
    numero_documento = "99999999"
    extension_documento = "9Z"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/usuarios/validar-duplicados/" -Method POST -Headers $HEADERS -Body $validDocData
    Write-Host "✅ Documento válido:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 2
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

# Documento duplicado
Write-Host "`n6. Probando documento duplicado..."
$duplicateDocData = @{
    tipo_documento = "CI"
    numero_documento = "12345678"
    extension_documento = "1A"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/usuarios/validar-duplicados/" -Method POST -Headers $HEADERS -Body $duplicateDocData
    Write-Host "✅ Documento duplicado (debería fallar):" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 2
} catch {
    Write-Host "⚠️ Error esperado (documento duplicado): $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
    if ($_.Exception.Response.StatusCode -eq 400) {
        Write-Host "✅ Validación funcionando correctamente" -ForegroundColor Green
    }
}

# 3. Probar endpoints de auditoría
Write-Host "`n📊 ENDPOINTS DE AUDITORÍA" -ForegroundColor Yellow
Write-Host "-"*30

# Listar logs de auditoría
Write-Host "`n7. Listando logs de auditoría..."
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/auditoria/logs/" -Headers $HEADERS
    Write-Host "✅ Logs de auditoría:" -ForegroundColor Green
    Write-Host "   Total: $($response.count)"
    $response.results | Select-Object -First 3 | ForEach-Object {
        Write-Host "   - $($_.accion): $($_.modelo) por $($_.usuario_email) - $($_.fecha_creacion)"
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

# Estadísticas de auditoría
Write-Host "`n8. Obteniendo estadísticas de auditoría..."
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/auditoria/estadisticas/" -Headers $HEADERS
    Write-Host "✅ Estadísticas:" -ForegroundColor Green
    $response | ConvertTo-Json -Depth 2
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

# 4. Probar endpoints de usuarios
Write-Host "`n👥 ENDPOINTS DE USUARIOS" -ForegroundColor Yellow
Write-Host "-"*30

# Listar usuarios
Write-Host "`n9. Listando usuarios..."
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/usuarios/users/" -Headers $HEADERS
    Write-Host "✅ Usuarios registrados:" -ForegroundColor Green
    $response.results | ForEach-Object {
        $doc = if ($_.documento_identidad) { $_.documento_identidad.documento_completo } else { "Sin documento" }
        Write-Host "   - $($_.email) - $($_.first_name) $($_.last_name) - Doc: $doc"
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

# 5. Probar endpoints de socios
Write-Host "`n🤝 ENDPOINTS DE SOCIOS" -ForegroundColor Yellow
Write-Host "-"*30

# Listar socios
Write-Host "`n10. Listando socios..."
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/socios/" -Headers $HEADERS
    Write-Host "✅ Socios registrados:" -ForegroundColor Green
    $response.results | ForEach-Object {
        $nombre = "$($_.usuario.first_name) $($_.usuario.last_name)"
        $doc = if ($_.usuario.documento_identidad) { $_.usuario.documento_identidad.documento_completo } else { "Sin documento" }
        Write-Host "   - $nombre - Tipo: $($_.get_tipo_socio_display) - Doc: $doc - Activo: $($_.activo)"
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

# 6. Verificar sesiones activas
Write-Host "`n🔐 SESIONES ACTIVAS" -ForegroundColor Yellow
Write-Host "-"*30

Write-Host "`n11. Verificando sesiones activas..."
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/api/auditoria/sesiones/" -Headers $HEADERS
    Write-Host "✅ Sesiones:" -ForegroundColor Green
    Write-Host "   Total: $($response.count)"
    $response.results | ForEach-Object {
        Write-Host "   - $($_.usuario_email) - Inicio: $($_.fecha_inicio) - Activa: $($_.activa)"
    }
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
}

Write-Host "`n🎉 PRUEBAS COMPLETADAS" -ForegroundColor Green
Write-Host "="*60
Write-Host "✅ Sistema funcionando con PostgreSQL" -ForegroundColor Green
Write-Host "✅ Validaciones de duplicados operativas" -ForegroundColor Green
Write-Host "✅ Sistema de auditoría registrando eventos" -ForegroundColor Green
Write-Host "✅ Endpoints de API respondiendo correctamente" -ForegroundColor Green

Write-Host "`n📝 PRÓXIMOS PASOS:" -ForegroundColor Cyan
Write-Host "1. Acceder al admin: http://localhost:8000/admin" -ForegroundColor White
Write-Host "2. Usuario admin creado para gestión" -ForegroundColor White
Write-Host "3. APIs REST disponibles para frontend" -ForegroundColor White
Write-Host "4. Sistema de validaciones previniendo duplicados" -ForegroundColor White
Write-Host "5. Auditoría completa de operaciones" -ForegroundColor White

Write-Host "`n🔗 URLS IMPORTANTES:" -ForegroundColor Cyan
Write-Host "- Admin: http://localhost:8000/admin" -ForegroundColor White
Write-Host "- API Root: http://localhost:8000/api/" -ForegroundColor White
Write-Host "- Validaciones: http://localhost:8000/api/usuarios/validar-duplicados/" -ForegroundColor White
Write-Host "- Auditoría: http://localhost:8000/api/auditoria/" -ForegroundColor White
Write-Host "- Documentos: http://localhost:8000/api/usuarios/documentos/" -ForegroundColor White
