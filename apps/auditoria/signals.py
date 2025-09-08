from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import AuditoriaLog, SesionUsuario, TipoAccion
from .utils import obtener_datos_request, serializar_objeto
from .middleware import get_current_user, get_current_ip, get_current_user_agent

User = get_user_model()


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Registra cuando un usuario inicia sesión"""
    ip, user_agent = obtener_datos_request(request)
    
    # Crear log de auditoría
    AuditoriaLog.objects.create(
        usuario=user,
        direccion_ip=ip,
        user_agent=user_agent,
        accion=TipoAccion.LOGIN,
        descripcion=f'Usuario {user.email} inició sesión exitosamente',
        exito=True
    )
    
    # Crear/actualizar sesión de usuario
    session_key = request.session.session_key
    if session_key:
        SesionUsuario.objects.update_or_create(
            session_key=session_key,
            defaults={
                'usuario': user,
                'direccion_ip': ip,
                'user_agent': user_agent,
                'activa': True,
                'fecha_cierre': None
            }
        )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """Registra cuando un usuario cierra sesión"""
    if user and user.is_authenticated:
        ip, user_agent = obtener_datos_request(request)
        
        # Crear log de auditoría
        AuditoriaLog.objects.create(
            usuario=user,
            direccion_ip=ip,
            user_agent=user_agent,
            accion=TipoAccion.LOGOUT,
            descripcion=f'Usuario {user.email} cerró sesión',
            exito=True
        )
        
        # Cerrar sesión en el modelo
        session_key = request.session.session_key
        if session_key:
            try:
                sesion = SesionUsuario.objects.get(
                    session_key=session_key,
                    usuario=user,
                    activa=True
                )
                sesion.activa = False
                sesion.fecha_cierre = timezone.now()
                sesion.save()
            except SesionUsuario.DoesNotExist:
                pass


@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Registra intentos de login fallidos"""
    ip, user_agent = obtener_datos_request(request)
    
    # Intentar obtener el email de las credenciales
    email = credentials.get('username', 'Desconocido')
    
    AuditoriaLog.objects.create(
        usuario=None,  # No hay usuario autenticado
        direccion_ip=ip,
        user_agent=user_agent,
        accion=TipoAccion.LOGIN_FAILED,
        descripcion=f'Intento de login fallido para: {email}',
        datos_nuevos={'email_intentado': email},
        exito=False
    )


# Variables globales para almacenar el estado anterior de los objetos
_objetos_anteriores = {}


@receiver(pre_save)
def capturar_estado_anterior(sender, instance, **kwargs):
    """Captura el estado anterior del objeto antes de guardar"""
    # Solo para modelos que queremos auditar
    modelos_auditados = [User]  # Agregar más modelos según sea necesario
    
    if sender in modelos_auditados and instance.pk:
        try:
            objeto_anterior = sender.objects.get(pk=instance.pk)
            _objetos_anteriores[f"{sender.__name__}_{instance.pk}"] = serializar_objeto(objeto_anterior)
        except sender.DoesNotExist:
            pass


@receiver(post_save)
def log_modelo_creado_actualizado(sender, instance, created, **kwargs):
    """Registra cuando se crea o actualiza un modelo"""
    # Solo para modelos que queremos auditar
    modelos_auditados = [User]  # Agregar más modelos según sea necesario
    
    if sender in modelos_auditados:
        # Obtener el usuario actual del contexto del hilo
        usuario = get_current_user()
        if usuario and not usuario.is_authenticated:
            usuario = None
            
        content_type = ContentType.objects.get_for_model(sender)
        
        if created:
            accion = TipoAccion.CREATE
            descripcion = f'Se creó {content_type.model} con ID {instance.pk}'
            datos_anteriores = None
            datos_nuevos = serializar_objeto(instance)
        else:
            accion = TipoAccion.UPDATE
            descripcion = f'Se actualizó {content_type.model} con ID {instance.pk}'
            
            # Obtener datos anteriores si están disponibles
            key = f"{sender.__name__}_{instance.pk}"
            datos_anteriores = _objetos_anteriores.pop(key, None)
            datos_nuevos = serializar_objeto(instance)
        
        # Solo crear el log si tenemos información del request o es una operación administrativa
        ip = get_current_ip() or '127.0.0.1'
        user_agent = get_current_user_agent() or 'Sistema'
        
        AuditoriaLog.objects.create(
            usuario=usuario,
            direccion_ip=ip,
            user_agent=user_agent,
            accion=accion,
            content_type=content_type,
            object_id=instance.pk,
            descripcion=descripcion,
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos,
            exito=True
        )


@receiver(post_delete)
def log_modelo_eliminado(sender, instance, **kwargs):
    """Registra cuando se elimina un modelo"""
    # Solo para modelos que queremos auditar
    modelos_auditados = [User]  # Agregar más modelos según sea necesario
    
    if sender in modelos_auditados:
        usuario = get_current_user()
        if usuario and not usuario.is_authenticated:
            usuario = None
            
        content_type = ContentType.objects.get_for_model(sender)
        
        # Solo crear el log si tenemos información del request o es una operación administrativa
        ip = get_current_ip() or '127.0.0.1'
        user_agent = get_current_user_agent() or 'Sistema'
        
        AuditoriaLog.objects.create(
            usuario=usuario,
            direccion_ip=ip,
            user_agent=user_agent,
            accion=TipoAccion.DELETE,
            content_type=content_type,
            object_id=instance.pk,
            descripcion=f'Se eliminó {content_type.model} con ID {instance.pk}',
            datos_anteriores=serializar_objeto(instance),
            exito=True
        )
