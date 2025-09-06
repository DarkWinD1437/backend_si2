# serializers.py
from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import Socio, Aporte

class SocioSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(source='usuario.get_full_name', read_only=True)
    email = serializers.EmailField(source='usuario.email', read_only=True)
    username = serializers.CharField(source='usuario.username', read_only=True)
    
    class Meta:
        model = Socio
        fields = [
            'id', 'usuario', 'nombre_completo', 'email', 'username', 'tipo_socio', 
            'dni', 'direccion', 'telefono', 'fecha_ingreso', 'activo', 'notas',
            'creado_en', 'actualizado_en'
        ]
        read_only_fields = ('id', 'usuario', 'fecha_ingreso', 'creado_en', 'actualizado_en')

class SocioCreateSerializer(serializers.ModelSerializer):
    # Campos para crear el usuario
    username = serializers.CharField(write_only=True, max_length=150)
    password = serializers.CharField(write_only=True, max_length=128)
    first_name = serializers.CharField(write_only=True, max_length=30)
    last_name = serializers.CharField(write_only=True, max_length=150)
    email = serializers.EmailField(write_only=True, max_length=254)
    
    class Meta:
        model = Socio
        fields = [
            'username', 'password', 'first_name', 'last_name', 'email',
            'tipo_socio', 'dni', 'direccion', 'telefono', 'notas'
        ]
    
    def validate_dni(self, value):
        if Socio.objects.filter(dni=value).exists():
            raise serializers.ValidationError("Este DNI ya está registrado")
        return value
    
    def validate_username(self, value):
        from apps.usuarios.models import User
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este username ya está en uso")
        return value

    def create(self, validated_data):
        from apps.usuarios.models import User
        
        user_data = {
            'username': validated_data.pop('username'),
            'password': make_password(validated_data.pop('password')),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'email': validated_data.pop('email')
        }
        
        user = User.objects.create(**user_data)
        socio = Socio.objects.create(usuario=user, **validated_data)
        return socio

class SocioUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(write_only=True, required=False, max_length=30)
    last_name = serializers.CharField(write_only=True, required=False, max_length=150)
    email = serializers.EmailField(write_only=True, required=False, max_length=254)
    
    class Meta:
        model = Socio
        fields = [
            'first_name', 'last_name', 'email',
            'tipo_socio', 'dni', 'direccion', 'telefono', 'notas', 'activo'
        ]
    
    def update(self, instance, validated_data):
        user = instance.usuario
        
        # Actualizar datos del usuario
        user_fields = ['first_name', 'last_name', 'email']
        for field in user_fields:
            if field in validated_data:
                setattr(user, field, validated_data.pop(field))
        user.save()
        
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