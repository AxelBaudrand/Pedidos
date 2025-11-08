from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
import requests

from .models import Mesa, Plato, Pedido, PlatoPedido

def home(request):
    # Página principal: lista de mesas del restaurante
    mesas = Mesa.objects.all().order_by('numero')
    contexto = {
        'mesas': mesas
    }
    return render(request, 'home.html', contexto)

def mesa_detalle(request, mesa_id):
    mesa = get_object_or_404(Mesa, pk=mesa_id)
    # Obtener pedidos activos (no entregados ni cancelados) de esta mesa
    pedidos_activos = mesa.pedidos.exclude(estado__in=['entregado', 'cancelado']).order_by('fecha_creacion')
    # Contar pedidos entregados para mostrar opción de cuenta
    pedidos_entregados_count = mesa.pedidos.filter(estado='entregado').count()
    contexto = {
        'mesa': mesa,
        'pedidos_activos': pedidos_activos,
        'pedidos_entregados_count': pedidos_entregados_count
    }
    return render(request, 'mesa_detalle.html', contexto)

def nuevo_pedido(request, mesa_id):
    # Crea un nuevo pedido para la mesa especificada, si está ocupada
    mesa = get_object_or_404(Mesa, pk=mesa_id)
    # Validar que la mesa esté ocupada antes de crear pedido
    if mesa.estado != 'ocupada':
        messages.error(request, "No se puede crear un pedido porque la mesa no está ocupada.")
        return redirect('mesa_detalle', mesa_id=mesa.id)
    # Crear el pedido con estado 'En elaboración'
    pedido = Pedido.objects.create(
        mesa=mesa,
        mesero=request.user,  # mesero responsable (usuario actual)
        estado='en_elaboracion'
    )
    messages.success(request, f"Pedido creado: {pedido.codigo}")
    # Redirigir al detalle del pedido para agregar platos
    return redirect('pedido_detalle', pedido_id=pedido.id)

def pedido_detalle(request, pedido_id):
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    mesa = pedido.mesa
    # Si el pedido no está en elaboración, no permitimos agregar/quitar platos
    if pedido.estado != 'en_elaboracion':
        # Redirige a la vista de mesa si se intenta acceder a pedido ya confirmado
        return redirect('mesa_detalle', mesa_id=mesa.id)
    # Listar platos disponibles (por ejemplo, platos del menú que estén marcados como disponibles)
    platos_menu = Plato.objects.filter(disponible=True).order_by('nombre')
    if request.method == 'POST':
        # Procesar formulario para agregar un plato al pedido
        plato_id = request.POST.get('plato')
        cantidad = request.POST.get('cantidad')
        observaciones = request.POST.get('observaciones', '')
        # Validar campos obligatorios
        if not plato_id or not cantidad:
            messages.error(request, "Debe seleccionar un plato y una cantidad.")
            return redirect('pedido_detalle', pedido_id=pedido.id)
        cantidad = int(cantidad)
        # Validar rango de cantidad 1-20
        if cantidad < 1 or cantidad > 20:
            messages.error(request, "La cantidad debe ser entre 1 y 20.")
            return redirect('pedido_detalle', pedido_id=pedido.id)
        plato = get_object_or_404(Plato, pk=plato_id)
        # Verificar disponibilidad (en caso de integración en tiempo real con Módulo 1, aquí podría consultarse)
        if not plato.disponible:
            messages.error(request, f"El plato '{plato.nombre}' no está disponible actualmente.")
            return redirect('pedido_detalle', pedido_id=pedido.id)
        # Si el plato ya está en el pedido (y misma observación), actualizar cantidad en lugar de duplicar
        existente = PlatoPedido.objects.filter(pedido=pedido, plato=plato, observaciones=observaciones).first()
        if existente:
            existente.cantidad += cantidad
            existente.save()
        else:
            PlatoPedido.objects.create(pedido=pedido, plato=plato, cantidad=cantidad, observaciones=observaciones)
        messages.success(request, f"{cantidad} x {plato.nombre} agregado al pedido.")
        return redirect('pedido_detalle', pedido_id=pedido.id)
    # GET: mostrar detalles del pedido y formulario para agregar platos
    contexto = {
        'pedido': pedido,
        'mesa': mesa,
        'platos_menu': platos_menu
    }
    return render(request, 'pedido_detalle.html', contexto)

def eliminar_plato(request, pedido_id, item_id):
    # Elimina un plato de un pedido (antes de enviarlo a cocina)
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if pedido.estado != 'en_elaboracion':
        return redirect('mesa_detalle', mesa_id=pedido.mesa.id)
    item = get_object_or_404(PlatoPedido, pk=item_id, pedido=pedido)
    item.delete()
    messages.info(request, f"Plato '{item.plato.nombre}' eliminado del pedido.")
    return redirect('pedido_detalle', pedido_id=pedido.id)

def enviar_pedido(request, pedido_id):
    # Enviar el pedido a cocina (cambia estado a 'En cocina' tras validar stock y notificar a Módulo 4)
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if pedido.estado != 'en_elaboracion':
        return redirect('mesa_detalle', mesa_id=pedido.mesa.id)
    # Preparar datos de platos para validación de stock con Módulo 1
    platos_data = [{"plato_id": item.plato.id, "cantidad": item.cantidad} for item in pedido.platos.all()]
    try:
        # Llamar a API M1 para validar stock
        respuesta = requests.post("http://modulo1/api/stock/validar", json={"platos": platos_data})
    except Exception as e:
        messages.error(request, "Error al conectar con sistema de stock.")
        return redirect('pedido_detalle', pedido_id=pedido.id)
    if respuesta.status_code != 200:
        messages.error(request, "Error en validación de stock (M1).")
        return redirect('pedido_detalle', pedido_id=pedido.id)
    data = respuesta.json()
    if not data.get('success', False):
        # Si falta stock de algún ingrediente, mostrar mensaje de error detallado
        mensaje = data.get('error') or "Stock insuficiente para preparar el pedido."
        # Ejemplo de mensaje esperado: "No disponible: [Plato X] (falta ingrediente Y)"
        messages.error(request, mensaje)
        # Mesero puede optar por quitar platos o cancelar pedido
        return redirect('pedido_detalle', pedido_id=pedido.id)
    # Si hay stock suficiente, proceder a enviar a cocina (Módulo 4)
    try:
        orden_detalle = {
            "pedido_id": pedido.id,
            "mesa": pedido.mesa.numero,
            "platos": [{"nombre": item.plato.nombre, "cantidad": item.cantidad, "observaciones": item.observaciones} for item in pedido.platos.all()]
        }
        resp_cocina = requests.post("http://modulo4/api/cocina/pedidos", json=orden_detalle)
    except Exception as e:
        messages.error(request, "No se pudo notificar a la cocina. Intente nuevamente.")
        return redirect('pedido_detalle', pedido_id=pedido.id)
    if resp_cocina.status_code != 200:
        messages.error(request, "La cocina no recibió el pedido. Intente nuevamente.")
        return redirect('pedido_detalle', pedido_id=pedido.id)
    # Si cocina recibió, consumir stock definitivamente en M1
    requests.post("http://modulo1/api/stock/consumir", json={"platos": platos_data})
    # Actualizar estado y registrar fecha/hora de envío a cocina
    pedido.estado = 'en_cocina'
    pedido.fecha_envio = timezone.now()
    pedido.save()
    messages.success(request, f"Pedido {pedido.codigo} enviado a cocina.")
    return redirect('mesa_detalle', mesa_id=pedido.mesa.id)

def cancelar_pedido(request, pedido_id):
    # Cancelar un pedido que aún no ha sido enviado a cocina
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if pedido.estado != 'en_elaboracion':
        return redirect('mesa_detalle', mesa_id=pedido.mesa.id)
    # (Aquí podríamos pedir confirmación y razón de cancelación; omitido por simplicidad)
    pedido.estado = 'cancelado'
    pedido.fecha_cancelacion = timezone.now()
    # Liberar reserva de stock en M1 si existía (llamado hipotético al API)
    requests.post("http://modulo1/api/stock/liberar", json={"pedido_id": pedido.id})
    pedido.save()
    messages.info(request, f"Pedido {pedido.codigo} cancelado.")
    return redirect('mesa_detalle', mesa_id=pedido.mesa.id)

def marcar_entregado(request, pedido_id):
    # Marcar un pedido como entregado (solo si ya está 'Listo')
    pedido = get_object_or_404(Pedido, pk=pedido_id)
    if pedido.estado != 'listo':
        return redirect('mesa_detalle', mesa_id=pedido.mesa.id)
    pedido.estado = 'entregado'
    pedido.fecha_entrega = timezone.now()
    pedido.save()
    # Notificar a Módulo 4 que el pedido fue entregado (confirmación)
    requests.post("http://modulo4/api/cocina/pedido_entregado", json={"pedido_id": pedido.id})
    messages.success(request, f"Pedido {pedido.codigo} marcado como ENTREGADO.")
    return redirect('mesa_detalle', mesa_id=pedido.mesa.id)

def ver_cuenta(request, mesa_id):
    # Ver el resumen de la cuenta de una mesa: todos los pedidos entregados
    mesa = get_object_or_404(Mesa, pk=mesa_id)
    pedidos_entregados = mesa.pedidos.filter(estado='entregado')
    total_general = 0
    detalle_pedidos = []
    for pedido in pedidos_entregados:
        subtotal = pedido.total
        total_general += subtotal
        detalle_pedidos.append({
            'pedido': pedido,
            'subtotal': subtotal
        })
    # Aplicar descuento si se solicita
    descuento = request.GET.get('descuento')  # porcentaje de descuento (0-100)
    total_con_descuento = None
    if descuento:
        try:
            descuento = float(descuento)
        except ValueError:
            descuento = None
        if descuento is not None and 0 < descuento <= 100:
            total_con_descuento = total_general * (1 - descuento/100.0)
    # Dividir cuenta entre N personas si se solicita
    personas = request.GET.get('personas')
    total_por_persona = None
    num_personas = None
    if personas:
        try:
            num_personas = int(personas)
        except ValueError:
            num_personas = None
        if num_personas and num_personas > 0:
            # Usar el total con descuento si existe, si no el total general
            base = total_con_descuento if total_con_descuento is not None else total_general
            total_por_persona = base / num_personas
    contexto = {
        'mesa': mesa,
        'detalle_pedidos': detalle_pedidos,
        'total_general': total_general,
        'descuento': descuento,
        'total_con_descuento': total_con_descuento,
        'num_personas': num_personas,
        'total_por_persona': total_por_persona
    }
    return render(request, 'cuenta.html', contexto)
