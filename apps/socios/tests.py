# tests.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Socio, Aporte
from .serializers import SocioSerializer, AporteSerializer

User = get_user_model()

class SocioModelTest(TestCase):
    """Pruebas para el modelo Socio"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Juan',
            last_name='Pérez',
            email='juan@ejemplo.com'
        )
        
        self.socio_data = {
            'usuario': self.user,
            'tipo_socio': 'PRODUCTOR',
            'dni': '12345678',
            'direccion': 'Calle Test 123, Lima',
            'telefono': '987654321',
            'activo': True,
            'notas': 'Socio de prueba'
        }

    def test_crear_socio_valido(self):
        """Test: Crear socio con datos válidos"""
        socio = Socio.objects.create(**self.socio_data)
        
        self.assertEqual(socio.__str__(), 'Juan Pérez - Productor')
        self.assertEqual(socio.nombre_completo(), 'Juan Pérez')
        self.assertEqual(socio.email(), 'juan@ejemplo.com')
        self.assertTrue(socio.esta_activo())
        self.assertEqual(socio.dni, '12345678')

    def test_dni_duplicado_error(self):
        """Test: No permitir DNI duplicado"""
        Socio.objects.create(**self.socio_data)
        
        # Crear segundo usuario
        user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123',
            first_name='Maria',
            last_name='Gomez',
            email='maria@ejemplo.com'
        )
        
        # Intentar crear socio con mismo DNI debería fallar
        with self.assertRaises(ValidationError):
            socio2 = Socio(
                usuario=user2,
                tipo_socio='CONSUMIDOR',
                dni='12345678',  # Mismo DNI
                direccion='Test',
                telefono='987654321'
            )
            socio2.full_clean()  # Forzar validación

    def test_dni_solo_numeros(self):
        """Test: Validar que DNI solo contenga números"""
        with self.assertRaises(ValidationError):
            socio = Socio(
                usuario=self.user,
                tipo_socio='PRODUCTOR',
                dni='123ABC78',  # DNI con letras
                direccion='Test',
                telefono='987654321'
            )
            socio.full_clean()

    def test_telefono_solo_numeros(self):
        """Test: Validar que teléfono solo contenga números"""
        with self.assertRaises(ValidationError):
            socio = Socio(
                usuario=self.user,
                tipo_socio='PRODUCTOR',
                dni='87654321',
                direccion='Test',
                telefono='9876ABC321'  # Teléfono con letras
            )
            socio.full_clean()

    def test_cambiar_estado_socio(self):
        """Test: Cambiar estado activo/inactivo del socio"""
        socio = Socio.objects.create(**self.socio_data)
        self.assertTrue(socio.activo)
        
        socio.activo = False
        socio.save()
        self.assertFalse(socio.activo)

class AporteModelTest(TestCase):
    """Pruebas para el modelo Aporte"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Carlos',
            last_name='Lopez'
        )
        
        self.socio = Socio.objects.create(
            usuario=self.user,
            tipo_socio='TRABAJADOR',
            dni='87654321',
            direccion='Av. Ejemplo 456',
            telefono='123456789',
            activo=True
        )

    def test_crear_aporte_economico(self):
        """Test: Crear aporte económico"""
        aporte = Aporte.objects.create(
            socio=self.socio,
            tipo_aporte='ECONOMICO',
            monto=150.50,
            descripcion='Aporte mensual enero',
            fecha_aporte='2024-01-15'
        )
        
        self.assertEqual(aporte.__str__(), 'Aporte de Carlos Lopez - Económico')
        self.assertEqual(aporte.monto, 150.50)

    def test_crear_aporte_trabajo(self):
        """Test: Crear aporte de trabajo (sin monto)"""
        aporte = Aporte.objects.create(
            socio=self.socio,
            tipo_aporte='TRABAJO',
            descripcion='Jornada de trabajo comunitario',
            fecha_aporte='2024-01-16'
        )
        
        self.assertIsNone(aporte.monto)
        self.assertEqual(aporte.tipo_aporte, 'TRABAJO')

class SocioAPITest(APITestCase):
    """Pruebas para la API de Socios"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='adminuser',
            password='adminpass123',
            first_name='Admin',
            last_name='User',
            email='admin@ejemplo.com'
        )
        
        self.client = Client()
        self.client.login(username='adminuser', password='adminpass123')
        
        self.socio_data = {
            'username': 'nuevosocio',
            'password': 'sociopass123',
            'first_name': 'Ana',
            'last_name': 'Torres',
            'email': 'ana@ejemplo.com',
            'tipo_socio': 'CONSUMIDOR',
            'dni': '11223344',
            'direccion': 'Calle Nueva 789',
            'telefono': '999888777',
            'notas': 'Nuevo socio de prueba'
        }

    def test_listar_socios(self):
        """Test: Listar todos los socios"""
        response = self.client.get(reverse('socios:socio-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_crear_socio_api(self):
        """Test: Crear socio mediante API"""
        response = self.client.post(
            reverse('socios:socio-list'),
            data=self.socio_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Socio.objects.count(), 1)
        self.assertEqual(Socio.objects.first().dni, '11223344')

    def test_obtener_socio_por_id(self):
        """Test: Obtener socio específico por ID"""
        # Primero crear el socio
        self.client.post(reverse('socios:socio-list'), data=self.socio_data, format='json')
        socio = Socio.objects.first()
        
        response = self.client.get(reverse('socios:socio-detail', kwargs={'pk': socio.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dni'], '11223344')

    def test_actualizar_socio(self):
        """Test: Actualizar datos de socio"""
        self.client.post(reverse('socios:socio-list'), data=self.socio_data, format='json')
        socio = Socio.objects.first()
        
        update_data = {
            'first_name': 'Ana Maria',  # Actualizar nombre
            'direccion': 'Nueva dirección 123',
            'telefono': '111222333'
        }
        
        response = self.client.patch(
            reverse('socios:socio-detail', kwargs={'pk': socio.pk}),
            data=update_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        socio.refresh_from_db()
        self.assertEqual(socio.usuario.first_name, 'Ana Maria')
        self.assertEqual(socio.telefono, '111222333')

    def test_cambiar_estado_socio_api(self):
        """Test: Cambiar estado activo/inactivo mediante API"""
        self.client.post(reverse('socios:socio-list'), data=self.socio_data, format='json')
        socio = Socio.objects.first()
        
        response = self.client.patch(
            reverse('socios:socio-toggle-activo', kwargs={'pk': socio.pk}),
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        socio.refresh_from_db()
        self.assertFalse(socio.activo)

    def test_estadisticas_socios(self):
        """Test: Obtener estadísticas de socios"""
        # Crear varios socios
        for i in range(3):
            data = self.socio_data.copy()
            data['dni'] = f'1000000{i}'
            data['username'] = f'user{i}'
            data['email'] = f'user{i}@ejemplo.com'
            self.client.post(reverse('socios:socio-list'), data=data, format='json')
        
        response = self.client.get(reverse('socios:socio-estadisticas'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_socios'], 3)

class AporteAPITest(APITestCase):
    """Pruebas para la API de Aportes"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.socio = Socio.objects.create(
            usuario=self.user,
            tipo_socio='PRODUCTOR',
            dni='12345678',
            direccion='Test Address',
            telefono='999888777',
            activo=True
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        self.aporte_data = {
            'socio': self.socio.pk,
            'tipo_aporte': 'ECONOMICO',
            'monto': 200.00,
            'descripcion': 'Aporte económico inicial',
            'fecha_aporte': '2024-01-20'
        }

    def test_crear_aporte_api(self):
        """Test: Crear aporte mediante API"""
        response = self.client.post(
            reverse('socios:aporte-list'),
            data=self.aporte_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Aporte.objects.count(), 1)
        self.assertEqual(Aporte.objects.first().monto, 200.00)

    def test_listar_aportes_por_socio(self):
        """Test: Listar aportes de un socio específico"""
        # Crear algunos aportes
        Aporte.objects.create(
            socio=self.socio,
            tipo_aporte='ECONOMICO',
            monto=100.00,
            descripcion='Aporte 1',
            fecha_aporte='2024-01-01'
        )
        Aporte.objects.create(
            socio=self.socio,
            tipo_aporte='TRABAJO',
            descripcion='Aporte 2',
            fecha_aporte='2024-01-02'
        )
        
        response = self.client.get(reverse('socios:socio-aportes', kwargs={'pk': self.socio.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_estadisticas_aportes(self):
        """Test: Obtener estadísticas de aportes"""
        # Crear varios aportes
        for i in range(3):
            Aporte.objects.create(
                socio=self.socio,
                tipo_aporte='ECONOMICO',
                monto=100.00 * (i + 1),
                descripcion=f'Aporte {i + 1}',
                fecha_aporte=f'2024-01-{10 + i}'
            )
        
        response = self.client.get(reverse('socios:aporte-estadisticas'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_aportes'], 3)
        self.assertEqual(response.data['total_monto'], 600.00)

# Comando para ejecutar las pruebas: 
# python manage.py test apps.socios --verbosity=2