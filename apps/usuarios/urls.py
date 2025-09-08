from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views
from .validation_views import DocumentoIdentidadViewSet, ValidacionDuplicadosViewSet

app_name = 'usuarios'

router = DefaultRouter()
router.register('', views.UserViewSet)
router.register('documentos', DocumentoIdentidadViewSet)
router.register('validaciones', ValidacionDuplicadosViewSet, basename='validaciones')

urlpatterns = [
    path('', include(router.urls)),
]
