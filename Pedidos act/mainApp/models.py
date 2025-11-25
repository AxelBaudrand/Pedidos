from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from datetime import timedelta 

class Plato(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Plato")
    precio = models.DecimalField(max_digits=7, decimal_places=2, verbose_name="Precio")
    # ✅ Campo para relacionar con el plato en M1
    plato_id_m1 = models.IntegerField(null=True, blank=True, verbose_name="ID Plato en M1", help_text="ID del plato en el módulo de Menú")

    class Meta:
        verbose_name = "Plato de Menú"
        verbose_name_plural = "Platos de Menú"

    def __str__(self):
        return f"{self.nombre} (${self.precio})"

class DetallePedido(models.Model):
    pedido = models.ForeignKey('Pedidos', on_delete=models.CASCADE, related_name='detalles', verbose_name="Pedido")
    plato = models.ForeignKey(Plato, on_delete=models.PROTECT, verbose_name="Plato")
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad")

    class Meta:
        verbose_name = "Detalle del Pedido"
        verbose_name_plural = "Detalles del Pedido"
        unique_together = ('pedido', 'plato')

    def subtotal(self):
        return self.cantidad * self.plato.precio

    def __str__(self):
        return f"{self.cantidad} x {self.plato.nombre} para Pedido #{self.pedido.id}"


class Mesas(models.Model):
    numero = models.CharField(max_length=10, unique=True, verbose_name="Número de Mesa")
    ocupada = models.BooleanField(default=False, verbose_name="Ocupada")
    ubicacion = models.CharField(max_length=100, verbose_name="Ubicación en el Restaurante")

    class Meta:
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"
        ordering = ['numero']

    def __str__(self):
        return f"Mesa {self.numero} - {'Ocupada' if self.ocupada else 'Libre'}"


class Pedidos(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('validando_stock', 'Validando Stock'),  # ✅ Nuevo estado
        ('en_elaboracion', 'En Elaboración'),  
        ('enviado_cocina', 'Enviado a Cocina'), 
        ('listo', 'Listo para Recoger'),        
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    nombre = models.CharField(max_length=100, verbose_name="Nombre del Cliente")
    mesa = models.ForeignKey(Mesas, on_delete=models.CASCADE, verbose_name="Mesa")
    mesero = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name="Mesero")
    
    notas_cocina = models.TextField(verbose_name="Notas para Cocina", blank=True, null=True)

    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name="Estado"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    
    timestamp_envio_cocina = models.DateTimeField(null=True, blank=True, verbose_name="Envío a Cocina") 
    timestamp_entrega = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Entrega")      
    reserva_stock_id = models.CharField(max_length=50, null=True, blank=True, verbose_name="ID Reserva M1") 
    
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="% Descuento")
    
    # ✅ Nuevos campos para control de stock con M1
    stock_validado = models.BooleanField(default=False, verbose_name="Stock Validado en M1")
    stock_consumido = models.BooleanField(default=False, verbose_name="Stock Consumido en M1")
    
    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha_creacion']

    def calcular_tiempo_total(self):
        if self.timestamp_entrega and self.fecha_creacion:
            return self.timestamp_entrega - self.fecha_creacion
        return timedelta(0)

    def calcular_total_neto(self):
        total = sum(detalle.subtotal() for detalle in self.detalles.all())
        return total

    def calcular_descuento_monto(self):
        return self.calcular_total_neto() * (self.descuento_porcentaje / 100)

    def calcular_total_final(self):
        return self.calcular_total_neto() - self.calcular_descuento_monto()

    # ✅ Método helper para obtener platos en formato para M1
    def get_platos_para_m1(self):
        """
        Retorna los platos del pedido en formato para enviar a M1
        """
        platos = []
        for detalle in self.detalles.all():
            if detalle.plato.plato_id_m1:  # Solo si tiene ID de M1
                platos.append({
                    'plato_id': detalle.plato.plato_id_m1,
                    'cantidad': detalle.cantidad
                })
        return platos

    def __str__(self):
        return f"Pedido #{self.id} - {self.nombre} - Mesa {self.mesa.numero}"

@receiver(post_delete, sender=Pedidos)
def liberar_mesa(sender, instance, **kwargs):
    if instance.mesa:
        instance.mesa.ocupada = False
        instance.mesa.save()