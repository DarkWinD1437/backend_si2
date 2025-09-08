from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditoriaLogViewSet, SesionUsuarioViewSet

router = DefaultRouter()
router.register(r'logs', AuditoriaLogViewSet)
router.register(r'sesiones', SesionUsuarioViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
