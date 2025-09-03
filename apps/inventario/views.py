from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import MovimientoInventario
from .serializers import MovimientoInventarioSerializer

class MovimientoInventarioViewSet(viewsets.ModelViewSet):
    queryset = MovimientoInventario.objects.all()
    serializer_class = MovimientoInventarioSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo', 'producto']
    search_fields = ['descripcion']
    ordering_fields = ['fecha', 'cantidad']
    ordering = ['-fecha']

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        total_entradas = MovimientoInventario.objects.filter(tipo='ENTRADA').count()
        total_salidas = MovimientoInventario.objects.filter(tipo='SALIDA').count()
        return Response({
            'total_entradas': total_entradas,
            'total_salidas': total_salidas,
        })
