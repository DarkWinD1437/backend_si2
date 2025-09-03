from django.db import models
from apps.productos.models import Producto

class MovimientoInventario(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
    ]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=7, choices=TIPO_CHOICES)
    cantidad = models.PositiveIntegerField()
    descripcion = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        ordering = ['-fecha']

    def save(self, *args, **kwargs):
        if self.tipo == 'ENTRADA':
            self.producto.stock += self.cantidad
        elif self.tipo == 'SALIDA':
            if self.producto.stock < self.cantidad:
                raise ValueError('No hay suficiente stock disponible')
            self.producto.stock -= self.cantidad
        self.producto.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_tipo_display()} de {self.cantidad} {self.producto.get_unidad_medida_display()} de {self.producto.nombre}"
