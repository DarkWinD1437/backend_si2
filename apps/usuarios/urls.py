from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views

app_name = 'usuarios'

router = DefaultRouter()
router.register('', views.UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
