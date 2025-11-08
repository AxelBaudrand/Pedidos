from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Modelos para Mesas del restaurante
class Mesa(models.Model):
    ESTADO_MESA = [
        ('libre', 'Libre'),
        ('ocupada', 'Ocupada'),
    ]
    numero = models.IntegerField(unique=True, verbose_name="Número de mesa")
    estado = models.CharField(max_length=10, choices=ESTADO_MESA, default='libre')

    def __str__(self):
        return f"Mesa {self.numero} ({self.get_estado_display()})"

# Modelos para Platos del menú
class Plato(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    disponible = models.BooleanField(default=True, verbose_name="Disponible")  # True si hay stock disponible

    def __str__(self):
        return self.nombre

# Modelo Pedido (orden de restaurante)
class Pedido(models.Model):
    ESTADO_PEDIDO = [
        ('en_elaboracion', 'En elaboración'),
        ('en_cocina', 'En cocina'),
        ('listo', 'Listo'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name='pedidos')
    mesero = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Mesero", related_name='pedidos')
    estado = models.CharField(max_length=20, choices=ESTADO_PEDIDO, default='en_elaboracion')
    codigo = models.CharField(max_length=30, unique=True, blank=True)  # Código único del pedido (ej: PED-001-20231104)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_envio = models.DateTimeField(null=True, blank=True, verbose_name="Enviado a cocina en")
    fecha_entrega = models.DateTimeField(null=True, blank=True, verbose_name="Entregado en")
    fecha_cancelacion = models.DateTimeField(null=True, blank=True, verbose_name="Cancelado en")
    razon_cancelacion = models.TextField(null=True, blank=True, verbose_name="Razón de cancelación")

    def __str__(self):
        return self.codigo or f"Pedido {self.id}"

    def save(self, *args, **kwargs):
        # Generar código único al crear (si no existe)
        if not self.codigo:
            super().save(*args, **kwargs)  # guardar para obtener self.id
            fecha = self.fecha_creacion or timezone.now()
            self.codigo = f"PED-{self.id:03d}-{fecha.strftime('%Y%m%d')}"
            # Actualizar solo el campo código
            super().save(update_fields=['codigo'])
        else:
            super().save(*args, **kwargs)

    @property
    def total(self):
        """Calcula el total del pedido sumando subtotal de cada plato."""
        return sum(item.cantidad * item.plato.precio for item in self.platos.all())

# Modelo intermedio para los platos dentro de cada Pedido
class PlatoPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='platos')
    plato = models.ForeignKey(Plato, on_delete=models.PROTECT, related_name='pedidos_items')
    cantidad = models.PositiveIntegerField(default=1)
    observaciones = models.CharField(max_length=200, null=True, blank=True, verbose_name="Observaciones")

    def __str__(self):
        return f"{self.cantidad} x {self.plato.nombre} (Pedido {self.pedido.codigo})"
