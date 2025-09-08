from django.contrib import admin
from .models import AuditoriaLog, SesionUsuario


@admin.register(AuditoriaLog)
class AuditoriaLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 
        'usuario', 
        'accion', 
        'direccion_ip', 
        'content_type',
        'exito'
    ]
    list_filter = [
        'accion', 
        'exito', 
        'timestamp',
        'content_type'
    ]
    search_fields = [
        'usuario__email', 
        'descripcion', 
        'direccion_ip'
    ]
    readonly_fields = [
        'timestamp', 
        'usuario', 
        'direccion_ip', 
        'user_agent',
        'accion', 
        'content_type', 
        'object_id',
        'descripcion', 
        'datos_anteriores', 
        'datos_nuevos',
        'exito'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(SesionUsuario)
class SesionUsuarioAdmin(admin.ModelAdmin):
    list_display = [
        'usuario', 
        'direccion_ip', 
        'fecha_inicio',
        'fecha_ultimo_acceso',
        'activa'
    ]
    list_filter = [
        'activa', 
        'fecha_inicio',
        'fecha_ultimo_acceso'
    ]
    search_fields = [
        'usuario__email', 
        'direccion_ip'
    ]
    readonly_fields = [
        'session_key',
        'fecha_inicio', 
        'fecha_ultimo_acceso',
        'fecha_cierre'
    ]
