# models.py
from django.db import models
from django.core.validators import RegexValidator
from apps.usuarios.models import User

class Socio(models.Model):
    TIPO_SOCIO_CHOICES = [
        ('PRODUCTOR', 'Productor'),
        ('CONSUMIDOR', 'Consumidor'),
        ('TRABAJADOR', 'Trabajador'),
    ]

    # Validadores
    dni_validator = RegexValidator(
        regex=r'^\d{8,15}$',
        message='El DNI debe contener solo números (8-15 dígitos)'
    )
    telefono_validator = RegexValidator(
        regex=r'^\d{7,15}$',
        message='El teléfono debe contener solo números (7-15 dígitos)'
    )

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='socio_perfil')
    tipo_socio = models.CharField(max_length=20, choices=TIPO_SOCIO_CHOICES)
    dni = models.CharField(
        max_length=20, 
        unique=True,
        validators=[dni_validator],
        help_text='DNI del socio (solo números)'
    )
    direccion = models.TextField(max_length=500)
    telefono = models.CharField(
        max_length=15,
        validators=[telefono_validator],
        help_text='Teléfono del socio (solo números)'
    )
    fecha_ingreso = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True, null=True)
    
    # Campos de auditoría
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Socio'
        verbose_name_plural = 'Socios'
        ordering = ['-fecha_ingreso']
        indexes = [
            models.Index(fields=['dni'], name='socio_dni_idx'),
            models.Index(fields=['activo'], name='socio_activo_idx'),
            models.Index(fields=['tipo_socio'], name='socio_tipo_idx'),
        ]

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.get_tipo_socio_display()}"

    def nombre_completo(self):
        return self.usuario.get_full_name()
    
    def email(self):
        return self.usuario.email
    
    def esta_activo(self):
        return self.activo

class Aporte(models.Model):
    TIPO_APORTE_CHOICES = [
        ('ECONOMICO', 'Económico'),
        ('TRABAJO', 'Trabajo'),
        ('PRODUCTO', 'Producto'),
    ]

    socio = models.ForeignKey(Socio, on_delete=models.CASCADE, related_name='aportes')
    tipo_aporte = models.CharField(max_length=20, choices=TIPO_APORTE_CHOICES)
    monto = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    descripcion = models.TextField(max_length=500)
    fecha_aporte = models.DateField()
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Aporte'
        verbose_name_plural = 'Aportes'
        ordering = ['-fecha_aporte']
        indexes = [
            models.Index(fields=['tipo_aporte'], name='aporte_tipo_idx'),
            models.Index(fields=['fecha_aporte'], name='aporte_fecha_idx'),
        ]

    def __str__(self):
        return f"Aporte de {self.socio.usuario.get_full_name()} - {self.get_tipo_aporte_display()}"