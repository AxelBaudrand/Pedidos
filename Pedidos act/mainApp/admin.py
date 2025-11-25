from django.contrib import admin
from .models import Pedidos, Mesas, Plato, DetallePedido 


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1 
    readonly_fields = ['subtotal'] 

@admin.register(Pedidos)
class PedidosAdmin(admin.ModelAdmin):
    list_display = [
        'id', 
        'nombre', 
        'mesa', 
        'mesero', 
        'estado', 
        'fecha_creacion',
        'timestamp_entrega', 
        'total_final_display' 
    ]
    
    
    list_filter = ['estado', 'fecha_creacion', 'mesero'] 
    search_fields = ['nombre', 'mesa__numero', 'reserva_stock_id']

   
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'mesa', 'mesero', 'estado'),
        }),
        ('Control de Tiempo y Stock (Criterios #18, #21, #24)', {
            'fields': ('timestamp_envio_cocina', 'timestamp_entrega', 'reserva_stock_id'),
            'classes': ('collapse',),
        }),
        ('Cuenta y Descuento (Criterio #26)', {
            'fields': ('descuento_porcentaje',),
        }),
    )


    inlines = [DetallePedidoInline]


    def total_final_display(self, obj):
        return f"${obj.calcular_total_final():.2f}"
    total_final_display.short_description = 'Total Final'


@admin.register(Mesas)
class MesasAdmin(admin.ModelAdmin):
    list_display = ['id', 'numero', 'ocupada', 'ubicacion']
    list_filter = ['ocupada']
    search_fields = ['numero', 'ubicacion']

@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'precio']
    search_fields = ['nombre']