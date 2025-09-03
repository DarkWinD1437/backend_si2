from django.db import models

class Producto(models.Model):
    UNIDAD_CHOICES = [
        ('KG', 'Kilogramos'),
        ('L', 'Litros'),
        ('U', 'Unidades'),
    ]

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    unidad_medida = models.CharField(max_length=2, choices=UNIDAD_CHOICES)
    stock = models.PositiveIntegerField(default=0)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return self.nombre
