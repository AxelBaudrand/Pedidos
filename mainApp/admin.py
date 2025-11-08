from django.contrib import admin
from .models import Mesa, Plato, Pedido, PlatoPedido

class PlatoPedidoInline(admin.TabularInline):
    model = PlatoPedido
    extra = 0
    fields = ('plato', 'cantidad', 'observaciones')
    readonly_fields = ()  # Podríamos hacer ciertos campos solo lectura si es necesario

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'mesa', 'mesero', 'estado', 'fecha_creacion', 'total_pedido')
    list_filter = ('estado', 'mesa', 'mesero', 'fecha_creacion')
    search_fields = ('codigo', 'mesa__numero', 'mesero__username')
    readonly_fields = ('codigo', 'fecha_creacion', 'fecha_envio', 'fecha_entrega', 'fecha_cancelacion')
    inlines = [PlatoPedidoInline]

    def total_pedido(self, obj):
        return f"${obj.total:.2f}"
    total_pedido.short_description = "Total Pedido"

@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'estado')
    list_editable = ('estado',)  # permitir marcar libre/ocupada rápidamente
    ordering = ('numero',)
    list_filter = ('estado',)

@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'disponible')
    list_filter = ('disponible',)
    search_fields = ('nombre',)
