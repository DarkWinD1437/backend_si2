from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

app_name = 'socios'

router = DefaultRouter()
router.register('socios', views.SocioViewSet)
router.register('aportes', views.AporteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
