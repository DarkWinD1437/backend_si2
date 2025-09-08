# Validación de Duplicados CI/NIT - Cooperativa SI2

## Descripción General

Este sistema previene la duplicación de documentos de identidad (CI, NIT, Pasaporte) en el registro de usuarios y socios de la cooperativa.

## Características Implementadas

### 1. Modelo de Documentos de Identidad
- **Ubicación**: `apps/usuarios/document_models.py`
- **Modelos**: `DocumentoIdentidad`, `TipoDocumento`
- **Validaciones**:
  - Formato específico por tipo de documento
  - Unicidad de documentos activos
  - Longitud mínima y máxima según tipo

### 2. Integración con Modelos Existentes
- **Usuario**: Campo `documento_identidad` (ForeignKey)
- **Socio**: Referencia al documento del usuario asociado
- **Compatibilidad**: Campo `dni` mantenido para retrocompatibilidad

### 3. Validaciones de Serializers
- **Ubicación**: `apps/usuarios/validation_serializers.py`
- **Funcionalidades**:
  - Validación de email único
  - Validación de documento único
  - Formato específico por tipo de documento
  - Validación cruzada email + documento

### 4. Endpoints de API
- **Ubicación**: `apps/usuarios/validation_views.py`
- **Endpoints disponibles**:
  ```
  POST /api/usuarios/validacion/validar-duplicados/
  GET /api/usuarios/documentos/
  POST /api/usuarios/documentos/
  GET /api/usuarios/documentos/{id}/
  PUT /api/usuarios/documentos/{id}/
  DELETE /api/usuarios/documentos/{id}/
  GET /api/usuarios/documentos/estadisticas/
  ```

## Guía de Uso

### Opción 1: Comando de Administración (Recomendado)

#### Ejecutar pruebas completas:
```powershell
.\test_validaciones.ps1 -TodoCompleto
```

#### Comandos individuales:
```powershell
# Crear datos de prueba
python manage.py test_validaciones --crear-datos-prueba

# Probar validaciones
python manage.py test_validaciones --probar-validaciones

# Ver estadísticas
python manage.py test_validaciones --mostrar-estadisticas

# Limpiar datos de prueba
python manage.py test_validaciones --limpiar-datos
```

#### Usando PowerShell:
```powershell
# Ver ayuda
.\test_validaciones.ps1 -Ayuda

# Ejecutar solo validaciones
.\test_validaciones.ps1 -ProbarValidaciones

# Ver estadísticas
.\test_validaciones.ps1 -MostrarEstadisticas
```

### Opción 2: API REST

#### 1. Iniciar el servidor Django:
```powershell
python manage.py runserver
```

#### 2. Probar validaciones via API:

**Validar email:**
```powershell
$body = @{ email = "nuevo@example.com" } | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8000/api/usuarios/validacion/validar-duplicados/" -Method POST -Body $body -ContentType "application/json"
```

**Validar documento:**
```powershell
$body = @{
    tipo_documento = "CI"
    numero_documento = "12345678"
    extension_documento = "1A"
} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8000/api/usuarios/validacion/validar-duplicados/" -Method POST -Body $body -ContentType "application/json"
```

**Obtener estadísticas:**
```powershell
Invoke-WebRequest -Uri "http://localhost:8000/api/usuarios/documentos/estadisticas/" -Method GET
```

#### 3. Usando curl (alternativa):
```bash
# Validar email
curl -X POST http://localhost:8000/api/usuarios/validacion/validar-duplicados/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Validar documento
curl -X POST http://localhost:8000/api/usuarios/validacion/validar-duplicados/ \
  -H "Content-Type: application/json" \
  -d '{"tipo_documento": "CI", "numero_documento": "12345678", "extension_documento": "1A"}'
```

### Opción 3: Django Admin

1. Acceder al admin: `http://localhost:8000/admin/`
2. Navegar a **Usuarios > Documentos identidad**
3. Intentar crear documentos duplicados
4. Observar las validaciones en tiempo real

### Opción 4: Django Shell

```python
python manage.py shell

# En el shell:
from apps.usuarios.validation_serializers import ValidacionDuplicadosSerializer

# Probar validación
data = {
    'email': 'test@example.com',
    'tipo_documento': 'CI',
    'numero_documento': '12345678',
    'extension_documento': '1A'
}

serializer = ValidacionDuplicadosSerializer(data=data)
print(f"¿Es válido? {serializer.is_valid()}")
if not serializer.is_valid():
    print(f"Errores: {serializer.errors}")
```

## Tipos de Validación Implementados

### 1. Validación de Email
- **Regla**: Email único en toda la base de datos
- **Comportamiento**: Error si el email ya existe
- **Mensaje**: "Ya existe un usuario con este email"

### 2. Validación de Documento
- **Regla**: Documento único por tipo (considerando extensión para CI)
- **Formatos validados**:
  - **CI**: 7-8 dígitos + extensión 1-2 caracteres
  - **NIT**: 13 dígitos exactos
  - **Pasaporte**: 6-9 caracteres alfanuméricos
- **Comportamiento**: Error si el documento ya existe
- **Mensaje**: "Ya existe un documento de identidad con estos datos"

### 3. Validación de Formato
- **CI**: `^\d{7,8}$` para número, `^[A-Za-z0-9]{1,2}$` para extensión
- **NIT**: `^\d{13}$`
- **Pasaporte**: `^[A-Za-z0-9]{6,9}$`

### 4. Validación Cruzada
- Verifica email Y documento simultáneamente
- Proporciona información detallada de duplicados encontrados

## Respuestas de la API

### Éxito (HTTP 200):
```json
{
  "_validation_info": {
    "email_disponible": true,
    "documento_disponible": true,
    "documento_formato_valido": true
  }
}
```

### Error de Validación (HTTP 400):
```json
{
  "email": ["Ya existe un usuario con este email"],
  "numero_documento": ["Ya existe un documento de identidad con estos datos"],
  "extension_documento": ["Este campo es requerido para documentos CI"]
}
```

## Escenarios de Prueba

### Datos de Prueba Creados:
1. **Usuario CI**: `usuario.ci@example.com` - CI: 12345678-1A
2. **Usuario NIT**: `empresa.nit@example.com` - NIT: 1234567890123
3. **Socio**: Asociado al usuario CI

### Casos de Prueba:
1. ✅ Email nuevo válido
2. ❌ Email duplicado existente
3. ✅ Documento nuevo válido
4. ❌ Documento duplicado existente
5. ✅ Validación completa válida
6. ❌ Validación completa con duplicados
7. ❌ Formato de documento incorrecto

## Integración con Sistema Existente

### En Serializers de Usuario:
```python
from apps.usuarios.validation_serializers import ValidacionDuplicadosSerializer

# En tu serializer de creación de usuario:
def validate(self, attrs):
    # Validar duplicados antes de crear
    validation_data = {
        'email': attrs.get('email'),
        'tipo_documento': attrs.get('tipo_documento'),
        'numero_documento': attrs.get('numero_documento'),
        'extension_documento': attrs.get('extension_documento'),
    }
    
    validator = ValidacionDuplicadosSerializer(data=validation_data)
    validator.is_valid(raise_exception=True)
    
    return attrs
```

### En Views de Frontend:
```javascript
// Validar antes de enviar formulario
const validarDuplicados = async (email, tipoDoc, numeroDoc, extension) => {
    const response = await fetch('/api/usuarios/validacion/validar-duplicados/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email,
            tipo_documento: tipoDoc,
            numero_documento: numeroDoc,
            extension_documento: extension
        })
    });
    
    if (!response.ok) {
        const errors = await response.json();
        throw new Error(JSON.stringify(errors));
    }
    
    return await response.json();
};
```

## Consideraciones de Rendimiento

1. **Índices de Base de Datos**: Automáticamente creados para campos únicos
2. **Consultas Optimizadas**: Uso de `select_related` y `prefetch_related`
3. **Validación Temprana**: Evita procesamiento innecesario
4. **Cache**: Considerado para estadísticas frecuentes

## Mantenimiento y Monitoreo

### Comandos Útiles:
```python
# Ver documentos duplicados (si los hubiera)
python manage.py shell -c "
from apps.usuarios.document_models import DocumentoIdentidad
from django.db.models import Count
duplicados = DocumentoIdentidad.objects.values('tipo_documento', 'numero_documento', 'extension').annotate(count=Count('id')).filter(count__gt=1)
print('Duplicados encontrados:', list(duplicados))
"

# Estadísticas rápidas
python manage.py test_validaciones --mostrar-estadisticas
```

### Logs de Auditoría:
Las validaciones se registran automáticamente en el sistema de auditoría implementado previamente.

## Troubleshooting

### Error: "Comando test_validaciones no encontrado"
**Solución**: Verificar que existe el archivo `apps/usuarios/management/commands/test_validaciones.py`

### Error: "No module named 'apps.usuarios.validation_serializers'"
**Solución**: Verificar que el archivo `apps/usuarios/validation_serializers.py` existe

### Error de Migración
**Solución**: 
```powershell
python manage.py makemigrations usuarios
python manage.py migrate
```

### API devuelve 404
**Solución**: Verificar que las URLs están registradas en `apps/usuarios/urls.py`

## Próximos Pasos Sugeridos

1. **Frontend Integration**: Implementar validación en tiempo real en formularios
2. **Bulk Validation**: Endpoint para validar múltiples registros
3. **Export/Import**: Validación durante importación masiva de datos
4. **Reportes**: Dashboard de estadísticas de documentos
5. **Notificaciones**: Alertas de intentos de duplicación
