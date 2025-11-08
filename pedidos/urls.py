from django.contrib import admin
from django.urls import path
from mainApp import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('mesa/<int:mesa_id>/', views.mesa_detalle, name='mesa_detalle'),
    path('mesa/<int:mesa_id>/nuevo_pedido/', views.nuevo_pedido, name='nuevo_pedido'),
    path('mesa/<int:mesa_id>/cuenta/', views.ver_cuenta, name='ver_cuenta'),
    path('pedido/<int:pedido_id>/', views.pedido_detalle, name='pedido_detalle'),
    path('pedido/<int:pedido_id>/eliminar_plato/<int:item_id>/', views.eliminar_plato, name='eliminar_plato'),
    path('pedido/<int:pedido_id>/enviar/', views.enviar_pedido, name='enviar_pedido'),
    path('pedido/<int:pedido_id>/cancelar/', views.cancelar_pedido, name='cancelar_pedido'),
    path('pedido/<int:pedido_id>/entregar/', views.marcar_entregado, name='marcar_entregado'),
]
