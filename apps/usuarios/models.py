from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.exceptions import ValidationError
from .document_models import DocumentoIdentidad, TipoDocumento

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El Email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # Relación con documento de identidad
    documento_identidad = models.OneToOneField(
        DocumentoIdentidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuario',
        help_text='Documento de identidad del usuario'
    )

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user'
    )

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    def clean(self):
        """Validaciones personalizadas"""
        super().clean()
        
        # Validar que el email no esté duplicado (además de la restricción de BD)
        if self.email:
            queryset = User.objects.filter(email=self.email)
            if self.pk:
                queryset = queryset.exclude(pk=self.pk)
            if queryset.exists():
                raise ValidationError({'email': 'Ya existe un usuario con este email'})
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def documento_numero(self):
        """Retorna el número de documento si existe"""
        if self.documento_identidad:
            return self.documento_identidad.documento_completo
        return None
    
    @property
    def tipo_documento(self):
        """Retorna el tipo de documento si existe"""
        if self.documento_identidad:
            return self.documento_identidad.get_tipo_documento_display()
        return None
    
    def tiene_documento(self):
        """Verifica si el usuario tiene documento asociado"""
        return self.documento_identidad is not None
    
    def __str__(self):
        if self.get_full_name():
            return f"{self.get_full_name()} ({self.email})"
        return self.email
