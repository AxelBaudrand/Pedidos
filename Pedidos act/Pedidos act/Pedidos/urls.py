from django.contrib import admin
from django.urls import path, include
from mainApp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('crear/', views.crear_pedido, name='crear_pedido'),
    path('detalle/<int:id>/', views.detalle_pedido, name='detalle_pedido'),
    path('editar/<int:id>/', views.editar_pedido, name='editar_pedido'),
    path('eliminar/<int:id>/', views.eliminar_pedido, name='eliminar_pedido'),
    path('mesa/<int:mesa_id>/pedidos/', views.pedidos_por_mesa, name='pedidos_por_mesa'),
    
    # ✅ Rutas para integración con M1 (API)
    path('pedido/<int:id>/validar-stock/', views.validar_stock_pedido, name='validar_stock'),
    path('pedido/<int:id>/enviar-cocina/', views.enviar_a_cocina, name='enviar_cocina'),
    path('pedido/<int:id>/cancelar/', views.cancelar_pedido, name='cancelar_pedido'),
    path('pedido/<int:id>/cambiar-estado/', views.cambiar_estado_pedido, name='cambiar_estado'),
]