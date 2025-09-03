from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Socio, Aporte
from .serializers import SocioSerializer, AporteSerializer

class SocioViewSet(viewsets.ModelViewSet):
    queryset = Socio.objects.all()
    serializer_class = SocioSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo_socio', 'activo']
    search_fields = ['usuario__first_name', 'usuario__last_name', 'dni']
    ordering_fields = ['fecha_ingreso']
    ordering = ['-fecha_ingreso']

    @action(detail=True)
    def aportes(self, request, pk=None):
        socio = self.get_object()
        aportes = socio.aportes.all()
        serializer = AporteSerializer(aportes, many=True)
        return Response(serializer.data)

class AporteViewSet(viewsets.ModelViewSet):
    queryset = Aporte.objects.all()
    serializer_class = AporteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo_aporte', 'socio']
    search_fields = ['descripcion']
    ordering_fields = ['fecha', 'monto']
    ordering = ['-fecha']
