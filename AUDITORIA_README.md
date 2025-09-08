# Sistema de Auditoría Básica - Django REST Framework

## 📋 Descripción

Este sistema de auditoría básica registra automáticamente las siguientes actividades:

- **Login/Logout**: Inicios y cierres de sesión de usuarios
- **CRUD de Usuarios**: Creación, actualización y eliminación de usuarios
- **Intentos de login fallidos**: Para detectar posibles ataques
- **Sesiones de usuarios**: Tracking de sesiones activas

## 🏗️ Arquitectura del Sistema

### Modelos Principales

1. **AuditoriaLog**: Registro principal de eventos de auditoría
2. **SesionUsuario**: Tracking de sesiones de usuarios
3. **TipoAccion**: Enumeración de tipos de acciones auditables

### Componentes

- **Signals**: Capturan automáticamente eventos de Django
- **Middleware**: Captura información del contexto HTTP
- **ViewSets**: API REST para consultar logs de auditoría
- **Commands**: Comandos de administración para gestionar la auditoría

## 🚀 Instalación y Configuración

### 1. Aplicación ya configurada en settings.py:

```python
INSTALLED_APPS = [
    # ... otras apps
    'apps.auditoria',
]

MIDDLEWARE = [
    # ... otros middlewares
    'apps.auditoria.middleware.AuditoriaMiddleware',
    # ... resto de middlewares
]
```

### 2. Migraciones aplicadas:

Los modelos de auditoría ya están migrados a la base de datos.

### 3. URLs configuradas:

La API de auditoría está disponible en: `http://localhost:8000/api/auditoria/`

## 📊 Endpoints de la API

### Logs de Auditoría

- **GET** `/api/auditoria/logs/` - Listar todos los logs (solo admin)
- **GET** `/api/auditoria/logs/estadisticas/` - Estadísticas de auditoría (solo admin)
- **GET** `/api/auditoria/logs/mis_logs/` - Logs del usuario actual

### Sesiones de Usuario

- **GET** `/api/auditoria/sesiones/` - Listar sesiones (solo admin)
- **GET** `/api/auditoria/sesiones/activas/` - Sesiones activas (solo admin)
- **GET** `/api/auditoria/sesiones/mis_sesiones/` - Sesiones del usuario actual

### Parámetros de Filtrado

Los endpoints soportan filtros:
- `accion`: Filtrar por tipo de acción (LOGIN, LOGOUT, CREATE, UPDATE, DELETE)
- `exito`: Filtrar por éxito/fallo de la acción
- `usuario`: Filtrar por usuario
- `search`: Búsqueda por email, IP o descripción

## 🧪 Cómo Probar el Sistema

### Opción 1: Swagger UI (Recomendado)

1. **Abrir Swagger**: http://127.0.0.1:8000/api/swagger/
2. **Obtener token**:
   - Usar endpoint `/api/token/`
   - Credenciales: `admin@example.com` / `admin123`
3. **Autorizar**: Copiar el token en "Authorize" con formato `Bearer <token>`
4. **Probar endpoints** de auditoría

### Opción 2: Script de Prueba

Ejecutar el script de prueba incluido:

```bash
# En Windows (desde la carpeta del proyecto)
test_auditoria.bat

# En Linux/Mac
chmod +x test_auditoria.sh
./test_auditoria.sh
```

### Opción 3: Admin de Django

1. **Ir al admin**: http://127.0.0.1:8000/admin/
2. **Login**: `admin@example.com` / `admin123`
3. **Ver sección "Auditoría"**:
   - Logs de Auditoría
   - Sesiones de Usuario

### Opción 4: Comandos de Administración

```bash
# Crear datos de prueba
python manage.py test_auditoria --crear-datos-prueba

# Ver estadísticas
python manage.py test_auditoria --mostrar-estadisticas

# Ver estadísticas de los últimos 7 días
python manage.py test_auditoria --mostrar-estadisticas --dias 7

# Limpiar logs antiguos (más de 90 días)
python manage.py test_auditoria --limpiar-logs --dias 90
```

## 📈 Ejemplos de Uso

### 1. Login Exitoso

```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

**Resultado**: Se crea un log con acción `LOGIN` y una sesión de usuario.

### 2. Login Fallido

```bash
curl -X POST http://127.0.0.1:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"wrong"}'
```

**Resultado**: Se crea un log con acción `LOGIN_FAILED`.

### 3. Crear Usuario

```bash
curl -X POST http://127.0.0.1:8000/api/usuarios/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"email":"nuevo@example.com","password":"pass123"}'
```

**Resultado**: Se crea un log con acción `CREATE`.

### 4. Consultar Logs

```bash
curl -X GET http://127.0.0.1:8000/api/auditoria/logs/ \
  -H "Authorization: Bearer <token>"
```

### 5. Ver Estadísticas

```bash
curl -X GET http://127.0.0.1:8000/api/auditoria/logs/estadisticas/ \
  -H "Authorization: Bearer <token>"
```

## 🔍 Información Capturada

### Para cada evento se registra:

- **Usuario**: Quien realizó la acción
- **Timestamp**: Cuándo ocurrió
- **Acción**: Tipo de acción (LOGIN, CREATE, etc.)
- **IP**: Dirección IP del usuario
- **User-Agent**: Navegador/cliente utilizado
- **Éxito/Fallo**: Si la acción fue exitosa
- **Datos**: Información antes/después para updates
- **Descripción**: Descripción legible de la acción

### Para sesiones se registra:

- **Usuario**: Propietario de la sesión
- **Session Key**: Identificador único de sesión
- **IP y User-Agent**: Información del cliente
- **Timestamps**: Inicio, último acceso, cierre
- **Estado**: Activa/Inactiva

## 🛡️ Consideraciones de Seguridad

1. **Acceso restringido**: Solo administradores pueden ver todos los logs
2. **Datos sensibles**: Las contraseñas nunca se almacenan en logs
3. **Detección de ataques**: Los intentos fallidos se registran con IP
4. **Limpieza automática**: Se recomienda limpiar logs antiguos regularmente

## 🔧 Personalización

### Agregar más modelos para auditar:

En `apps/auditoria/signals.py`, modificar la lista:

```python
modelos_auditados = [User, OtroModelo, ...]
```

### Cambiar tipos de acción:

En `apps/auditoria/models.py`, modificar `TipoAccion`:

```python
class TipoAccion(models.TextChoices):
    NUEVA_ACCION = 'NUEVA_ACCION', 'Nueva Acción'
```

### Personalizar filtros:

En `apps/auditoria/views.py`, modificar `filterset_fields`:

```python
filterset_fields = ['accion', 'exito', 'nuevo_campo']
```

## 📝 Logs de Ejemplo

```json
{
  "id": 1,
  "usuario_email": "admin@example.com",
  "direccion_ip": "127.0.0.1",
  "accion": "LOGIN",
  "accion_display": "Inicio de sesión",
  "descripcion": "Usuario admin@example.com inició sesión exitosamente",
  "timestamp": "2025-09-08T11:30:00Z",
  "exito": true
}
```

## 🚨 Monitoreo y Alertas

### Consultas útiles para monitoreo:

1. **Intentos fallidos en la última hora**:
   ```
   GET /api/auditoria/logs/?accion=LOGIN_FAILED&timestamp__gte=<hace_1_hora>
   ```

2. **Usuarios más activos**:
   ```
   GET /api/auditoria/logs/estadisticas/
   ```

3. **Sesiones sospechosas** (múltiples IPs):
   ```
   GET /api/auditoria/sesiones/?usuario=<user_id>
   ```

## 🎯 Próximos Pasos

Para expandir el sistema de auditoría:

1. **Notificaciones**: Alertas por email/SMS para eventos críticos
2. **Dashboard**: Interface visual para estadísticas
3. **Exportación**: Funcionalidad para exportar logs
4. **Geolocalización**: Determinar ubicación por IP
5. **Machine Learning**: Detección de patrones anómalos

---

## 📞 Soporte

Para dudas sobre el sistema de auditoría, revisar:
1. Los logs en `/admin/auditoria/`
2. Las estadísticas en la API
3. Los comandos de administración disponibles
