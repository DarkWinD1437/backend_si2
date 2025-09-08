from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from apps.usuarios.models import User
from apps.usuarios.document_models import DocumentoIdentidad, TipoDocumento


class DocumentoIdentidadSerializer(serializers.ModelSerializer):
    """Serializer para documentos de identidad"""
    
    documento_completo = serializers.CharField(read_only=True)
    tipo_documento_display = serializers.CharField(source='get_tipo_documento_display', read_only=True)
    
    class Meta:
        model = DocumentoIdentidad
        fields = [
            'id', 'tipo_documento', 'tipo_documento_display', 'numero_documento', 
            'extension', 'documento_completo', 'activo', 'fecha_registro'
        ]
        read_only_fields = ['id', 'fecha_registro']
    
    def validate(self, attrs):
        """Validación cruzada"""
        tipo_documento = attrs.get('tipo_documento')
        numero_documento = attrs.get('numero_documento')
        extension = attrs.get('extension')
        
        # Normalizar número de documento
        if numero_documento:
            attrs['numero_documento'] = DocumentoIdentidad.normalizar_numero(numero_documento)
        
        # Validar si ya existe el documento
        instance_pk = self.instance.pk if self.instance else None
        
        if DocumentoIdentidad.existe_documento(
            tipo_documento=tipo_documento,
            numero_documento=attrs['numero_documento'],
            extension=extension,
            excluir_pk=instance_pk
        ):
            documento_completo = attrs['numero_documento']
            if extension:
                documento_completo += f"-{extension}"
            
            raise serializers.ValidationError(
                f"Ya existe un {TipoDocumento(tipo_documento).label} con número {documento_completo}"
            )
        
        return attrs


class UserExtendedSerializer(serializers.ModelSerializer):
    """Serializer extendido para usuarios con documento de identidad"""
    
    # Campos del documento (para crear/actualizar)
    tipo_documento = serializers.ChoiceField(
        choices=TipoDocumento.choices,
        write_only=True,
        required=False
    )
    numero_documento = serializers.CharField(
        max_length=20,
        write_only=True,
        required=False,
        help_text='Número del documento sin guiones ni espacios'
    )
    extension_documento = serializers.CharField(
        max_length=5,
        write_only=True,
        required=False,
        allow_blank=True,
        help_text='Extensión del documento (ej: 1A para CI)'
    )
    
    # Campos de lectura del documento
    documento_info = DocumentoIdentidadSerializer(source='documento_identidad', read_only=True)
    documento_numero = serializers.CharField(read_only=True)
    tipo_documento_display = serializers.CharField(source='tipo_documento', read_only=True)
    
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'username', 'password',
            'is_active', 'date_joined',
            'tipo_documento', 'numero_documento', 'extension_documento',
            'documento_info', 'documento_numero', 'tipo_documento_display'
        ]
        read_only_fields = ['id', 'date_joined', 'username']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }
    
    def validate_email(self, value):
        """Validar email único"""
        queryset = User.objects.filter(email=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise serializers.ValidationError("Ya existe un usuario con este email")
        
        return value
    
    def validate(self, attrs):
        """Validación cruzada"""
        # Si se proporcionan datos de documento, validar que estén completos
        tipo_documento = attrs.get('tipo_documento')
        numero_documento = attrs.get('numero_documento')
        
        if tipo_documento or numero_documento:
            if not (tipo_documento and numero_documento):
                raise serializers.ValidationError(
                    "Debe proporcionar tanto el tipo como el número de documento"
                )
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        """Crear usuario con documento de identidad"""
        # Extraer datos del documento
        tipo_documento = validated_data.pop('tipo_documento', None)
        numero_documento = validated_data.pop('numero_documento', None)
        extension_documento = validated_data.pop('extension_documento', None) or None
        
        # Crear el usuario
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        
        # Crear documento de identidad si se proporcionaron datos
        if tipo_documento and numero_documento:
            documento = DocumentoIdentidad.objects.create(
                tipo_documento=tipo_documento,
                numero_documento=numero_documento,
                extension=extension_documento
            )
            user.documento_identidad = documento
            user.save()
        
        return user
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """Actualizar usuario y documento de identidad"""
        # Extraer datos del documento
        tipo_documento = validated_data.pop('tipo_documento', None)
        numero_documento = validated_data.pop('numero_documento', None)
        extension_documento = validated_data.pop('extension_documento', None)
        
        # Actualizar password si se proporciona
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)
        
        # Actualizar campos del usuario
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Gestionar documento de identidad
        if tipo_documento and numero_documento:
            if instance.documento_identidad:
                # Actualizar documento existente
                documento = instance.documento_identidad
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
                instance.documento_identidad = documento
        
        instance.save()
        return instance


class ValidacionDuplicadosSerializer(serializers.Serializer):
    """Serializer para validar duplicados sin crear registros"""
    
    email = serializers.EmailField(required=False)
    tipo_documento = serializers.ChoiceField(choices=TipoDocumento.choices, required=False)
    numero_documento = serializers.CharField(max_length=20, required=False)
    extension_documento = serializers.CharField(max_length=5, required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validar duplicados y retornar información"""
        errores = {}
        info = {}
        
        # Validar email
        email = attrs.get('email')
        if email:
            if User.objects.filter(email=email).exists():
                errores['email'] = 'Este email ya está registrado'
            else:
                info['email'] = 'Email disponible'
        
        # Validar documento
        tipo_documento = attrs.get('tipo_documento')
        numero_documento = attrs.get('numero_documento')
        extension_documento = attrs.get('extension_documento') or None
        
        if tipo_documento and numero_documento:
            numero_normalizado = DocumentoIdentidad.normalizar_numero(numero_documento)
            
            if DocumentoIdentidad.existe_documento(
                tipo_documento=tipo_documento,
                numero_documento=numero_normalizado,
                extension=extension_documento
            ):
                documento_completo = numero_normalizado
                if extension_documento:
                    documento_completo += f"-{extension_documento}"
                
                errores['documento'] = f'Ya existe un {TipoDocumento(tipo_documento).label} con número {documento_completo}'
            else:
                info['documento'] = 'Documento disponible'
        
        # Si hay errores, lanzar excepción
        if errores:
            raise serializers.ValidationError(errores)
        
        # Si no hay errores, retornar información positiva
        attrs['_validation_info'] = info
        return attrs
