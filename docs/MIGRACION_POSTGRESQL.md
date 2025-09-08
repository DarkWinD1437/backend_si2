# Guía de Migración de SQLite a PostgreSQL

## Cooperativa SI2 - Sistema de Auditoría y Validaciones

### 📋 Descripción

Esta guía te ayudará a migrar tu aplicación Django desde SQLite a PostgreSQL, manteniendo todos los datos de auditoría y configuraciones de validación.

### 🛠️ Requisitos Previos

1. **PostgreSQL instalado** (versión 12 o superior)
2. **Python 3.8+** con entorno virtual
3. **Acceso administrativo** a PostgreSQL

### 📦 Instalación de PostgreSQL

#### Windows:
```powershell
# Descargar desde: https://www.postgresql.org/download/windows/
# O usar Chocolatey:
choco install postgresql

# O usar winget:
winget install PostgreSQL.PostgreSQL
```

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### macOS:
```bash
# Usar Homebrew:
brew install postgresql
brew services start postgresql
```

### 🔧 Configuración Paso a Paso

#### 1. Instalar Dependencias Python

```powershell
# Activar entorno virtual
.venv\Scripts\activate

# Instalar psycopg2 para PostgreSQL
pip install psycopg2-binary==2.9.9

# Instalar todas las dependencias actualizadas
pip install -r requirements.txt
```

#### 2. Configurar PostgreSQL

**Opción A: Usar el script automatizado**
```powershell
# Ejecutar configuración completa
.\scripts\setup_postgresql.ps1 -All

# O paso a paso:
.\scripts\setup_postgresql.ps1 -Setup      # Configurar DB
.\scripts\setup_postgresql.ps1 -Migrate    # Migraciones
.\scripts\setup_postgresql.ps1 -LoadData   # Datos iniciales
```

**Opción B: Configuración manual**

1. **Acceder a PostgreSQL:**
```sql
-- Como usuario postgres
psql -U postgres

-- Crear base de datos
CREATE DATABASE cooperativa_si2
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    TEMPLATE = template0;

-- Conectar a la nueva base de datos
\c cooperativa_si2;

-- Crear extensiones útiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";
```

2. **Configurar archivo .env:**
```env
# Base de datos PostgreSQL
DATABASE_ENGINE=django.db.backends.postgresql
DATABASE_NAME=cooperativa_si2
DATABASE_USER=postgres
DATABASE_PASSWORD=tu_password_aqui
DATABASE_HOST=localhost
DATABASE_PORT=5432
```

#### 3. Migrar Datos Existentes (Si tienes datos en SQLite)

**Opción A: Exportar/Importar con Django**
```powershell
# 1. Hacer backup de datos SQLite
python manage.py dumpdata --natural-foreign --natural-primary > backup_sqlite.json

# 2. Cambiar a PostgreSQL en settings.py
# 3. Crear nuevas migraciones
python manage.py makemigrations

# 4. Aplicar migraciones a PostgreSQL
python manage.py migrate

# 5. Cargar datos (puede requerir ajustes)
python manage.py loaddata backup_sqlite.json
```

**Opción B: Migración Limpia**
```powershell
# 1. Configurar PostgreSQL
# 2. Ejecutar migraciones desde cero
python manage.py makemigrations
python manage.py migrate

# 3. Crear nuevos datos de prueba
python manage.py test_validaciones --crear-datos-prueba
```

#### 4. Verificar Migración

```powershell
# Verificar configuración
python manage.py check

# Verificar conexión a DB
python manage.py shell -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT version();')
    print('PostgreSQL:', cursor.fetchone()[0])
"

# Verificar modelos
python manage.py shell -c "
from apps.usuarios.models import User
from apps.auditoria.models import AuditoriaLog
print('Usuarios:', User.objects.count())
print('Logs de auditoría:', AuditoriaLog.objects.count())
"
```

### 🎯 Ventajas de PostgreSQL

#### 1. **Mejores Constraints y Validaciones**
```sql
-- PostgreSQL soporta constraints avanzados
ALTER TABLE usuarios_documentoidentidad 
ADD CONSTRAINT check_ci_length 
CHECK (
    CASE 
        WHEN tipo_documento = 'CI' THEN length(numero_documento) >= 7 AND length(numero_documento) <= 8
        WHEN tipo_documento = 'NIT' THEN length(numero_documento) = 13
        ELSE true
    END
);
```

#### 2. **Mejor Performance para Auditoría**
```sql
-- Índices optimizados para consultas de auditoría
CREATE INDEX idx_auditoria_usuario_fecha 
ON auditoria_auditorialog(usuario_id, fecha_hora);

CREATE INDEX idx_auditoria_accion_fecha 
ON auditoria_auditorialog(accion, fecha_hora);

-- Búsqueda de texto completo
CREATE INDEX idx_auditoria_search 
ON auditoria_auditorialog 
USING gin(to_tsvector('spanish', detalles));
```

#### 3. **Transacciones ACID Completas**
```python
# Con PostgreSQL, las transacciones son más robustas
from django.db import transaction

@transaction.atomic
def crear_usuario_con_auditoria(datos):
    # Todo se ejecuta en una transacción
    user = User.objects.create(**datos)
    documento = DocumentoIdentidad.objects.create(**doc_datos)
    user.documento_identidad = documento
    user.save()
    # Si falla algo, todo se revierte automáticamente
```

### 📊 Optimizaciones Específicas

#### 1. **Configuración de Conexiones**
```python
# En settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'cooperativa_si2',
        'USER': 'postgres',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 300,  # Reutilizar conexiones
        'ATOMIC_REQUESTS': True,  # Transacciones automáticas
        'OPTIONS': {
            'client_encoding': 'UTF8',
        },
    }
}
```

#### 2. **Índices para Performance**
```python
# En modelos, usar índices PostgreSQL
class AuditoriaLog(models.Model):
    # ... campos ...
    
    class Meta:
        indexes = [
            models.Index(fields=['usuario', 'fecha_hora']),
            models.Index(fields=['accion', 'fecha_hora']),
            models.Index(fields=['ip_address']),
        ]
```

#### 3. **Configuración de Logging SQL**
```python
# En settings.py para debug
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'sql_file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/sql.log',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['sql_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### 🧪 Testing con PostgreSQL

```powershell
# Ejecutar tests de validaciones
python manage.py test_validaciones --probar-validaciones

# Ver estadísticas
python manage.py test_validaciones --mostrar-estadisticas

# Limpiar datos de prueba
python manage.py test_validaciones --limpiar-datos
```

### 🔍 Monitoreo y Mantenimiento

#### 1. **Consultas de Auditoría Optimizadas**
```sql
-- Top usuarios más activos
SELECT 
    u.email,
    COUNT(*) as total_acciones,
    COUNT(DISTINCT DATE(al.fecha_hora)) as dias_activos
FROM auditoria_auditorialog al
JOIN usuarios_user u ON al.usuario_id = u.id
WHERE al.fecha_hora >= NOW() - INTERVAL '30 days'
GROUP BY u.email
ORDER BY total_acciones DESC
LIMIT 10;

-- Estadísticas de acciones por día
SELECT 
    DATE(fecha_hora) as fecha,
    accion,
    COUNT(*) as total
FROM auditoria_auditorialog
WHERE fecha_hora >= NOW() - INTERVAL '7 days'
GROUP BY DATE(fecha_hora), accion
ORDER BY fecha DESC, total DESC;
```

#### 2. **Backup y Restore**
```powershell
# Backup
pg_dump -U postgres -h localhost cooperativa_si2 > backup_$(Get-Date -Format "yyyyMMdd_HHmmss").sql

# Restore
psql -U postgres -h localhost -d cooperativa_si2 -f backup_20241208_143000.sql
```

### 🚨 Troubleshooting

#### Problemas Comunes:

1. **Error de conexión:**
```
FATAL: password authentication failed for user "postgres"
```
**Solución:** Verificar password en .env y pg_hba.conf

2. **Error de encoding:**
```
UnicodeDecodeError: 'utf-8' codec can't decode
```
**Solución:** Configurar encoding UTF8 en DATABASE_OPTIONS

3. **Migraciones lentas:**
```
Migration is taking too long
```
**Solución:** Usar `--fake-initial` para migraciones iniciales

### 📈 Resultados Esperados

Con PostgreSQL configurado correctamente, deberías tener:

- ✅ **Validaciones robustas** de CI/NIT/Pasaporte
- ✅ **Auditoría completa** de todas las operaciones
- ✅ **Performance optimizada** para consultas complejas
- ✅ **Integridad de datos** garantizada con constraints
- ✅ **Escalabilidad** para crecimiento futuro

### 🎯 Próximos Pasos

1. **Configurar PostgreSQL** con el script automatizado
2. **Migrar datos** desde SQLite (si aplica)
3. **Probar validaciones** con datos reales
4. **Configurar backups** automáticos
5. **Optimizar consultas** según uso real
