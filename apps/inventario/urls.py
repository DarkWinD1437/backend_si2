from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

app_name = 'inventario'

router = DefaultRouter()
router.register('', views.MovimientoInventarioViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
