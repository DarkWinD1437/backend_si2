# models.py
from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from apps.usuarios.models import User
from apps.usuarios.document_models import DocumentoIdentidad, TipoDocumento

class Socio(models.Model):
    TIPO_SOCIO_CHOICES = [
        ('PRODUCTOR', 'Productor'),
        ('CONSUMIDOR', 'Consumidor'),
        ('TRABAJADOR', 'Trabajador'),
    ]

    # Validadores
    telefono_validator = RegexValidator(
        regex=r'^\d{7,15}$',
        message='El teléfono debe contener solo números (7-15 dígitos)'
    )

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='socio_perfil')
    tipo_socio = models.CharField(max_length=20, choices=TIPO_SOCIO_CHOICES)
    
    # Reemplazamos el campo DNI por una referencia al documento
    # Mantenemos compatibilidad temporal con el campo dni
    dni = models.CharField(
        max_length=20, 
        unique=True,
        null=True,
        blank=True,
        help_text='DEPRECATED: Usar documento_identidad en su lugar'
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

    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        # Validar que el usuario asociado tenga documento de identidad
        if self.usuario and not self.usuario.documento_identidad:
            raise ValidationError({
                'usuario': 'El usuario debe tener un documento de identidad asociado'
            })
        
        # Validar que no haya duplicados de documento entre socios activos
        if self.usuario and self.usuario.documento_identidad and self.activo:
            documento = self.usuario.documento_identidad
            
            # Buscar otros socios activos con el mismo documento
            socios_con_mismo_doc = Socio.objects.filter(
                usuario__documento_identidad__tipo_documento=documento.tipo_documento,
                usuario__documento_identidad__numero_documento=documento.numero_documento,
                usuario__documento_identidad__extension=documento.extension,
                activo=True
            ).exclude(pk=self.pk)
            
            if socios_con_mismo_doc.exists():
                raise ValidationError({
                    'usuario': f'Ya existe un socio activo con el documento '
                             f'{documento.get_tipo_documento_display()}: {documento.documento_completo}'
                })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.get_tipo_socio_display()}"

    def nombre_completo(self):
        return self.usuario.get_full_name()
    
    def email(self):
        return self.usuario.email
    
    def esta_activo(self):
        return self.activo
    
    @property
    def documento_numero(self):
        """Retorna el número de documento del usuario"""
        if self.usuario and self.usuario.documento_identidad:
            return self.usuario.documento_identidad.documento_completo
        return self.dni  # Fallback al campo legacy
    
    @property
    def tipo_documento(self):
        """Retorna el tipo de documento del usuario"""
        if self.usuario and self.usuario.documento_identidad:
            return self.usuario.documento_identidad.get_tipo_documento_display()
        return 'CI/DNI'  # Fallback para datos legacy

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