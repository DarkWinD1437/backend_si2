from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class Command(BaseCommand):
    help = 'Comando para probar la conexión a PostgreSQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-connection',
            action='store_true',
            help='Probar conexión básica a PostgreSQL',
        )
        parser.add_argument(
            '--create-database',
            action='store_true',
            help='Crear la base de datos si no existe',
        )
        parser.add_argument(
            '--show-info',
            action='store_true',
            help='Mostrar información de la conexión',
        )

    def handle(self, *args, **options):
        if options['test_connection']:
            self.test_connection()
        
        if options['create_database']:
            self.create_database()
        
        if options['show_info']:
            self.show_info()

    def test_connection(self):
        """Probar conexión básica a PostgreSQL"""
        self.stdout.write("Probando conexión a PostgreSQL...")
        
        try:
            # Probar conexión directa con psycopg2
            db_settings = settings.DATABASES['default']
            
            conn = psycopg2.connect(
                host=db_settings['HOST'],
                port=db_settings['PORT'],
                user=db_settings['USER'],
                password=db_settings['PASSWORD'],
                database='postgres'  # Conectar a la DB por defecto primero
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Conexión exitosa a PostgreSQL\n'
                    f'   Versión: {version[0]}'
                )
            )
            
            # Verificar si existe la base de datos
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (db_settings['NAME'],)
            )
            
            if cursor.fetchone():
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Base de datos "{db_settings["NAME"]}" existe'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️ Base de datos "{db_settings["NAME"]}" no existe'
                    )
                )
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error de conexión: {e}')
            )

    def create_database(self):
        """Crear la base de datos si no existe"""
        self.stdout.write("Creando base de datos si no existe...")
        
        try:
            db_settings = settings.DATABASES['default']
            
            # Conectar a la base de datos por defecto para crear la nueva
            conn = psycopg2.connect(
                host=db_settings['HOST'],
                port=db_settings['PORT'],
                user=db_settings['USER'],
                password=db_settings['PASSWORD'],
                database='postgres'
            )
            
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Verificar si la base de datos existe
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (db_settings['NAME'],)
            )
            
            if cursor.fetchone():
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Base de datos "{db_settings["NAME"]}" ya existe'
                    )
                )
            else:
                # Crear la base de datos
                cursor.execute(
                    f'CREATE DATABASE "{db_settings["NAME"]}" '
                    f'OWNER "{db_settings["USER"]}" '
                    f'ENCODING "UTF8" '
                    f'LC_COLLATE "Spanish_Bolivia.1252" '
                    f'LC_CTYPE "Spanish_Bolivia.1252";'
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Base de datos "{db_settings["NAME"]}" creada exitosamente'
                    )
                )
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creando base de datos: {e}')
            )

    def show_info(self):
        """Mostrar información de la configuración"""
        self.stdout.write("Información de configuración PostgreSQL:")
        
        db_settings = settings.DATABASES['default']
        
        self.stdout.write(f"\n📊 CONFIGURACIÓN:")
        self.stdout.write(f"   Engine: {db_settings['ENGINE']}")
        self.stdout.write(f"   Database: {db_settings['NAME']}")
        self.stdout.write(f"   User: {db_settings['USER']}")
        self.stdout.write(f"   Host: {db_settings['HOST']}")
        self.stdout.write(f"   Port: {db_settings['PORT']}")
        
        # Probar conexión con Django
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                
                cursor.execute("SELECT current_database();")
                current_db = cursor.fetchone()
                
                cursor.execute("SELECT current_user;")
                current_user = cursor.fetchone()
                
                self.stdout.write(f"\n📋 INFORMACIÓN DE CONEXIÓN:")
                self.stdout.write(f"   Versión PostgreSQL: {version[0]}")
                self.stdout.write(f"   Base de datos actual: {current_db[0]}")
                self.stdout.write(f"   Usuario actual: {current_user[0]}")
                
                # Mostrar tablas existentes
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """)
                tables = cursor.fetchall()
                
                if tables:
                    self.stdout.write(f"\n📋 TABLAS EXISTENTES ({len(tables)}):")
                    for table in tables:
                        self.stdout.write(f"   - {table[0]}")
                else:
                    self.stdout.write(f"\n📋 No hay tablas en la base de datos")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error obteniendo información: {e}')
            )
