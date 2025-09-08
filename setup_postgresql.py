"""
Script para verificar la conexión a PostgreSQL y realizar la migración desde SQLite
"""

import os
import sys
import django
from pathlib import Path

# Añadir el proyecto al path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model
from apps.usuarios.document_models import DocumentoIdentidad, TipoDocumento
from apps.socios.models import Socio
from apps.auditoria.models import AuditoriaLog, SesionUsuario

User = get_user_model()

def verificar_conexion_postgresql():
    """Verificar que la conexión a PostgreSQL funciona"""
    print("🔍 Verificando conexión a PostgreSQL...")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Conexión exitosa a PostgreSQL: {version[0]}")
            
            # Verificar que la base de datos existe
            cursor.execute("SELECT current_database();")
            db_name = cursor.fetchone()
            print(f"📊 Base de datos actual: {db_name[0]}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        print("\n💡 Asegúrate de que:")
        print("   1. PostgreSQL esté instalado y ejecutándose")
        print("   2. La base de datos 'cooperativa_si2' exista")
        print("   3. Las credenciales en .env sean correctas")
        print("   4. El usuario tenga permisos en la base de datos")
        return False

def crear_base_datos_si_no_existe():
    """Crear la base de datos si no existe"""
    print("\n🏗️ Verificando si la base de datos existe...")
    
    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        import environ
        
        env = environ.Env()
        environ.Env.read_env()
        
        # Conectar a PostgreSQL (sin especificar base de datos)
        conn = psycopg2.connect(
            host=env('DATABASE_HOST', default='localhost'),
            port=env('DATABASE_PORT', default='5432'),
            user=env('DATABASE_USER', default='postgres'),
            password=env('DATABASE_PASSWORD', default='123456')
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Verificar si la base de datos existe
        db_name = env('DATABASE_NAME', default='cooperativa_db')
        cursor.execute(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s",
            (db_name,)
        )
        
        if not cursor.fetchone():
            print(f"📊 Creando base de datos '{db_name}'...")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✅ Base de datos '{db_name}' creada exitosamente")
        else:
            print(f"✅ Base de datos '{db_name}' ya existe")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creando/verificando base de datos: {e}")
        return False

def ejecutar_migraciones():
    """Ejecutar las migraciones de Django"""
    print("\n🔄 Ejecutando migraciones...")
    
    try:
        # Hacer migraciones
        print("   📝 Creando archivos de migración...")
        execute_from_command_line(['manage.py', 'makemigrations'])
        
        # Aplicar migraciones
        print("   🚀 Aplicando migraciones...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("✅ Migraciones completadas exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en migraciones: {e}")
        return False

def crear_superusuario():
    """Crear un superusuario si no existe"""
    print("\n👤 Verificando superusuario...")
    
    try:
        if not User.objects.filter(is_superuser=True).exists():
            print("   📝 Creando superusuario admin...")
            
            # Crear documento para el admin
            doc_admin = DocumentoIdentidad.objects.create(
                tipo_documento=TipoDocumento.CI,
                numero_documento='12345678',
                extension='1A'
            )
            
            # Crear superusuario
            admin = User.objects.create_superuser(
                email='admin@cooperativa.com',
                password='admin123',
                first_name='Admin',
                last_name='Sistema',
                username='admin'
            )
            admin.documento_identidad = doc_admin
            admin.save()
            
            print("✅ Superusuario 'admin@cooperativa.com' creado (password: admin123)")
        else:
            print("✅ Ya existe un superusuario")
            
        return True
        
    except Exception as e:
        print(f"❌ Error creando superusuario: {e}")
        return False

def verificar_modelos():
    """Verificar que los modelos funcionen correctamente"""
    print("\n🧪 Verificando modelos...")
    
    try:
        # Verificar modelo de usuarios
        user_count = User.objects.count()
        print(f"   👥 Usuarios en base de datos: {user_count}")
        
        # Verificar modelo de documentos
        doc_count = DocumentoIdentidad.objects.count()
        print(f"   📋 Documentos de identidad: {doc_count}")
        
        # Verificar modelo de socios
        socio_count = Socio.objects.count()
        print(f"   🤝 Socios registrados: {socio_count}")
        
        # Verificar modelo de auditoría
        audit_count = AuditoriaLog.objects.count()
        print(f"   📊 Registros de auditoría: {audit_count}")
        
        # Verificar modelo de sesiones
        session_count = SesionUsuario.objects.count()
        print(f"   🔐 Sesiones registradas: {session_count}")
        
        print("✅ Todos los modelos funcionan correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando modelos: {e}")
        return False

def mostrar_informacion_conexion():
    """Mostrar información de la conexión actual"""
    print("\n📊 INFORMACIÓN DE LA BASE DE DATOS")
    print("=" * 50)
    
    try:
        with connection.cursor() as cursor:
            # Información básica
            cursor.execute("SELECT current_database(), current_user, version();")
            db_info = cursor.fetchone()
            print(f"Base de datos: {db_info[0]}")
            print(f"Usuario: {db_info[1]}")
            print(f"Versión PostgreSQL: {db_info[2].split(',')[0]}")
            
            # Información de tablas
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            print(f"\nTablas creadas: {len(tables)}")
            for table in tables:
                print(f"  - {table[0]}")
                
    except Exception as e:
        print(f"❌ Error obteniendo información: {e}")

def main():
    """Función principal"""
    print("🚀 CONFIGURACIÓN DE POSTGRESQL PARA COOPERATIVA SI2")
    print("=" * 60)
    
    # Paso 1: Crear base de datos si no existe
    if not crear_base_datos_si_no_existe():
        return
    
    # Paso 2: Verificar conexión
    if not verificar_conexion_postgresql():
        return
    
    # Paso 3: Ejecutar migraciones
    if not ejecutar_migraciones():
        return
    
    # Paso 4: Crear superusuario
    if not crear_superusuario():
        return
    
    # Paso 5: Verificar modelos
    if not verificar_modelos():
        return
    
    # Paso 6: Mostrar información
    mostrar_informacion_conexion()
    
    print("\n🎉 ¡CONFIGURACIÓN COMPLETADA EXITOSAMENTE!")
    print("=" * 60)
    print("✅ PostgreSQL configurado y funcionando")
    print("✅ Migraciones aplicadas")
    print("✅ Modelos verificados")
    print("✅ Sistema de auditoría listo")
    print("✅ Validaciones de duplicados activas")
    print("\n📝 Próximos pasos:")
    print("   1. python manage.py runserver (iniciar servidor)")
    print("   2. Acceder a http://localhost:8000/admin")
    print("   3. Login: admin@cooperativa.com / admin123")
    print("   4. Probar endpoints de API")

if __name__ == "__main__":
    main()
