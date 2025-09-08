from django.core.management.base import BaseCommand
from django.db import transaction
from apps.usuarios.models import User
from apps.usuarios.document_models import DocumentoIdentidad, TipoDocumento
from apps.socios.models import Socio
from apps.usuarios.validation_serializers import ValidacionDuplicadosSerializer
from rest_framework import serializers


class Command(BaseCommand):
    help = 'Comando para probar las validaciones de duplicados CI/NIT'

    def add_arguments(self, parser):
        parser.add_argument(
            '--crear-datos-prueba',
            action='store_true',
            help='Crear datos de prueba para validaciones',
        )
        parser.add_argument(
            '--probar-validaciones',
            action='store_true',
            help='Probar diferentes escenarios de validación',
        )
        parser.add_argument(
            '--limpiar-datos',
            action='store_true',
            help='Limpiar datos de prueba',
        )
        parser.add_argument(
            '--mostrar-estadisticas',
            action='store_true',
            help='Mostrar estadísticas de documentos',
        )

    def handle(self, *args, **options):
        if options['crear_datos_prueba']:
            self.crear_datos_prueba()
        
        if options['probar_validaciones']:
            self.probar_validaciones()
        
        if options['mostrar_estadisticas']:
            self.mostrar_estadisticas()
        
        if options['limpiar_datos']:
            self.limpiar_datos()

    def crear_datos_prueba(self):
        """Crear datos de prueba para demostrar validaciones"""
        self.stdout.write("Creando datos de prueba para validaciones...")
        
        try:
            with transaction.atomic():
                # 1. Crear un documento CI
                doc_ci = DocumentoIdentidad.objects.create(
                    tipo_documento=TipoDocumento.CI,
                    numero_documento='12345678',
                    extension='1A'
                )
                
                # 2. Crear usuario con CI
                user1 = User.objects.create_user(
                    email='usuario.ci@example.com',
                    password='password123',
                    first_name='Juan',
                    last_name='Pérez',
                    username='juan.perez'
                )
                user1.documento_identidad = doc_ci
                user1.save()
                
                # 3. Crear un documento NIT
                doc_nit = DocumentoIdentidad.objects.create(
                    tipo_documento=TipoDocumento.NIT,
                    numero_documento='1234567890123'
                )
                
                # 4. Crear usuario con NIT
                user2 = User.objects.create_user(
                    email='empresa.nit@example.com',
                    password='password123',
                    first_name='Empresa',
                    last_name='SA',
                    username='empresa.sa'
                )
                user2.documento_identidad = doc_nit
                user2.save()
                
                # 5. Crear socio con el primer usuario
                socio1 = Socio.objects.create(
                    usuario=user1,
                    tipo_socio='PRODUCTOR',
                    direccion='Av. Principal 123',
                    telefono='70123456',
                    dni=doc_ci.documento_completo  # Compatibilidad
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Datos de prueba creados exitosamente:\n'
                        f'   - Usuario CI: {user1.email} - {doc_ci.documento_completo}\n'
                        f'   - Usuario NIT: {user2.email} - {doc_nit.documento_completo}\n'
                        f'   - Socio: {socio1.nombre_completo()}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creando datos de prueba: {e}')
            )

    def probar_validaciones(self):
        """Probar diferentes escenarios de validación"""
        self.stdout.write("\n" + "="*60)
        self.stdout.write("PROBANDO VALIDACIONES DE DUPLICADOS")
        self.stdout.write("="*60)
        
        # Test 1: Email válido (nuevo)
        self.stdout.write("\n1. Probando email nuevo...")
        self._probar_validacion({
            'email': 'nuevo.usuario@example.com'
        })
        
        # Test 2: Email duplicado
        self.stdout.write("\n2. Probando email duplicado...")
        self._probar_validacion({
            'email': 'usuario.ci@example.com'
        })
        
        # Test 3: Documento nuevo
        self.stdout.write("\n3. Probando documento nuevo...")
        self._probar_validacion({
            'tipo_documento': TipoDocumento.CI,
            'numero_documento': '87654321',
            'extension_documento': '2B'
        })
        
        # Test 4: Documento duplicado
        self.stdout.write("\n4. Probando documento duplicado...")
        self._probar_validacion({
            'tipo_documento': TipoDocumento.CI,
            'numero_documento': '12345678',
            'extension_documento': '1A'
        })
        
        # Test 5: Validación completa válida
        self.stdout.write("\n5. Probando datos completos válidos...")
        self._probar_validacion({
            'email': 'valido@example.com',
            'tipo_documento': TipoDocumento.CI,
            'numero_documento': '11111111',
            'extension_documento': '3C'
        })
        
        # Test 6: Validación completa con duplicados
        self.stdout.write("\n6. Probando datos completos con duplicados...")
        self._probar_validacion({
            'email': 'usuario.ci@example.com',
            'tipo_documento': TipoDocumento.CI,
            'numero_documento': '12345678',
            'extension_documento': '1A'
        })
        
        # Test 7: Formato de documento incorrecto
        self.stdout.write("\n7. Probando formato de documento incorrecto...")
        self._probar_validacion({
            'tipo_documento': TipoDocumento.CI,
            'numero_documento': '123',  # Muy corto
        })

    def _probar_validacion(self, datos):
        """Probar validación con datos específicos"""
        serializer = ValidacionDuplicadosSerializer(data=datos)
        
        try:
            serializer.is_valid(raise_exception=True)
            self.stdout.write(
                self.style.SUCCESS(
                    f"   ✅ VÁLIDO: {datos}\n"
                    f"   Info: {serializer.validated_data.get('_validation_info', {})}"
                )
            )
        except serializers.ValidationError as e:
            self.stdout.write(
                self.style.ERROR(
                    f"   ❌ INVÁLIDO: {datos}\n"
                    f"   Errores: {e.detail}"
                )
            )

    def mostrar_estadisticas(self):
        """Mostrar estadísticas de documentos y usuarios"""
        self.stdout.write("\n" + "="*60)
        self.stdout.write("ESTADÍSTICAS DE DOCUMENTOS Y USUARIOS")
        self.stdout.write("="*60)
        
        # Usuarios totales
        total_usuarios = User.objects.count()
        usuarios_con_doc = User.objects.exclude(documento_identidad__isnull=True).count()
        usuarios_sin_doc = total_usuarios - usuarios_con_doc
        
        self.stdout.write(f"\n📊 USUARIOS:")
        self.stdout.write(f"   Total: {total_usuarios}")
        self.stdout.write(f"   Con documento: {usuarios_con_doc}")
        self.stdout.write(f"   Sin documento: {usuarios_sin_doc}")
        
        # Documentos por tipo
        self.stdout.write(f"\n📋 DOCUMENTOS:")
        total_docs = DocumentoIdentidad.objects.filter(activo=True).count()
        self.stdout.write(f"   Total activos: {total_docs}")
        
        for tipo_choice in TipoDocumento.choices:
            tipo_codigo = tipo_choice[0]
            tipo_nombre = tipo_choice[1]
            count = DocumentoIdentidad.objects.filter(
                tipo_documento=tipo_codigo,
                activo=True
            ).count()
            self.stdout.write(f"   {tipo_nombre}: {count}")
        
        # Socios
        total_socios = Socio.objects.count()
        socios_activos = Socio.objects.filter(activo=True).count()
        socios_con_doc = Socio.objects.exclude(
            usuario__documento_identidad__isnull=True
        ).count()
        
        self.stdout.write(f"\n👥 SOCIOS:")
        self.stdout.write(f"   Total: {total_socios}")
        self.stdout.write(f"   Activos: {socios_activos}")
        self.stdout.write(f"   Con documento: {socios_con_doc}")
        
        # Detalles de documentos existentes
        if total_docs > 0:
            self.stdout.write(f"\n📝 DOCUMENTOS REGISTRADOS:")
            documentos = DocumentoIdentidad.objects.filter(activo=True).select_related('usuario')
            
            for doc in documentos:
                info = f"   {doc.get_tipo_documento_display()}: {doc.documento_completo}"
                
                if hasattr(doc, 'usuario') and doc.usuario:
                    info += f" → {doc.usuario.email}"
                    
                    if hasattr(doc.usuario, 'socio_perfil'):
                        socio = doc.usuario.socio_perfil
                        info += f" (Socio: {socio.get_tipo_socio_display()})"
                
                self.stdout.write(info)

    def limpiar_datos(self):
        """Limpiar datos de prueba"""
        self.stdout.write("Limpiando datos de prueba...")
        
        try:
            with transaction.atomic():
                # Buscar usuarios de prueba
                emails_prueba = [
                    'usuario.ci@example.com',
                    'empresa.nit@example.com',
                    'nuevo.usuario@example.com',
                    'valido@example.com'
                ]
                
                usuarios_eliminados = 0
                documentos_eliminados = 0
                socios_eliminados = 0
                
                for email in emails_prueba:
                    try:
                        user = User.objects.get(email=email)
                        
                        # Eliminar socio si existe
                        if hasattr(user, 'socio_perfil'):
                            user.socio_perfil.delete()
                            socios_eliminados += 1
                        
                        # Eliminar documento si existe
                        if user.documento_identidad:
                            user.documento_identidad.delete()
                            documentos_eliminados += 1
                        
                        # Eliminar usuario
                        user.delete()
                        usuarios_eliminados += 1
                        
                    except User.DoesNotExist:
                        pass
                
                # Limpiar documentos huérfanos
                docs_huerfanos = DocumentoIdentidad.objects.filter(
                    usuario__isnull=True,
                    numero_documento__in=['12345678', '1234567890123', '87654321', '11111111']
                )
                docs_huerfanos_count = docs_huerfanos.count()
                docs_huerfanos.delete()
                documentos_eliminados += docs_huerfanos_count
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Limpieza completada:\n'
                        f'   - Usuarios eliminados: {usuarios_eliminados}\n'
                        f'   - Documentos eliminados: {documentos_eliminados}\n'
                        f'   - Socios eliminados: {socios_eliminados}'
                    )
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error en la limpieza: {e}')
            )
