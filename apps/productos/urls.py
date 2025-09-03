from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

app_name = 'productos'

router = DefaultRouter()
router.register('', views.ProductoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
