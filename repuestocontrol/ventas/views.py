from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from .models import Cliente, Venta, DetalleVenta
from repuestocontrol.inventario.models import Repuesto
from repuestocontrol.core.models import Configuracion
from repuestocontrol.core.sri import (
    generar_xml_factura,
    simular_autorizacion_sri,
    generar_rid_pdf,
    validar_cedula,
    validar_ruc,
)
from .forms import ClienteForm, VentaForm


@login_required
def venta_list(request):
    ventas = Venta.objects.select_related("cliente", "vendedor").all()

    estado = request.GET.get("estado")
    metodo = request.GET.get("metodo")
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    if estado:
        ventas = ventas.filter(estado=estado)
    if metodo:
        ventas = ventas.filter(metodo_pago=metodo)
    if fecha_inicio:
        ventas = ventas.filter(created_at__date__gte=fecha_inicio)
    if fecha_fin:
        ventas = ventas.filter(created_at__date__lte=fecha_fin)

    paginator = Paginator(ventas, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "ventas/venta_list.html", {"page_obj": page_obj})


@login_required
def venta_create(request):
    if request.method == "POST":
        return crear_venta(request)

    cliente_form = ClienteForm()
    venta_form = VentaForm()
    repuestos = Repuesto.objects.filter(activo=True, stock_actual__gt=0).select_related(
        "marca", "modelo"
    )
    clientes = Cliente.objects.all().order_by("nombre")

    config = Configuracion.get_config()
    iva_tarifa = float(config.iva_tarifa) if config else 12

    return render(
        request,
        "ventas/venta_form.html",
        {
            "cliente_form": cliente_form,
            "venta_form": venta_form,
            "repuestos": repuestos,
            "clientes": clientes,
            "iva_tarifa": iva_tarifa,
        },
    )


@login_required
def crear_venta(request):
    try:
        with transaction.atomic():
            cliente_id = request.POST.get("cliente")
            metodo_pago = request.POST.get("metodo_pago")
            forma_pago_sri = request.POST.get("forma_pago_sri", "01")
            notas = request.POST.get("notas")
            descuento = Decimal(str(request.POST.get("descuento", 0)))

            config = Configuracion.get_config()
            if not config:
                messages.error(
                    request,
                    "No hay configuración de empresa. Configure los datos tributarios.",
                )
                return redirect("ventas:venta_create")

            cliente = None
            if cliente_id:
                cliente = Cliente.objects.get(id=cliente_id)

            # Datos del cliente para factura
            cliente_nombre = cliente.nombre if cliente else "CONSUMIDOR FINAL"
            cliente_identificacion = (
                cliente.cedula if cliente and cliente.cedula else "9999999999"
            )
            cliente_tipo_id = (
                cliente.tipo_identificacion if cliente else "consumidor_final"
            )
            cliente_direccion = cliente.direccion if cliente else "N/A"
            cliente_telefono = cliente.telefono if cliente else ""
            cliente_email = cliente.email if cliente else ""

            ultimo = Venta.objects.order_by("-id").first()
            numero = f"VT-{timezone.now().year}{str((ultimo.id if ultimo else 0) + 1).zfill(6)}"

            # Generar número de factura
            secuencial = config.get_siguiente_secuencial()
            numero_factura = config.generar_numero_factura(secuencial)

            venta = Venta.objects.create(
                numero=numero,
                numero_factura=numero_factura,
                secuencia_factura=secuencial,
                cliente=cliente,
                cliente_nombre=cliente_nombre,
                cliente_identificacion=cliente_identificacion,
                cliente_tipo_identificacion=cliente_tipo_id,
                cliente_direccion=cliente_direccion,
                cliente_telefono=cliente_telefono,
                cliente_email=cliente_email,
                vendedor=request.user,
                metodo_pago=metodo_pago,
                forma_pago_sri=forma_pago_sri,
                notas=notas,
                descuento=descuento,
                estado=Venta.Estado.COMPLETADA,
            )

            items = request.POST.getlist("items")
            subtotal_12 = Decimal("0")
            subtotal_0 = Decimal("0")

            for item in items:
                data = item.split(",")
                repuesto_id = int(data[0])
                cantidad = int(data[1])
                precio = Decimal(data[2])

                repuesto = Repuesto.objects.get(id=repuesto_id)

                if repuesto.stock_actual < cantidad:
                    venta.delete()
                    messages.error(
                        request,
                        f"Stock insuficiente para {repuesto.nombre}. Disponible: {repuesto.stock_actual}",
                    )
                    return redirect("ventas:venta_create")

                repuesto.stock_actual -= cantidad
                repuesto.save()

                detalle = DetalleVenta.objects.create(
                    venta=venta,
                    repuesto=repuesto,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    subtotal=cantidad * precio,
                )
                subtotal_12 += detalle.subtotal

            # Calcular IVA
            iva_tarifa = Decimal(str(config.iva_tarifa))
            subtotal_con_desc = subtotal_12 - descuento
            iva = subtotal_con_desc * (iva_tarifa / Decimal("100"))
            total = subtotal_12 + subtotal_0 + iva - descuento

            venta.subtotal_12 = subtotal_12
            venta.subtotal_0 = subtotal_0
            venta.iva = iva.quantize(Decimal("0.01"))
            venta.total = total.quantize(Decimal("0.01"))
            venta.save()

            # Generar XML y simular autorización
            try:
                xml_data = generar_xml_factura(venta, config)
                venta.clave_acceso = xml_data["clave_acceso"]

                # Simular autorización (en producción, enviar al SRI)
                respuesta = simular_autorizacion_sri(
                    xml_data["xml"], xml_data["clave_acceso"], config
                )
                venta.estado_sri = respuesta["estado"].lower()
                venta.save()
            except Exception as e:
                # Si falla la generación de XML, continuar sin ella
                pass

            messages.success(
                request,
                f"Venta {venta.numero} creada correctamente. Factura: {venta.numero_factura}",
            )
            return redirect("ventas:venta_detail", pk=venta.id)

    except Exception as e:
        messages.error(request, f"Error al crear la venta: {str(e)}")
        return redirect("ventas:venta_create")


@login_required
def venta_detail(request, pk):
    venta = get_object_or_404(
        Venta.objects.select_related("cliente", "vendedor").prefetch_related(
            "detalles__repuesto"
        ),
        pk=pk,
    )

    config = Configuracion.get_config()
    ride_data = generar_rid_pdf(venta, config) if config else None

    return render(
        request, "ventas/venta_detail.html", {"venta": venta, "ride_data": ride_data}
    )


@login_required
def venta_anular(request, pk):
    venta = get_object_or_404(Venta, pk=pk)

    if request.method == "POST":
        if venta.estado == Venta.Estado.ANULADA:
            messages.error(request, "La venta ya está anulada.")
            return redirect("ventas:venta_detail", pk=pk)

        with transaction.atomic():
            for detalle in venta.detalles.all():
                detalle.repuesto.stock_actual += detalle.cantidad
                detalle.repuesto.save()

            venta.estado = Venta.Estado.ANULADA
            venta.estado_sri = "anulada"
            venta.save()

        messages.success(request, f"Venta {venta.numero} anulada correctamente.")
        return redirect("ventas:venta_list")

    return render(request, "ventas/venta_confirm_anular.html", {"venta": venta})


@login_required
def cliente_list(request):
    clientes = Cliente.objects.all().order_by("nombre")
    return render(request, "ventas/cliente_list.html", {"clientes": clientes})


@login_required
def cliente_create(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, "Cliente creado correctamente.")
            return redirect("ventas:cliente_list")
    else:
        form = ClienteForm()
    return render(
        request, "ventas/cliente_form.html", {"form": form, "action": "Crear"}
    )


@login_required
def cliente_edit(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, "Cliente actualizado correctamente.")
            return redirect("ventas:cliente_list")
    else:
        form = ClienteForm(instance=cliente)
    return render(
        request, "ventas/cliente_form.html", {"form": form, "action": "Editar"}
    )


@login_required
def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        cliente.delete()
        messages.success(request, "Cliente eliminado correctamente.")
        return redirect("ventas:cliente_list")
    return render(
        request,
        "ventas/cliente_confirm_delete.html",
        {"object": cliente, "type": "cliente"},
    )


@login_required
def cliente_api_create(request):
    """API para crear cliente desde el formulario de venta"""
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            return JsonResponse(
                {
                    "success": True,
                    "cliente": {
                        "id": cliente.id,
                        "nombre": cliente.nombre,
                        "cedula": cliente.cedula,
                        "tipo_identificacion": cliente.tipo_identificacion,
                        "telefono": cliente.telefono,
                        "email": cliente.email,
                        "direccion": cliente.direccion,
                    },
                }
            )
        else:
            return JsonResponse({"success": False, "error": str(form.errors)})
    return JsonResponse({"success": False, "error": "Método no permitido"})


@login_required
def validar_identificacion(request):
    """API para validar identificación"""
    tipo = request.GET.get("tipo", "cedula")
    identificacion = request.GET.get("identificacion", "")

    if tipo == "ruc":
        es_valido = validar_ruc(identificacion)
    elif tipo == "cedula":
        es_valido = validar_cedula(identificacion)
    else:
        es_valido = len(identificacion) >= 5

    return JsonResponse(
        {
            "valido": es_valido,
            "mensaje": "Identificación válida"
            if es_valido
            else "Identificación inválida",
        }
    )
