from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from apps.usuarios.models import User
from apps.usuarios.document_models import DocumentoIdentidad, TipoDocumento
from apps.usuarios.validation_serializers import (
    DocumentoIdentidadSerializer, 
    UserExtendedSerializer,
    ValidacionDuplicadosSerializer
)


class DocumentoIdentidadViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar documentos de identidad"""
    
    queryset = DocumentoIdentidad.objects.filter(activo=True)
    serializer_class = DocumentoIdentidadSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Permisos específicos por acción"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAdminUser]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def validar_duplicado(self, request):
        """Endpoint para validar si un documento ya existe"""
        serializer = ValidacionDuplicadosSerializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            # Si llega aquí, no hay duplicados
            return Response({
                'valido': True,
                'mensaje': 'No se encontraron duplicados',
                'info': serializer.validated_data.get('_validation_info', {})
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Hay duplicados o errores de validación
            return Response({
                'valido': False,
                'errores': serializer.errors if hasattr(serializer, 'errors') else str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def buscar(self, request):
        """Buscar documentos por número o tipo"""
        numero = request.query_params.get('numero', '')
        tipo = request.query_params.get('tipo', '')
        
        queryset = self.get_queryset()
        
        if numero:
            numero_normalizado = DocumentoIdentidad.normalizar_numero(numero)
            queryset = queryset.filter(numero_documento__icontains=numero_normalizado)
        
        if tipo:
            queryset = queryset.filter(tipo_documento=tipo)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'results': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """Estadísticas de documentos por tipo"""
        stats = {}
        
        for tipo_choice in TipoDocumento.choices:
            tipo_codigo = tipo_choice[0]
            tipo_nombre = tipo_choice[1]
            
            count = self.get_queryset().filter(tipo_documento=tipo_codigo).count()
            stats[tipo_codigo] = {
                'nombre': tipo_nombre,
                'cantidad': count
            }
        
        return Response({
            'total_documentos': self.get_queryset().count(),
            'por_tipo': stats
        })


class ValidacionDuplicadosViewSet(viewsets.ViewSet):
    """ViewSet específico para validaciones de duplicados"""
    
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def verificar_email(self, request):
        """Verificar si un email ya está registrado"""
        email = request.data.get('email', '').strip().lower()
        
        if not email:
            return Response({
                'error': 'Email es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        existe = User.objects.filter(email=email).exists()
        
        return Response({
            'email': email,
            'existe': existe,
            'disponible': not existe,
            'mensaje': 'Email ya registrado' if existe else 'Email disponible'
        })
    
    @action(detail=False, methods=['post'])
    def verificar_documento(self, request):
        """Verificar si un documento ya está registrado"""
        tipo_documento = request.data.get('tipo_documento', TipoDocumento.CI)
        numero_documento = request.data.get('numero_documento', '').strip()
        extension = request.data.get('extension', '').strip() or None
        
        if not numero_documento:
            return Response({
                'error': 'Número de documento es requerido'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Normalizar número
        numero_normalizado = DocumentoIdentidad.normalizar_numero(numero_documento)
        
        # Verificar existencia
        existe = DocumentoIdentidad.existe_documento(
            tipo_documento=tipo_documento,
            numero_documento=numero_normalizado,
            extension=extension
        )
        
        documento_completo = numero_normalizado
        if extension:
            documento_completo += f"-{extension}"
        
        response_data = {
            'tipo_documento': tipo_documento,
            'numero_documento': numero_normalizado,
            'extension': extension,
            'documento_completo': documento_completo,
            'existe': existe,
            'disponible': not existe,
            'mensaje': f'Documento ya registrado' if existe else 'Documento disponible'
        }
        
        # Si existe, buscar información adicional
        if existe:
            try:
                documento = DocumentoIdentidad.objects.get(
                    tipo_documento=tipo_documento,
                    numero_documento=numero_normalizado,
                    extension=extension,
                    activo=True
                )
                
                # Buscar usuario asociado
                if hasattr(documento, 'usuario') and documento.usuario:
                    response_data['usuario_asociado'] = {
                        'id': documento.usuario.id,
                        'email': documento.usuario.email,
                        'nombre': documento.usuario.get_full_name()
                    }
                
                # Buscar socio asociado
                if hasattr(documento, 'usuario') and documento.usuario and hasattr(documento.usuario, 'socio_perfil'):
                    socio = documento.usuario.socio_perfil
                    response_data['socio_asociado'] = {
                        'id': socio.id,
                        'tipo_socio': socio.get_tipo_socio_display(),
                        'activo': socio.activo
                    }
                
            except DocumentoIdentidad.DoesNotExist:
                pass
        
        return Response(response_data)
    
    @action(detail=False, methods=['post'])
    def verificar_completo(self, request):
        """Verificar email y documento en una sola consulta"""
        serializer = ValidacionDuplicadosSerializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            return Response({
                'valido': True,
                'mensaje': 'Todos los datos están disponibles',
                'info': serializer.validated_data.get('_validation_info', {})
            })
        
        except Exception:
            return Response({
                'valido': False,
                'errores': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def buscar_por_criterio(self, request):
        """Buscar usuarios/socios por diferentes criterios"""
        email = request.query_params.get('email', '')
        numero_documento = request.query_params.get('numero_documento', '')
        nombre = request.query_params.get('nombre', '')
        
        # Buscar usuarios
        usuarios_query = User.objects.all()
        
        if email:
            usuarios_query = usuarios_query.filter(email__icontains=email)
        
        if numero_documento:
            numero_normalizado = DocumentoIdentidad.normalizar_numero(numero_documento)
            usuarios_query = usuarios_query.filter(
                documento_identidad__numero_documento__icontains=numero_normalizado
            )
        
        if nombre:
            usuarios_query = usuarios_query.filter(
                Q(first_name__icontains=nombre) | 
                Q(last_name__icontains=nombre)
            )
        
        # Limitar resultados
        usuarios = usuarios_query.select_related('documento_identidad')[:20]
        
        resultados = []
        for usuario in usuarios:
            resultado = {
                'id': usuario.id,
                'email': usuario.email,
                'nombre_completo': usuario.get_full_name(),
                'documento': None,
                'es_socio': False,
                'socio_info': None
            }
            
            if usuario.documento_identidad:
                resultado['documento'] = {
                    'tipo': usuario.documento_identidad.get_tipo_documento_display(),
                    'numero': usuario.documento_identidad.documento_completo
                }
            
            # Verificar si es socio
            if hasattr(usuario, 'socio_perfil'):
                resultado['es_socio'] = True
                socio = usuario.socio_perfil
                resultado['socio_info'] = {
                    'id': socio.id,
                    'tipo_socio': socio.get_tipo_socio_display(),
                    'activo': socio.activo,
                    'fecha_ingreso': socio.fecha_ingreso
                }
            
            resultados.append(resultado)
        
        return Response({
            'total_encontrados': len(resultados),
            'resultados': resultados
        })
