from rest_framework import serializers
from .models import Socio, Aporte
from apps.usuarios.serializers import UserSerializer

class SocioSerializer(serializers.ModelSerializer):
    usuario = UserSerializer()

    class Meta:
        model = Socio
        fields = '__all__'
        read_only_fields = ('fecha_ingreso',)

    def create(self, validated_data):
        usuario_data = validated_data.pop('usuario')
        user = UserSerializer().create(usuario_data)
        socio = Socio.objects.create(usuario=user, **validated_data)
        return socio

class AporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aporte
        fields = '__all__'
        read_only_fields = ('fecha',)
