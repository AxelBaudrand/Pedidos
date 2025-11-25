from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Pedidos, Mesas, Plato, DetallePedido
from django.contrib.auth.models import User
from .services import MenuAPIService
from django.utils import timezone
import json

# Instancia del servicio de API
menu_api = MenuAPIService()

# Página principal: lista de pedidos y mesas disponibles
def home(request):
    pedidos = Pedidos.objects.all()
    mesas_disponibles = Mesas.objects.filter(ocupada=False)
    meseros = User.objects.filter(groups__name='Meseros')
    platos = Plato.objects.all().order_by('nombre')  # Todos los platos ordenados
    
    # Contar platos con y sin ID de M1
    platos_con_id_m1 = platos.filter(plato_id_m1__isnull=False).count()
    platos_sin_id_m1 = platos.filter(plato_id_m1__isnull=True).count()
    
    return render(request, 'home.html', {
        'pedidos': pedidos, 
        'Mesas': mesas_disponibles, 
        'Meseros': meseros,
        'platos': platos,
        'platos_con_id_m1': platos_con_id_m1,
        'platos_sin_id_m1': platos_sin_id_m1
    })

# Crear nuevo pedido
def crear_pedido(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        mesa_id = request.POST.get('mesa')
        mesero_id = request.POST.get('mesero')
        notas_cocina = request.POST.get('notas_cocina', '')
        
        # Recibir platos del formulario
        platos_ids = request.POST.getlist('platos[]')
        cantidades = request.POST.getlist('cantidades[]')
        
        if nombre and mesa_id and mesero_id and platos_ids:
            try:
                mesa = Mesas.objects.get(id=mesa_id)
                mesero = User.objects.get(id=mesero_id)
                
                # Marcar mesa como ocupada
                mesa.ocupada = True
                mesa.save()

                # Crear el pedido
                pedido = Pedidos.objects.create(
                    nombre=nombre, 
                    mesa=mesa, 
                    mesero=mesero,
                    notas_cocina=notas_cocina,
                    estado='pendiente'
                )
                
                # Crear los detalles del pedido
                for i, plato_id in enumerate(platos_ids):
                    if plato_id:
                        plato = Plato.objects.get(id=plato_id)
                        cantidad = int(cantidades[i]) if i < len(cantidades) else 1
                        
                        DetallePedido.objects.create(
                            pedido=pedido,
                            plato=plato,
                            cantidad=cantidad
                        )
                
                messages.success(request, f'✅ ¡Pedido #{pedido.id} creado exitosamente!')
                return redirect('detalle_pedido', id=pedido.id)
                
            except Exception as e:
                messages.error(request, f'❌ Error al crear pedido: {str(e)}')
        else:
            messages.error(request, '❌ Todos los campos son obligatorios.')

    return redirect('home')

# Ver detalle del pedido
def detalle_pedido(request, id):
    pedido = get_object_or_404(Pedidos, id=id)
    detalles = pedido.detalles.all()
    
    return render(request, 'detalle_pedido.html', {
        'pedido': pedido,
        'detalles': detalles
    })

# Editar pedido
def editar_pedido(request, id):
    pedido = get_object_or_404(Pedidos, id=id)
    mesas_disponibles = Mesas.objects.filter(ocupada=False) | Mesas.objects.filter(id=pedido.mesa.id)
    platos = Plato.objects.all()
    detalles = pedido.detalles.all()

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        mesa_id = request.POST.get('mesa')
        notas_cocina = request.POST.get('notas_cocina', '')
        estado = request.POST.get('estado')

        # Recibir platos del formulario (si es que vienen)
        platos_ids = request.POST.getlist('platos[]')
        cantidades = request.POST.getlist('cantidades[]')

        if nombre and mesa_id:
            try:
                mesa_actual = pedido.mesa
                nueva_mesa = Mesas.objects.get(id=mesa_id)

                # Si cambia la mesa, liberar la anterior y ocupar la nueva
                if mesa_actual.id != nueva_mesa.id:
                    mesa_actual.ocupada = False
                    mesa_actual.save()
                    nueva_mesa.ocupada = True
                    nueva_mesa.save()

                # Actualizar datos básicos del pedido
                pedido.nombre = nombre
                pedido.mesa = nueva_mesa
                pedido.notas_cocina = notas_cocina
                if estado:
                    pedido.estado = estado
                pedido.save()

                #  SOLO si el formulario trae platos, actualizamos los detalles
                if platos_ids:
                    # Eliminar detalles antiguos
                    pedido.detalles.all().delete()

                    # Crear nuevos detalles
                    for i, plato_id in enumerate(platos_ids):
                        if plato_id:
                            plato = Plato.objects.get(id=plato_id)
                            cantidad = int(cantidades[i]) if i < len(cantidades) else 1

                            DetallePedido.objects.create(
                                pedido=pedido,
                                plato=plato,
                                cantidad=cantidad
                            )

                messages.success(request, '✅ ¡Pedido actualizado exitosamente!')
                return redirect('detalle_pedido', id=pedido.id)

            except Exception as e:
                messages.error(request, f'❌ Error al actualizar: {str(e)}')
        else:
            messages.error(request, '❌ Todos los campos son obligatorios.')

    return render(request, 'editar_pedido.html', {
        'pedido': pedido,
        'Mesas': mesas_disponibles,
        'platos': platos,
        'detalles': detalles
    })


# Eliminar pedido
def eliminar_pedido(request, id):
    pedido = get_object_or_404(Pedidos, id=id)
    if request.method == 'POST':
        mesa = pedido.mesa
        mesa.ocupada = False
        mesa.save()
        pedido.delete()
        messages.success(request, '🗑️ Pedido eliminado y Mesa liberada.')
        return redirect('home')
    
    return render(request, 'confirmar_eliminar.html', {'pedido': pedido})

# Mostrar pedidos por mesa
def pedidos_por_mesa(request, mesa_id):
    mesa = get_object_or_404(Mesas, id=mesa_id)
    pedidos = Pedidos.objects.filter(mesa=mesa).exclude(estado='entregado')

    return render(request, 'pedidos_por_mesa.html', {
        'mesa': mesa,
        'pedidos': pedidos
    })

# ============================================
# ✅ VISTAS PARA INTEGRACIÓN CON API M1
# ============================================

@require_POST
def validar_stock_pedido(request, id):
    """
    Valida el stock del pedido con el módulo M1
    """
    pedido = get_object_or_404(Pedidos, id=id)
    
    # Verificar que tenga platos
    if not pedido.detalles.exists():
        return JsonResponse({
            'success': False,
            'message': 'El pedido no tiene platos asignados'
        }, status=400)
    
    # Verificar que los platos tengan ID de M1
    platos_sin_id = []
    for detalle in pedido.detalles.all():
        if not detalle.plato.plato_id_m1:
            platos_sin_id.append(detalle.plato.nombre)
    
    if platos_sin_id:
        return JsonResponse({
            'success': False,
            'message': f'Los siguientes platos no tienen ID de M1: {", ".join(platos_sin_id)}'
        }, status=400)
    
    # Preparar lista de platos para M1
    platos = pedido.get_platos_para_m1()
    
    if not platos:
        return JsonResponse({
            'success': False,
            'message': 'No hay platos válidos para enviar a M1'
        }, status=400)
    
    # Llamar a la API de M1
    resultado = menu_api.validar_stock(platos)
    
    if resultado['success']:
        # Actualizar estado del pedido
        pedido.estado = 'validando_stock'
        pedido.stock_validado = True
        
        # Guardar ID de reserva si M1 lo proporciona
        if resultado['data'] and 'reserva_id' in resultado['data']:
            pedido.reserva_stock_id = resultado['data']['reserva_id']
        
        pedido.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Stock validado correctamente. Puede confirmar el pedido.',
            'data': resultado['data']
        })
    else:
        return JsonResponse({
            'success': False,
            'message': resultado['message']
        }, status=400)

@require_POST
def enviar_a_cocina(request, id):
    """
    Confirma el pedido y consume el stock definitivamente
    """
    pedido = get_object_or_404(Pedidos, id=id)
    
    # Verificar que el stock esté validado
    if not pedido.stock_validado:
        return JsonResponse({
            'success': False,
            'message': 'Debe validar el stock antes de enviar a cocina'
        }, status=400)
    
    # Verificar que no esté ya consumido
    if pedido.stock_consumido:
        return JsonResponse({
            'success': False,
            'message': 'El stock ya fue consumido para este pedido'
        }, status=400)
    
    # Preparar lista de platos
    platos = pedido.get_platos_para_m1()
    
    if not platos:
        return JsonResponse({
            'success': False,
            'message': 'No hay platos válidos para enviar'
        }, status=400)
    
    # Consumir stock en M1
    resultado = menu_api.consumir_stock(pedido.id, platos)
    
    if resultado['success']:
        # Actualizar pedido
        pedido.estado = 'enviado_cocina'
        pedido.stock_consumido = True
        pedido.timestamp_envio_cocina = timezone.now()
        pedido.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Pedido enviado a cocina correctamente',
            'data': resultado['data']
        })
    else:
        return JsonResponse({
            'success': False,
            'message': resultado['message']
        }, status=400)

@require_POST
def cancelar_pedido(request, id):
    """
    Cancela un pedido y libera la reserva de stock
    """
    pedido = get_object_or_404(Pedidos, id=id)
    
    # Solo cancelar stock si está validado pero no consumido
    if pedido.stock_validado and not pedido.stock_consumido:
        platos = pedido.get_platos_para_m1()
        
        if platos:
            # Cancelar reserva en M1
            resultado = menu_api.cancelar_reserva(platos)
            
            if not resultado['success']:
                return JsonResponse({
                    'success': False,
                    'message': f"Advertencia al cancelar reserva: {resultado['message']}"
                }, status=400)
    
    # Actualizar estado y liberar mesa
    pedido.estado = 'cancelado'
    pedido.save()
    
    mesa = pedido.mesa
    mesa.ocupada = False
    mesa.save()
    
    return JsonResponse({
        'success': True,
        'message': 'Pedido cancelado correctamente'
    })

# ============================================
# ✅ VISTA PARA CAMBIAR ESTADO DEL PEDIDO
# ============================================

@require_POST
def cambiar_estado_pedido(request, id):
    """
    Cambia el estado del pedido manualmente
    """
    pedido = get_object_or_404(Pedidos, id=id)
    nuevo_estado = request.POST.get('estado')
    
    if nuevo_estado not in dict(Pedidos.ESTADO_CHOICES):
        return JsonResponse({
            'success': False,
            'message': 'Estado no válido'
        }, status=400)
    
    # Registrar timestamp de entrega
    if nuevo_estado == 'entregado' and not pedido.timestamp_entrega:
        pedido.timestamp_entrega = timezone.now()
    
    pedido.estado = nuevo_estado
    pedido.save()
    
    return JsonResponse({
        'success': True,
        'message': f'Estado actualizado a: {pedido.get_estado_display()}'
    })