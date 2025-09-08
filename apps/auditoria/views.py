from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import AuditoriaLog, SesionUsuario
from .serializers import AuditoriaLogSerializer, SesionUsuarioSerializer


class AuditoriaLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar logs de auditoría"""
    
    queryset = AuditoriaLog.objects.all().select_related('usuario', 'content_type')
    serializer_class = AuditoriaLogSerializer
    permission_classes = [permissions.IsAdminUser]
    
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['accion', 'exito', 'content_type']
    search_fields = ['usuario__email', 'descripcion', 'direccion_ip']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Endpoint para obtener estadísticas de auditoría"""
        
        # Parámetros de fecha
        dias = int(request.query_params.get('dias', 30))
        fecha_desde = timezone.now() - timedelta(days=dias)
        
        queryset = self.get_queryset().filter(timestamp__gte=fecha_desde)
        
        # Estadísticas por acción
        stats_accion = queryset.values('accion').annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Estadísticas por usuario
        stats_usuario = queryset.exclude(usuario__isnull=True).values(
            'usuario__email'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        # Estadísticas por día
        stats_por_dia = queryset.extra(
            select={'dia': 'date(timestamp)'}
        ).values('dia').annotate(
            total=Count('id'),
            exitosos=Count('id', filter=Q(exito=True)),
            fallidos=Count('id', filter=Q(exito=False))
        ).order_by('dia')
        
        # Intentos de login fallidos recientes
        login_fallidos = queryset.filter(
            accion='LOGIN_FAILED',
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).values('direccion_ip').annotate(
            intentos=Count('id')
        ).order_by('-intentos')[:10]
        
        return Response({
            'periodo_dias': dias,
            'total_eventos': queryset.count(),
            'estadisticas_por_accion': stats_accion,
            'usuarios_mas_activos': stats_usuario,
            'actividad_por_dia': list(stats_por_dia),
            'intentos_login_fallidos_24h': list(login_fallidos)
        })
    
    @action(detail=False, methods=['get'])
    def mis_logs(self, request):
        """Endpoint para que un usuario vea sus propios logs"""
        self.permission_classes = [permissions.IsAuthenticated]
        self.check_permissions(request)
        
        queryset = self.get_queryset().filter(usuario=request.user)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SesionUsuarioViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para consultar sesiones de usuario"""
    
    queryset = SesionUsuario.objects.all().select_related('usuario')
    serializer_class = SesionUsuarioSerializer
    permission_classes = [permissions.IsAdminUser]
    
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['activa', 'usuario']
    ordering_fields = ['fecha_inicio', 'fecha_ultimo_acceso']
    ordering = ['-fecha_inicio']
    
    @action(detail=False, methods=['get'])
    def activas(self, request):
        """Endpoint para obtener sesiones activas"""
        sesiones_activas = self.get_queryset().filter(activa=True)
        serializer = self.get_serializer(sesiones_activas, many=True)
        return Response({
            'total': sesiones_activas.count(),
            'sesiones': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def mis_sesiones(self, request):
        """Endpoint para que un usuario vea sus propias sesiones"""
        self.permission_classes = [permissions.IsAuthenticated]
        self.check_permissions(request)
        
        queryset = self.get_queryset().filter(usuario=request.user)
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
