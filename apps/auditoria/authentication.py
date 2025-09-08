from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from apps.auditoria.models import AuditoriaLog, TipoAccion
from apps.auditoria.utils import obtener_datos_request


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personalizado para agregar información adicional al token"""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Agregar información personalizada al token
        token['email'] = user.email
        token['is_staff'] = user.is_staff
        
        return token


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista personalizada para login con auditoría"""
    
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        # Obtener datos del request
        ip, user_agent = obtener_datos_request(request)
        email = request.data.get('email', '')
        
        # Intentar autenticar
        user = authenticate(
            request=request,
            username=email,
            password=request.data.get('password', '')
        )
        
        if user is not None:
            # Login exitoso - el signal user_logged_in se encargará del log
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                # Agregar información adicional a la respuesta
                response.data['user'] = {
                    'id': user.id,
                    'email': user.email,
                    'is_staff': user.is_staff,
                    'date_joined': user.date_joined.isoformat()
                }
            
            return response
        else:
            # Login fallido - se registra automáticamente por el signal
            return Response(
                {'detail': 'Credenciales inválidas'},
                status=status.HTTP_401_UNAUTHORIZED
            )
