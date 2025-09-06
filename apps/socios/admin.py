# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Socio, Aporte

@admin.register(Socio)
class SocioAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'dni', 'nombre_completo', 'email', 'tipo_socio', 
        'telefono', 'activo', 'fecha_ingreso'
    ]
    list_filter = ['tipo_socio', 'activo', 'fecha_ingreso', 'creado_en']
    search_fields = [
        'dni', 'usuario__first_name', 'usuario__last_name', 
        'usuario__email', 'telefono'
    ]
    list_editable = ['activo']
    readonly_fields = ['fecha_ingreso', 'creado_en', 'actualizado_en']
    list_per_page = 20
    
    fieldsets = (
        ('Información de Usuario', {
            'fields': ('usuario', 'dni', 'tipo_socio')
        }),
        ('Información de Contacto', {
            'fields': ('direccion', 'telefono')
        }),
        ('Estado', {
            'fields': ('activo', 'fecha_ingreso')
        }),
        ('Información Adicional', {
            'fields': ('notas',),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )
    
    def nombre_completo(self, obj):
        return obj.usuario.get_full_name()
    
    def email(self, obj):
        return obj.usuario.email

@admin.register(Aporte)
class AporteAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'socio', 'tipo_aporte', 'monto_formateado', 
        'fecha_aporte', 'descripcion_corta'
    ]
    list_filter = ['tipo_aporte', 'fecha_aporte', 'creado_en']
    search_fields = [
        'socio__usuario__first_name', 'socio__usuario__last_name', 
        'socio__dni', 'descripcion'
    ]
    readonly_fields = ['creado_en', 'actualizado_en']
    list_per_page = 20
    
    def monto_formateado(self, obj):
        if obj.monto:
            return f"${obj.monto:,.2f}"
        return "N/A"
    monto_formateado.short_description = 'Monto'
    
    def descripcion_corta(self, obj):
        if len(obj.descripcion) > 50:
            return f"{obj.descripcion[:50]}..."
        return obj.descripcion
    descripcion_corta.short_description = 'Descripción'