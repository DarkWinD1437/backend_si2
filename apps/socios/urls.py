# urls.py
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

app_name = 'socios'

router = DefaultRouter()
router.register('socios', views.SocioViewSet, basename='socio')
router.register('aportes', views.AporteViewSet, basename='aporte')

urlpatterns = [
    path('', include(router.urls)),
]