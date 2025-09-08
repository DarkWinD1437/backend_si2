from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.auditoria.models import AuditoriaLog, SesionUsuario
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Comando para probar la funcionalidad de auditoría'

    def add_arguments(self, parser):
        parser.add_argument(
            '--crear-datos-prueba',
            action='store_true',
            help='Crear datos de prueba para auditoría',
        )
        parser.add_argument(
            '--mostrar-estadisticas',
            action='store_true',
            help='Mostrar estadísticas de auditoría',
        )
        parser.add_argument(
            '--limpiar-logs',
            action='store_true',
            help='Limpiar logs de auditoría antiguos',
        )
        parser.add_argument(
            '--dias',
            type=int,
            default=30,
            help='Número de días para estadísticas o limpieza',
        )

    def handle(self, *args, **options):
        if options['crear_datos_prueba']:
            self.crear_datos_prueba()
        
        if options['mostrar_estadisticas']:
            self.mostrar_estadisticas(options['dias'])
        
        if options['limpiar_logs']:
            self.limpiar_logs(options['dias'])

    def crear_datos_prueba(self):
        """Crear algunos datos de prueba para demostrar la auditoría"""
        self.stdout.write("Creando datos de prueba para auditoría...")
        
        # Crear un usuario de prueba
        email = "usuario_prueba@example.com"
        
        try:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': 'Usuario',
                    'last_name': 'Prueba'
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Usuario de prueba creado: {email}')
                )
            else:
                self.stdout.write(f'Usuario ya existe: {email}')
                
                # Actualizar el usuario para generar log de auditoría
                user.first_name = "Usuario Actualizado"
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Usuario actualizado para generar log de auditoría')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creando usuario: {e}')
            )

    def mostrar_estadisticas(self, dias):
        """Mostrar estadísticas de auditoría"""
        fecha_desde = timezone.now() - timedelta(days=dias)
        
        self.stdout.write(f"\n=== ESTADÍSTICAS DE AUDITORÍA (últimos {dias} días) ===")
        
        # Total de logs
        total_logs = AuditoriaLog.objects.filter(timestamp__gte=fecha_desde).count()
        self.stdout.write(f"Total de eventos: {total_logs}")
        
        # Logs por acción
        self.stdout.write("\n--- Eventos por tipo de acción ---")
        acciones = AuditoriaLog.objects.filter(
            timestamp__gte=fecha_desde
        ).values_list('accion', flat=True).distinct()
        
        for accion in acciones:
            count = AuditoriaLog.objects.filter(
                timestamp__gte=fecha_desde,
                accion=accion
            ).count()
            self.stdout.write(f"{accion}: {count}")
        
        # Intentos de login fallidos
        login_fallidos = AuditoriaLog.objects.filter(
            timestamp__gte=fecha_desde,
            accion='LOGIN_FAILED'
        ).count()
        
        if login_fallidos > 0:
            self.stdout.write(
                self.style.WARNING(f"\n⚠️  Intentos de login fallidos: {login_fallidos}")
            )
        
        # Sesiones activas
        sesiones_activas = SesionUsuario.objects.filter(activa=True).count()
        self.stdout.write(f"\nSesiones activas: {sesiones_activas}")
        
        # Usuarios más activos
        self.stdout.write("\n--- Usuarios más activos ---")
        usuarios_activos = AuditoriaLog.objects.filter(
            timestamp__gte=fecha_desde,
            usuario__isnull=False
        ).values('usuario__email').distinct()[:5]
        
        for usuario in usuarios_activos:
            email = usuario['usuario__email']
            count = AuditoriaLog.objects.filter(
                timestamp__gte=fecha_desde,
                usuario__email=email
            ).count()
            self.stdout.write(f"{email}: {count} acciones")

    def limpiar_logs(self, dias):
        """Limpiar logs de auditoría antiguos"""
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        logs_antiguos = AuditoriaLog.objects.filter(timestamp__lt=fecha_limite)
        count = logs_antiguos.count()
        
        if count > 0:
            logs_antiguos.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Se eliminaron {count} logs de auditoría antiguos')
            )
        else:
            self.stdout.write('No hay logs antiguos para eliminar')
        
        # Limpiar sesiones inactivas antiguas
        sesiones_antiguas = SesionUsuario.objects.filter(
            fecha_ultimo_acceso__lt=fecha_limite,
            activa=False
        )
        count_sesiones = sesiones_antiguas.count()
        
        if count_sesiones > 0:
            sesiones_antiguas.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Se eliminaron {count_sesiones} sesiones antiguas')
            )
