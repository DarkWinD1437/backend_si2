from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
import re


class TipoDocumento(models.TextChoices):
    """Tipos de documentos de identidad"""
    CI = 'CI', 'Cédula de Identidad'
    NIT = 'NIT', 'Número de Identificación Tributaria' 
    PASAPORTE = 'PASAPORTE', 'Pasaporte'
    CARNET_EXTRANJERO = 'CARNET_EXTRANJERO', 'Carnet de Extranjero'


class DocumentoIdentidad(models.Model):
    """Modelo para gestionar documentos de identidad únicos"""
    
    tipo_documento = models.CharField(
        max_length=20,
        choices=TipoDocumento.choices,
        default=TipoDocumento.CI
    )
    
    numero_documento = models.CharField(
        max_length=20,
        help_text='Número del documento sin guiones ni espacios'
    )
    
    # Para permitir formatos como CI con extensión (ej: 12345678-1A)
    extension = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        help_text='Extensión del documento (ej: 1A para CI)'
    )
    
    # Campos de auditoría
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'documentos_identidad'
        verbose_name = 'Documento de Identidad'
        verbose_name_plural = 'Documentos de Identidad'
        
        # Constrainst único compuesto
        constraints = [
            models.UniqueConstraint(
                fields=['tipo_documento', 'numero_documento', 'extension'],
                name='unique_documento_completo',
                condition=models.Q(activo=True)
            ),
            models.UniqueConstraint(
                fields=['tipo_documento', 'numero_documento'],
                name='unique_documento_sin_extension',
                condition=models.Q(activo=True, extension__isnull=True)
            )
        ]
        
        indexes = [
            models.Index(fields=['tipo_documento', 'numero_documento']),
            models.Index(fields=['numero_documento']),
            models.Index(fields=['activo']),
        ]
    
    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        # Limpiar el número de documento (remover espacios, guiones, etc.)
        if self.numero_documento:
            self.numero_documento = re.sub(r'[^\w]', '', self.numero_documento).upper()
        
        # Validar formato según tipo de documento
        self._validar_formato_documento()
        
        # Validar unicidad
        self._validar_unicidad()
    
    def _validar_formato_documento(self):
        """Valida el formato según el tipo de documento"""
        if not self.numero_documento:
            raise ValidationError({'numero_documento': 'El número de documento es obligatorio'})
        
        if self.tipo_documento == TipoDocumento.CI:
            # CI boliviana: 7-12 dígitos
            if not re.match(r'^\d{7,12}$', self.numero_documento):
                raise ValidationError({
                    'numero_documento': 'La CI debe contener entre 7 y 12 dígitos'
                })
            
            # Validar extensión si existe
            if self.extension:
                if not re.match(r'^[1-9][A-Z]?$', self.extension):
                    raise ValidationError({
                        'extension': 'La extensión de CI debe ser formato: 1A, 2B, etc.'
                    })
        
        elif self.tipo_documento == TipoDocumento.NIT:
            # NIT boliviano: formato específico
            if not re.match(r'^\d{10,13}$', self.numero_documento):
                raise ValidationError({
                    'numero_documento': 'El NIT debe contener entre 10 y 13 dígitos'
                })
        
        elif self.tipo_documento == TipoDocumento.PASAPORTE:
            # Pasaporte: formato alfanumérico
            if not re.match(r'^[A-Z0-9]{6,15}$', self.numero_documento):
                raise ValidationError({
                    'numero_documento': 'El pasaporte debe contener entre 6 y 15 caracteres alfanuméricos'
                })
    
    def _validar_unicidad(self):
        """Valida que no exista otro documento igual activo"""
        queryset = DocumentoIdentidad.objects.filter(
            tipo_documento=self.tipo_documento,
            numero_documento=self.numero_documento,
            activo=True
        ).exclude(pk=self.pk)
        
        # Si hay extensión, debe coincidir
        if self.extension:
            queryset = queryset.filter(extension=self.extension)
        else:
            queryset = queryset.filter(extension__isnull=True)
        
        if queryset.exists():
            documento_existente = queryset.first()
            if self.extension:
                documento_completo = f"{self.numero_documento}-{self.extension}"
            else:
                documento_completo = self.numero_documento
            
            raise ValidationError({
                'numero_documento': f'Ya existe un {self.get_tipo_documento_display()} '
                                  f'con número {documento_completo}'
            })
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def documento_completo(self):
        """Retorna el documento completo formateado"""
        if self.extension:
            return f"{self.numero_documento}-{self.extension}"
        return self.numero_documento
    
    def __str__(self):
        return f"{self.get_tipo_documento_display()}: {self.documento_completo}"
    
    @classmethod
    def existe_documento(cls, tipo_documento, numero_documento, extension=None, excluir_pk=None):
        """Método de clase para verificar si existe un documento"""
        queryset = cls.objects.filter(
            tipo_documento=tipo_documento,
            numero_documento=numero_documento,
            activo=True
        )
        
        if extension:
            queryset = queryset.filter(extension=extension)
        else:
            queryset = queryset.filter(extension__isnull=True)
        
        if excluir_pk:
            queryset = queryset.exclude(pk=excluir_pk)
        
        return queryset.exists()
    
    @classmethod
    def normalizar_numero(cls, numero):
        """Normaliza un número de documento"""
        if numero:
            return re.sub(r'[^\w]', '', numero).upper()
        return numero
