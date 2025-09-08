from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

User = get_user_model()


class TipoAccion(models.TextChoices):
    """Tipos de acciones para auditoría"""
    LOGIN = 'LOGIN', 'Inicio de sesión'
    LOGOUT = 'LOGOUT', 'Cierre de sesión'
    LOGIN_FAILED = 'LOGIN_FAILED', 'Intento de login fallido'
    CREATE = 'CREATE', 'Crear'
    UPDATE = 'UPDATE', 'Actualizar'
    DELETE = 'DELETE', 'Eliminar'
    VIEW = 'VIEW', 'Visualizar'


class AuditoriaLog(models.Model):
    """Modelo para registrar actividades de auditoría"""
    
    # Usuario que realizó la acción
    usuario = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='logs_auditoria'
    )
    
    # Datos de la sesión/request
    direccion_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Información de la acción
    accion = models.CharField(
        max_length=20, 
        choices=TipoAccion.choices,
        db_index=True
    )
    
    # Modelo afectado (para CRUD)
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    objeto_afectado = GenericForeignKey('content_type', 'object_id')
    
    # Detalles adicionales
    descripcion = models.TextField(blank=True)
    datos_anteriores = models.JSONField(null=True, blank=True)  # Para updates
    datos_nuevos = models.JSONField(null=True, blank=True)
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    exito = models.BooleanField(default=True)  # Si la acción fue exitosa
    
    class Meta:
        db_table = 'auditoria_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['usuario', 'timestamp']),
            models.Index(fields=['accion', 'timestamp']),
            models.Index(fields=['content_type', 'object_id']),
        ]
    
    def __str__(self):
        usuario_str = self.usuario.email if self.usuario else 'Anónimo'
        return f'{usuario_str} - {self.get_accion_display()} - {self.timestamp}'


class SesionUsuario(models.Model):
    """Modelo para trackear sesiones de usuarios"""
    
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='sesiones'
    )
    
    # Datos de la sesión
    session_key = models.CharField(max_length=40, unique=True)
    direccion_ip = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_ultimo_acceso = models.DateTimeField(auto_now=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    
    # Estado
    activa = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'sesiones_usuario'
        ordering = ['-fecha_inicio']
    
    def __str__(self):
        return f'{self.usuario.email} - {self.fecha_inicio}'
