from django.core.serializers import serialize
from django.forms.models import model_to_dict
import json


def obtener_datos_request(request):
    """Extrae la IP y User-Agent del request"""
    # Obtener IP (considerando proxies)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    
    # Obtener User-Agent
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    return ip, user_agent


def serializar_objeto(instance):
    """Serializa un objeto de modelo a diccionario JSON"""
    try:
        # Convertir modelo a diccionario
        data = model_to_dict(instance)
        
        # Convertir valores no serializables
        for key, value in data.items():
            if hasattr(value, 'isoformat'):  # DateTime objects
                data[key] = value.isoformat()
            elif hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool, type(None))):
                data[key] = str(value)
        
        return data
    except Exception as e:
        return {'error': f'No se pudo serializar: {str(e)}'}


def obtener_usuario_actual():
    """Obtiene el usuario actual del contexto (si está disponible)"""
    # Esta función puede ser mejorada usando threading.local()
    # o un middleware personalizado para almacenar el usuario actual
    return None


class AuditMiddleware:
    """Middleware para capturar el usuario actual en las operaciones"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Almacenar el usuario en el request para que sea accesible
        # en los signals
        if hasattr(request, 'user') and request.user.is_authenticated:
            request._audit_user = request.user
        
        response = self.get_response(request)
        return response
