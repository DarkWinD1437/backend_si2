from django.db import models
from apps.usuarios.models import User

class Socio(models.Model):
    TIPO_SOCIO_CHOICES = [
        ('PRODUCTOR', 'Productor'),
        ('CONSUMIDOR', 'Consumidor'),
        ('TRABAJADOR', 'Trabajador'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    tipo_socio = models.CharField(max_length=10, choices=TIPO_SOCIO_CHOICES)
    dni = models.CharField(max_length=20, unique=True)
    direccion = models.TextField()
    telefono = models.CharField(max_length=15)
    fecha_ingreso = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Socio'
        verbose_name_plural = 'Socios'
        ordering = ['-fecha_ingreso']

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.get_tipo_socio_display()}"

class Aporte(models.Model):
    TIPO_APORTE_CHOICES = [
        ('ECONOMICO', 'Económico'),
        ('TRABAJO', 'Trabajo'),
        ('PRODUCTO', 'Producto'),
    ]

    socio = models.ForeignKey(Socio, on_delete=models.CASCADE, related_name='aportes')
    tipo_aporte = models.CharField(max_length=10, choices=TIPO_APORTE_CHOICES)
    monto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Aporte'
        verbose_name_plural = 'Aportes'
        ordering = ['-fecha']

    def __str__(self):
        return f"Aporte de {self.socio.usuario.get_full_name()} - {self.get_tipo_aporte_display()}"
