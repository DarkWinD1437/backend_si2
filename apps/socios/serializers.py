# serializers.py
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from django.db import transaction
from .models import Socio, Aporte
from apps.usuarios.models import User
from apps.usuarios.document_models import DocumentoIdentidad, TipoDocumento
from apps.usuarios.validation_serializers import DocumentoIdentidadSerializer, UserExtendedSerializer

class SocioSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(source='usuario.get_full_name', read_only=True)
    email = serializers.EmailField(source='usuario.email', read_only=True)
    username = serializers.CharField(source='usuario.username', read_only=True)
    
    # Información del documento
    documento_numero = serializers.CharField(read_only=True)
    tipo_documento = serializers.CharField(read_only=True)
    documento_info = DocumentoIdentidadSerializer(source='usuario.documento_identidad', read_only=True)
    
    class Meta:
        model = Socio
        fields = [
            'id', 'usuario', 'nombre_completo', 'email', 'username', 'tipo_socio', 
            'dni', 'direccion', 'telefono', 'fecha_ingreso', 'activo', 'notas',
            'documento_numero', 'tipo_documento', 'documento_info',
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = ('id', 'usuario', 'fecha_ingreso', 'creado_en', 'actualizado_en')


class SocioCreateSerializer(serializers.ModelSerializer):
    # Campos para crear el usuario
    username = serializers.CharField(write_only=True, max_length=150, required=False)
    password = serializers.CharField(write_only=True, max_length=128)
    first_name = serializers.CharField(write_only=True, max_length=30)
    last_name = serializers.CharField(write_only=True, max_length=150)
    email = serializers.EmailField(write_only=True, max_length=254)
    
    # Campos para el documento de identidad
    tipo_documento = serializers.ChoiceField(
        choices=TipoDocumento.choices,
        write_only=True,
        default=TipoDocumento.CI,
        help_text='Tipo de documento de identidad'
    )
    numero_documento = serializers.CharField(
        write_only=True,
        max_length=20,
        help_text='Número del documento sin guiones ni espacios'
    )
    extension_documento = serializers.CharField(
        write_only=True,
        max_length=5,
        required=False,
        allow_blank=True,
        help_text='Extensión del documento (ej: 1A para CI)'
    )
    
    class Meta:
        model = Socio
        fields = [
            'username', 'password', 'first_name', 'last_name', 'email',
            'tipo_documento', 'numero_documento', 'extension_documento',
            'tipo_socio', 'dni', 'direccion', 'telefono', 'notas'
        ]
    
    def validate_email(self, value):
        """Validar email único"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está registrado")
        return value
    
    def validate(self, attrs):
        """Validaciones cruzadas"""
        # Validar documento único
        tipo_documento = attrs.get('tipo_documento')
        numero_documento = attrs.get('numero_documento')
        extension_documento = attrs.get('extension_documento') or None
        
        if numero_documento:
            numero_normalizado = DocumentoIdentidad.normalizar_numero(numero_documento)
            attrs['numero_documento'] = numero_normalizado
            
            if DocumentoIdentidad.existe_documento(
                tipo_documento=tipo_documento,
                numero_documento=numero_normalizado,
                extension=extension_documento
            ):
                documento_completo = numero_normalizado
                if extension_documento:
                    documento_completo += f"-{extension_documento}"
                
                raise serializers.ValidationError({
                    'numero_documento': f'Ya existe un {TipoDocumento(tipo_documento).label} '
                                      f'con número {documento_completo}'
                })
        
        # Generar username si no se proporciona
        if not attrs.get('username'):
            email = attrs.get('email', '')
            attrs['username'] = email.split('@')[0] if email else f"user_{numero_documento}"
        
        # Validar username único
        username = attrs.get('username')
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({
                'username': "Este username ya está en uso"
            })
        
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """Crear socio con usuario y documento de identidad"""
        # Extraer datos del documento
        tipo_documento = validated_data.pop('tipo_documento')
        numero_documento = validated_data.pop('numero_documento')
        extension_documento = validated_data.pop('extension_documento', None) or None
        
        # Extraer datos del usuario
        user_data = {
            'username': validated_data.pop('username'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'email': validated_data.pop('email')
        }
        password = validated_data.pop('password')
        
        # Crear documento de identidad
        documento = DocumentoIdentidad.objects.create(
            tipo_documento=tipo_documento,
            numero_documento=numero_documento,
            extension=extension_documento
        )
        
        # Crear usuario
        user = User.objects.create_user(password=password, **user_data)
        user.documento_identidad = documento
        user.save()
        
        # Migrar DNI si se proporciona (compatibilidad)
        if not validated_data.get('dni'):
            validated_data['dni'] = documento.documento_completo
        
        # Crear socio
        socio = Socio.objects.create(usuario=user, **validated_data)
        return socio


class SocioUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(write_only=True, required=False, max_length=30)
    last_name = serializers.CharField(write_only=True, required=False, max_length=150)
    email = serializers.EmailField(write_only=True, required=False, max_length=254)
    
    # Campos para actualizar documento
    tipo_documento = serializers.ChoiceField(
        choices=TipoDocumento.choices,
        write_only=True,
        required=False,
        help_text='Tipo de documento de identidad'
    )
    numero_documento = serializers.CharField(
        write_only=True,
        max_length=20,
        required=False,
        help_text='Número del documento sin guiones ni espacios'
    )
    extension_documento = serializers.CharField(
        write_only=True,
        max_length=5,
        required=False,
        allow_blank=True,
        help_text='Extensión del documento (ej: 1A para CI)'
    )
    
    class Meta:
        model = Socio
        fields = [
            'first_name', 'last_name', 'email',
            'tipo_documento', 'numero_documento', 'extension_documento',
            'tipo_socio', 'dni', 'direccion', 'telefono', 'notas', 'activo'
        ]
    
    def validate_email(self, value):
        """Validar email único"""
        queryset = User.objects.filter(email=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.usuario.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("Este email ya está registrado")
        return value
    
    def validate(self, attrs):
        """Validaciones cruzadas"""
        # Validar documento si se actualiza
        tipo_documento = attrs.get('tipo_documento')
        numero_documento = attrs.get('numero_documento')
        extension_documento = attrs.get('extension_documento')
        
        if numero_documento:
            numero_normalizado = DocumentoIdentidad.normalizar_numero(numero_documento)
            attrs['numero_documento'] = numero_normalizado
            
            # Excluir el documento actual del usuario
            excluir_pk = None
            if self.instance and self.instance.usuario.documento_identidad:
                excluir_pk = self.instance.usuario.documento_identidad.pk
            
            if DocumentoIdentidad.existe_documento(
                tipo_documento=tipo_documento or TipoDocumento.CI,
                numero_documento=numero_normalizado,
                extension=extension_documento,
                excluir_pk=excluir_pk
            ):
                documento_completo = numero_normalizado
                if extension_documento:
                    documento_completo += f"-{extension_documento}"
                
                raise serializers.ValidationError({
                    'numero_documento': f'Ya existe un documento con número {documento_completo}'
                })
        
        return attrs
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """Actualizar socio, usuario y documento"""
        user = instance.usuario
        
        # Extraer datos del documento
        tipo_documento = validated_data.pop('tipo_documento', None)
        numero_documento = validated_data.pop('numero_documento', None)
        extension_documento = validated_data.pop('extension_documento', None)
        
        # Actualizar datos del usuario
        user_fields = ['first_name', 'last_name', 'email']
        for field in user_fields:
            if field in validated_data:
                setattr(user, field, validated_data.pop(field))
        user.save()
        
        # Actualizar documento si se proporcionan datos
        if numero_documento:
            if not tipo_documento and user.documento_identidad:
                tipo_documento = user.documento_identidad.tipo_documento
            elif not tipo_documento:
                tipo_documento = TipoDocumento.CI
            
            if user.documento_identidad:
                # Actualizar documento existente
                documento = user.documento_identidad
                documento.tipo_documento = tipo_documento
                documento.numero_documento = numero_documento
                documento.extension = extension_documento
                documento.save()
            else:
                # Crear nuevo documento
                documento = DocumentoIdentidad.objects.create(
                    tipo_documento=tipo_documento,
                    numero_documento=numero_documento,
                    extension=extension_documento
                )
                user.documento_identidad = documento
                user.save()
            
            # Actualizar DNI legacy si no se especifica
            if 'dni' not in validated_data:
                validated_data['dni'] = documento.documento_completo
        
        # Actualizar datos del socio
        return super().update(instance, validated_data)

class AporteSerializer(serializers.ModelSerializer):
    socio_info = serializers.CharField(source='socio.__str__', read_only=True)
    socio_nombre = serializers.CharField(source='socio.nombre_completo', read_only=True)
    
    class Meta:
        model = Aporte
        fields = [
            'id', 'socio', 'socio_info', 'socio_nombre', 'tipo_aporte', 'monto', 
            'descripcion', 'fecha_aporte', 'creado_en', 'actualizado_en'
        ]
        read_only_fields = ('id', 'creado_en', 'actualizado_en')