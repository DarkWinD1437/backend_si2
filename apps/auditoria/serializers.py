from rest_framework import serializers
from .models import AuditoriaLog, SesionUsuario


class AuditoriaLogSerializer(serializers.ModelSerializer):
    """Serializer para logs de auditoría"""
    
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)
    accion_display = serializers.CharField(source='get_accion_display', read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    
    class Meta:
        model = AuditoriaLog
        fields = [
            'id',
            'usuario_email',
            'direccion_ip',
            'accion',
            'accion_display',
            'content_type_name',
            'object_id',
            'descripcion',
            'timestamp',
            'exito'
        ]
        read_only_fields = fields


class SesionUsuarioSerializer(serializers.ModelSerializer):
    """Serializer para sesiones de usuario"""
    
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)
    duracion_sesion = serializers.SerializerMethodField()
    
    class Meta:
        model = SesionUsuario
        fields = [
            'id',
            'usuario_email',
            'direccion_ip',
            'fecha_inicio',
            'fecha_ultimo_acceso',
            'fecha_cierre',
            'activa',
            'duracion_sesion'
        ]
        read_only_fields = fields
    
    def get_duracion_sesion(self, obj):
        """Calcula la duración de la sesión"""
        if obj.fecha_cierre:
            delta = obj.fecha_cierre - obj.fecha_inicio
        else:
            delta = obj.fecha_ultimo_acceso - obj.fecha_inicio
        
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
