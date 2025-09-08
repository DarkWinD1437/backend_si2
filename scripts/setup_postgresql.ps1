# Script para configurar PostgreSQL y migrar la aplicación
# Configuración de PostgreSQL para Cooperativa SI2

param(
    [switch]$Install,
    [switch]$Setup,
    [switch]$Migrate,
    [switch]$LoadData,
    [switch]$All,
    [string]$PostgresPath = "C:\Program Files\PostgreSQL\16\bin",
    [string]$Host = "localhost",
    [string]$Port = "5432",
    [string]$Username = "postgres",
    [string]$Database = "cooperativa_si2"
)

# Colores para output
function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

# Verificar si PostgreSQL está instalado
function Test-PostgreSQL {
    try {
        if (Test-Path "$PostgresPath\psql.exe") {
            Write-Success "PostgreSQL encontrado en: $PostgresPath"
            return $true
        } else {
            Write-Error "PostgreSQL no encontrado en: $PostgresPath"
            return $false
        }
    } catch {
        Write-Error "Error verificando PostgreSQL: $($_.Exception.Message)"
        return $false
    }
}

# Instalar dependencias Python
function Install-Dependencies {
    Write-Info "Instalando dependencias de Python..."
    
    try {
        # Activar entorno virtual si existe
        if (Test-Path ".venv\Scripts\activate.ps1") {
            & .\.venv\Scripts\activate.ps1
            Write-Success "Entorno virtual activado"
        }
        
        # Instalar psycopg2-binary
        pip install psycopg2-binary==2.9.9
        Write-Success "psycopg2-binary instalado"
        
        # Instalar todas las dependencias
        pip install -r requirements.txt
        Write-Success "Dependencias instaladas desde requirements.txt"
        
    } catch {
        Write-Error "Error instalando dependencias: $($_.Exception.Message)"
        return $false
    }
    
    return $true
}

# Configurar base de datos PostgreSQL
function Setup-Database {
    Write-Info "Configurando base de datos PostgreSQL..."
    
    if (-not (Test-PostgreSQL)) {
        Write-Error "PostgreSQL no está disponible. Instale PostgreSQL primero."
        return $false
    }
    
    try {
        $env:PGPASSWORD = Read-Host "Ingrese la contraseña de PostgreSQL" -AsSecureString
        $env:PGPASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($env:PGPASSWORD))
        
        # Ejecutar script SQL
        $sqlScript = "scripts\setup_postgresql.sql"
        if (Test-Path $sqlScript) {
            Write-Info "Ejecutando script de configuración..."
            & "$PostgresPath\psql.exe" -h $Host -p $Port -U $Username -f $sqlScript
            Write-Success "Base de datos configurada exitosamente"
        } else {
            Write-Error "Script SQL no encontrado: $sqlScript"
            return $false
        }
        
    } catch {
        Write-Error "Error configurando base de datos: $($_.Exception.Message)"
        return $false
    }
    
    return $true
}

# Ejecutar migraciones Django
function Run-Migrations {
    Write-Info "Ejecutando migraciones de Django..."
    
    try {
        # Verificar configuración
        Write-Info "Verificando configuración de Django..."
        python manage.py check
        
        # Mostrar migraciones pendientes
        Write-Info "Migraciones pendientes:"
        python manage.py showmigrations
        
        # Crear migraciones si es necesario
        Write-Info "Creando nuevas migraciones..."
        python manage.py makemigrations
        
        # Aplicar migraciones
        Write-Info "Aplicando migraciones..."
        python manage.py migrate
        
        Write-Success "Migraciones aplicadas exitosamente"
        
    } catch {
        Write-Error "Error en migraciones: $($_.Exception.Message)"
        return $false
    }
    
    return $true
}

# Cargar datos iniciales
function Load-InitialData {
    Write-Info "Cargando datos iniciales..."
    
    try {
        # Crear superusuario
        Write-Info "Creando superusuario..."
        python manage.py shell -c "
from django.contrib.auth import get_user_model
from apps.usuarios.document_models import DocumentoIdentidad, TipoDocumento

User = get_user_model()

# Crear documento para admin
doc_admin = DocumentoIdentidad.objects.create(
    tipo_documento=TipoDocumento.CI,
    numero_documento='12345678',
    extension='LP'
)

# Crear superusuario
if not User.objects.filter(email='admin@cooperativa.com').exists():
    admin = User.objects.create_superuser(
        email='admin@cooperativa.com',
        password='admin123',
        first_name='Admin',
        last_name='Sistema',
        username='admin'
    )
    admin.documento_identidad = doc_admin
    admin.save()
    print('Superusuario creado: admin@cooperativa.com / admin123')
else:
    print('Superusuario ya existe')
"
        
        # Ejecutar comando de test de validaciones
        Write-Info "Creando datos de prueba..."
        python manage.py test_validaciones --crear-datos-prueba
        
        Write-Success "Datos iniciales cargados"
        
    } catch {
        Write-Error "Error cargando datos: $($_.Exception.Message)"
        return $false
    }
    
    return $true
}

# Verificar conexión a PostgreSQL
function Test-DatabaseConnection {
    Write-Info "Verificando conexión a la base de datos..."
    
    try {
        python manage.py shell -c "
from django.db import connection
from django.core.management.color import no_style

try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT version();')
        version = cursor.fetchone()[0]
        print(f'✅ Conexión exitosa a PostgreSQL: {version}')
        
        cursor.execute('SELECT current_database();')
        db_name = cursor.fetchone()[0]
        print(f'📊 Base de datos actual: {db_name}')
        
        # Mostrar tablas
        cursor.execute(\"\"\"
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            ORDER BY tablename;
        \"\"\")
        tables = cursor.fetchall()
        print(f'📋 Tablas en la base de datos: {len(tables)}')
        for table in tables[:10]:  # Mostrar primeras 10
            print(f'   - {table[0]}')
        if len(tables) > 10:
            print(f'   ... y {len(tables) - 10} más')
            
except Exception as e:
    print(f'❌ Error de conexión: {e}')
    exit(1)
"
        Write-Success "Conexión a base de datos verificada"
        
    } catch {
        Write-Error "Error verificando conexión: $($_.Exception.Message)"
        return $false
    }
    
    return $true
}

# Función principal
function Main {
    Write-Info "=== Configuración PostgreSQL para Cooperativa SI2 ==="
    Write-Info "Directorio actual: $(Get-Location)"
    
    # Verificar que estamos en el directorio correcto
    if (-not (Test-Path "manage.py")) {
        Write-Error "No se encontró manage.py. Ejecute desde el directorio raíz del proyecto."
        exit 1
    }
    
    $success = $true
    
    if ($Install -or $All) {
        Write-Info "`n--- Instalando dependencias ---"
        $success = $success -and (Install-Dependencies)
    }
    
    if ($Setup -or $All) {
        Write-Info "`n--- Configurando base de datos ---"
        $success = $success -and (Setup-Database)
    }
    
    if ($Migrate -or $All) {
        Write-Info "`n--- Ejecutando migraciones ---"
        $success = $success -and (Run-Migrations)
        
        if ($success) {
            $success = $success -and (Test-DatabaseConnection)
        }
    }
    
    if ($LoadData -or $All) {
        Write-Info "`n--- Cargando datos iniciales ---"
        $success = $success -and (Load-InitialData)
    }
    
    if ($success) {
        Write-Success "`n🎉 ¡Configuración completada exitosamente!"
        Write-Info "`nPróximos pasos:"
        Write-Info "1. Verificar que el servidor Django funcione: python manage.py runserver"
        Write-Info "2. Acceder al admin: http://localhost:8000/admin/"
        Write-Info "3. Probar las APIs: http://localhost:8000/api/schema/swagger-ui/"
        Write-Info "4. Verificar auditoría: http://localhost:8000/api/auditoria/"
    } else {
        Write-Error "`n💥 La configuración falló. Revise los errores anteriores."
        exit 1
    }
}

# Mostrar ayuda si no se especifican parámetros
if (-not ($Install -or $Setup -or $Migrate -or $LoadData -or $All)) {
    Write-Info "Uso del script de configuración PostgreSQL:"
    Write-Info ""
    Write-Info "Parámetros disponibles:"
    Write-Info "  -Install    : Instalar dependencias Python"
    Write-Info "  -Setup      : Configurar base de datos PostgreSQL"
    Write-Info "  -Migrate    : Ejecutar migraciones Django"
    Write-Info "  -LoadData   : Cargar datos iniciales"
    Write-Info "  -All        : Ejecutar todos los pasos"
    Write-Info ""
    Write-Info "Ejemplos:"
    Write-Info "  .\scripts\setup_postgresql.ps1 -All"
    Write-Info "  .\scripts\setup_postgresql.ps1 -Install -Migrate"
    Write-Info "  .\scripts\setup_postgresql.ps1 -Setup -Username postgres -Database cooperativa_si2"
    Write-Info ""
    Write-Info "Parámetros opcionales:"
    Write-Info "  -PostgresPath : Ruta de instalación de PostgreSQL (default: C:\Program Files\PostgreSQL\16\bin)"
    Write-Info "  -Host         : Host de PostgreSQL (default: localhost)"
    Write-Info "  -Port         : Puerto de PostgreSQL (default: 5432)"
    Write-Info "  -Username     : Usuario de PostgreSQL (default: postgres)"
    Write-Info "  -Database     : Nombre de la base de datos (default: cooperativa_si2)"
    exit 0
}

# Ejecutar función principal
Main
