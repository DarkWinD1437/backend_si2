# views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum
from django.utils import timezone
from .models import Socio, Aporte
from .serializers import (
    SocioSerializer, SocioCreateSerializer, 
    SocioUpdateSerializer, AporteSerializer
)

class SocioViewSet(viewsets.ModelViewSet):
    queryset = Socio.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo_socio', 'activo']
    search_fields = [
        'usuario__first_name', 'usuario__last_name', 
        'dni', 'usuario__email', 'telefono'
    ]
    ordering_fields = [
        'fecha_ingreso', 'usuario__first_name', 
        'usuario__last_name', 'creado_en'
    ]
    ordering = ['-creado_en']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SocioCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SocioUpdateSerializer
        return SocioSerializer

    def get_queryset(self):
        queryset = Socio.objects.all()
        
        # Filtrar por estado activo/inactivo
        estado = self.request.query_params.get('estado', None)
        if estado is not None:
            if estado.lower() == 'true':
                queryset = queryset.filter(activo=True)
            elif estado.lower() == 'false':
                queryset = queryset.filter(activo=False)
        
        return queryset

    @action(detail=True, methods=['get'])
    def aportes(self, request, pk=None):
        socio = self.get_object()
        aportes = socio.aportes.all()
        serializer = AporteSerializer(aportes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def toggle_activo(self, request, pk=None):
        socio = self.get_object()
        socio.activo = not socio.activo
        socio.save()
        
        return Response({
            'message': f'Socio {"activado" if socio.activo else "desactivado"} correctamente',
            'activo': socio.activo
        })

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        total = Socio.objects.count()
        activos = Socio.objects.filter(activo=True).count()
        inactivos = Socio.objects.filter(activo=False).count()
        
        # Estadísticas por tipo de socio
        por_tipo = Socio.objects.values('tipo_socio').annotate(
            total=Count('id'),
            activos=Count('id', filter=Q(activo=True)),
            inactivos=Count('id', filter=Q(activo=False))
        )
        
        return Response({
            'total_socios': total,
            'socios_activos': activos,
            'socios_inactivos': inactivos,
            'por_tipo_socio': por_tipo
        })

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        if not query:
            return Response({'error': 'Parámetro de búsqueda requerido'}, status=400)
        
        socios = Socio.objects.filter(
            Q(usuario__first_name__icontains=query) |
            Q(usuario__last_name__icontains=query) |
            Q(dni__icontains=query) |
            Q(usuario__email__icontains=query) |
            Q(telefono__icontains=query)
        )
        
        serializer = SocioSerializer(socios, many=True)
        return Response(serializer.data)

class AporteViewSet(viewsets.ModelViewSet):
    queryset = Aporte.objects.all()
    serializer_class = AporteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo_aporte', 'socio', 'fecha_aporte']
    search_fields = [
        'descripcion', 'socio__usuario__first_name', 
        'socio__usuario__last_name', 'socio__dni'
    ]
    ordering_fields = ['fecha_aporte', 'monto', 'creado_en']
    ordering = ['-fecha_aporte']

    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        # Estadísticas de aportes
        total_aportes = Aporte.objects.count()
        total_monto = Aporte.objects.aggregate(total=Sum('monto'))['total'] or 0
        
        # Aportes por tipo
        por_tipo = Aporte.objects.values('tipo_aporte').annotate(
            cantidad=Count('id'),
            monto_total=Sum('monto')
        )
        
        # Aportes últimos 30 días
        ultimos_30_dias = Aporte.objects.filter(
            fecha_aporte__gte=timezone.now().date() - timezone.timedelta(days=30)
        ).count()
        
        return Response({
            'total_aportes': total_aportes,
            'total_monto': float(total_monto),
            'aportes_ultimos_30_dias': ultimos_30_dias,
            'por_tipo_aporte': por_tipo
        })