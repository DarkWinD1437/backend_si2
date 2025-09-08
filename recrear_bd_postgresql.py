#!/usr/bin/env python
"""
Script para recrear la base de datos PostgreSQL con codificación UTF-8
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

def recrear_base_datos():
    """Recrear la base de datos con codificación UTF-8"""
    
    # Parámetros de conexión
    conn_params = {
        'host': 'localhost',
        'port': '5432',
        'user': 'postgres',
        'password': '123456',
        'database': 'postgres'  # Conectar a la BD por defecto
    }
    
    try:
        print("🔗 Conectando a PostgreSQL...")
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Terminar todas las conexiones a la base de datos
        print("🔄 Terminando conexiones activas...")
        cursor.execute("""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = 'cooperativa_db'
            AND pid <> pg_backend_pid()
        """)
        
        # Verificar si la base de datos existe
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            ('cooperativa_db',)
        )
        
        if cursor.fetchone():
            print("🗑️ Eliminando base de datos existente...")
            cursor.execute("DROP DATABASE cooperativa_db")
            print("✅ Base de datos eliminada")
        
        # Crear nueva base de datos con UTF-8
        print("🏗️ Creando nueva base de datos con UTF-8...")
        cursor.execute("""
            CREATE DATABASE cooperativa_db
            WITH 
            TEMPLATE = template0
            OWNER = postgres
            ENCODING = 'UTF8'
            LC_COLLATE = 'C'
            LC_CTYPE = 'C'
            TABLESPACE = pg_default
            CONNECTION LIMIT = -1
        """)
        
        print("✅ Base de datos 'cooperativa_db' creada exitosamente con UTF-8")
        
        # Verificar la codificación
        cursor.execute(
            "SELECT pg_encoding_to_char(encoding) FROM pg_database WHERE datname = %s",
            ('cooperativa_db',)
        )
        encoding = cursor.fetchone()[0]
        print(f"📝 Codificación verificada: {encoding}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Error de PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

def probar_conexion_django():
    """Probar conexión desde Django después de recrear la BD"""
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()
        
        from django.db import connection
        
        print("🔗 Probando conexión desde Django...")
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"✅ Django conectado exitosamente")
            print(f"📊 PostgreSQL: {version.split(',')[0]}")
            
            # Verificar codificación
            cursor.execute("SHOW server_encoding")
            server_enc = cursor.fetchone()[0]
            print(f"🔤 Codificación servidor: {server_enc}")
            
            cursor.execute("SHOW client_encoding")  
            client_enc = cursor.fetchone()[0]
            print(f"🔤 Codificación cliente: {client_enc}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error conectando desde Django: {e}")
        return False

if __name__ == "__main__":
    print("🚀 RECREANDO BASE DE DATOS POSTGRESQL")
    print("=" * 50)
    
    if recrear_base_datos():
        print("\n🎉 Base de datos recreada exitosamente!")
        
        if probar_conexion_django():
            print("\n✅ Todo listo para ejecutar las migraciones")
            print("Ejecuta: python manage.py migrate")
        else:
            print("\n⚠️ Hay problemas con Django, revisa la configuración")
    else:
        print("\n❌ No se pudo recrear la base de datos")
