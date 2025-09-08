from django.utils.deprecation import MiddlewareMixin
from .utils import obtener_datos_request
from .models import AuditoriaLog, SesionUsuario, TipoAccion
import threading

# Variable local del hilo para almacenar el contexto del request
_thread_local = threading.local()


class AuditoriaMiddleware(MiddlewareMixin):
    """Middleware para auditoría que captura información del request"""
    
    def process_request(self, request):
        # Almacenar información del request en el contexto del hilo
        ip, user_agent = obtener_datos_request(request)
        
        _thread_local.ip = ip
        _thread_local.user_agent = user_agent
        _thread_local.user = getattr(request, 'user', None)
        _thread_local.request = request
        
        # Actualizar última actividad de la sesión si existe
        if hasattr(request, 'user') and request.user.is_authenticated:
            session_key = request.session.session_key
            if session_key:
                try:
                    sesion = SesionUsuario.objects.get(
                        session_key=session_key,
                        usuario=request.user,
                        activa=True
                    )
                    sesion.save()  # Esto actualizará fecha_ultimo_acceso por auto_now=True
                except SesionUsuario.DoesNotExist:
                    pass
    
    def process_response(self, request, response):
        # Limpiar el contexto del hilo
        for attr in ['ip', 'user_agent', 'user', 'request']:
            if hasattr(_thread_local, attr):
                delattr(_thread_local, attr)
        
        return response


def get_current_request():
    """Obtiene el request actual del contexto del hilo"""
    return getattr(_thread_local, 'request', None)


def get_current_user():
    """Obtiene el usuario actual del contexto del hilo"""
    return getattr(_thread_local, 'user', None)


def get_current_ip():
    """Obtiene la IP actual del contexto del hilo"""
    return getattr(_thread_local, 'ip', None)


def get_current_user_agent():
    """Obtiene el User-Agent actual del contexto del hilo"""
    return getattr(_thread_local, 'user_agent', None)
