from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
from repuestocontrol.inventario.models import Repuesto, Categoria, Marca
from repuestocontrol.ventas.models import Venta, DetalleVenta


@login_required
def index(request):
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)

    total_repuestos = Repuesto.objects.filter(activo=True).count()
    productos_criticos = Repuesto.objects.filter(
        activo=True, stock_actual__lte=F("stock_minimo")
    ).count()
    total_categorias = Categoria.objects.count()
    total_marcas = Marca.objects.count()

    ventas_hoy = Venta.objects.filter(
        created_at__date=hoy, estado=Venta.Estado.COMPLETADA
    )
    ingresos_hoy = ventas_hoy.aggregate(total=Sum("total"))["total"] or 0
    ventas_hoy_count = ventas_hoy.count()

    ventas_mes = Venta.objects.filter(
        created_at__date__gte=inicio_mes, estado=Venta.Estado.COMPLETADA
    )
    ingresos_mes = ventas_mes.aggregate(total=Sum("total"))["total"] or 0
    ventas_mes_count = ventas_mes.count()

    repuestos_mas_vendidos = (
        DetalleVenta.objects.filter(venta__estado=Venta.Estado.COMPLETADA)
        .values("repuesto__codigo", "repuesto__nombre")
        .annotate(total_vendido=Sum("cantidad"), ingresos=Sum("subtotal"))
        .order_by("-total_vendido")[:10]
    )

    ultimos_30_dias = hoy - timedelta(days=30)
    ingresos_diarios = (
        Venta.objects.filter(
            created_at__date__gte=ultimos_30_dias, estado=Venta.Estado.COMPLETADA
        )
        .values("created_at__date")
        .annotate(total=Sum("total"))
        .order_by("created_at__date")
    )

    categorias_data = (
        DetalleVenta.objects.filter(venta__estado=Venta.Estado.COMPLETADA)
        .values("repuesto__categoria__nombre")
        .annotate(total=Sum("cantidad"))
        .order_by("-total")[:5]
    )

    productos_bajo_stock = Repuesto.objects.filter(
        activo=True, stock_actual__lte=F("stock_minimo")
    ).select_related("marca", "categoria")[:10]

    ultimas_ventas = Venta.objects.select_related("cliente", "vendedor").order_by(
        "-created_at"
    )[:10]

    return render(
        request,
        "dashboard/index.html",
        {
            "total_repuestos": total_repuestos,
            "productos_criticos": productos_criticos,
            "total_categorias": total_categorias,
            "total_marcas": total_marcas,
            "ingresos_hoy": ingresos_hoy,
            "ventas_hoy_count": ventas_hoy_count,
            "ingresos_mes": ingresos_mes,
            "ventas_mes_count": ventas_mes_count,
            "repuestos_mas_vendidos": repuestos_mas_vendidos,
            "ingresos_diarios": list(ingresos_diarios),
            "categorias_data": list(categorias_data),
            "productos_bajo_stock": productos_bajo_stock,
            "ultimas_ventas": ultimas_ventas,
        },
    )
