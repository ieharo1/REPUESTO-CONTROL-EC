from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from repuestocontrol.inventario.models import Repuesto, Marca, Modelo, Categoria


def catalogo(request):
    query = request.GET.get("q", "")
    marca_id = request.GET.get("marca", "")
    modelo_id = request.GET.get("modelo", "")
    categoria_id = request.GET.get("categoria", "")

    repuestos = Repuesto.objects.select_related("marca", "modelo", "categoria").filter(
        activo=True, stock_actual__gt=0
    )

    if query:
        repuestos = repuestos.filter(
            Q(codigo__icontains=query)
            | Q(nombre__icontains=query)
            | Q(marca__nombre__icontains=query)
            | Q(categoria__nombre__icontains=query)
        )

    if marca_id:
        repuestos = repuestos.filter(marca_id=marca_id)
    if modelo_id:
        repuestos = repuestos.filter(modelo_id=modelo_id)
    if categoria_id:
        repuestos = repuestos.filter(categoria_id=categoria_id)

    repuestos = repuestos.order_by("nombre")

    paginator = Paginator(repuestos, 24)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    marcas = Marca.objects.filter(activa=True).order_by("nombre")
    categorias = Categoria.objects.all().order_by("nombre")

    modelos = Modelo.objects.select_related("marca").all()

    return render(
        request,
        "catalogo_publico/catalogo.html",
        {
            "page_obj": page_obj,
            "marcas": marcas,
            "modelos": modelos,
            "categorias": categorias,
            "query": query,
        },
    )


def repuesto_detail(request, pk):
    repuesto = Repuesto.objects.select_related("marca", "modelo", "categoria").get(
        pk=pk, activo=True
    )
    relacionados = Repuesto.objects.filter(
        activo=True, stock_actual__gt=0, marca=repuesto.marca
    ).exclude(pk=pk)[:4]

    return render(
        request,
        "catalogo_publico/repuesto_detail.html",
        {
            "repuesto": repuesto,
            "relacionados": relacionados,
        },
    )
