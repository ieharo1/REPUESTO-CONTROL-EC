from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.http import JsonResponse
from .models import Marca, Modelo, Categoria, Repuesto
from .forms import MarcaForm, ModeloForm, CategoriaForm, RepuestoForm


@login_required
def marca_list(request):
    marcas = Marca.objects.all().order_by("nombre")
    return render(request, "inventario/marca_list.html", {"marcas": marcas})


@login_required
def marca_create(request):
    if request.method == "POST":
        form = MarcaForm(request.POST)
        if form.save():
            messages.success(request, "Marca creada correctamente.")
            return redirect("inventario:marca_list")
    else:
        form = MarcaForm()
    return render(
        request, "inventario/marca_form.html", {"form": form, "action": "Crear"}
    )


@login_required
def marca_edit(request, pk):
    marca = get_object_or_404(Marca, pk=pk)
    if request.method == "POST":
        form = MarcaForm(request.POST, instance=marca)
        if form.save():
            messages.success(request, "Marca actualizada correctamente.")
            return redirect("inventario:marca_list")
    else:
        form = MarcaForm(instance=marca)
    return render(
        request, "inventario/marca_form.html", {"form": form, "action": "Editar"}
    )


@login_required
def marca_delete(request, pk):
    marca = get_object_or_404(Marca, pk=pk)
    if request.method == "POST":
        marca.delete()
        messages.success(request, "Marca eliminada correctamente.")
        return redirect("inventario:marca_list")
    return render(
        request,
        "inventario/marca_confirm_delete.html",
        {"object": marca, "type": "marca"},
    )


@login_required
def modelo_list(request):
    modelos = (
        Modelo.objects.select_related("marca").all().order_by("marca__nombre", "nombre")
    )
    return render(request, "inventario/modelo_list.html", {"modelos": modelos})


@login_required
def modelo_create(request):
    if request.method == "POST":
        form = ModeloForm(request.POST)
        if form.save():
            messages.success(request, "Modelo creado correctamente.")
            return redirect("inventario:modelo_list")
    else:
        form = ModeloForm()
    return render(
        request, "inventario/modelo_form.html", {"form": form, "action": "Crear"}
    )


@login_required
def modelo_edit(request, pk):
    modelo = get_object_or_404(Modelo, pk=pk)
    if request.method == "POST":
        form = ModeloForm(request.POST, instance=modelo)
        if form.save():
            messages.success(request, "Modelo actualizado correctamente.")
            return redirect("inventario:modelo_list")
    else:
        form = ModeloForm(instance=modelo)
    return render(
        request, "inventario/modelo_form.html", {"form": form, "action": "Editar"}
    )


@login_required
def modelo_delete(request, pk):
    modelo = get_object_or_404(Modelo, pk=pk)
    if request.method == "POST":
        modelo.delete()
        messages.success(request, "Modelo eliminado correctamente.")
        return redirect("inventario:modelo_list")
    return render(
        request,
        "inventario/modelo_confirm_delete.html",
        {"object": modelo, "type": "modelo"},
    )


@login_required
def categoria_list(request):
    categorias = Categoria.objects.all().order_by("nombre")
    return render(request, "inventario/categoria_list.html", {"categorias": categorias})


@login_required
def categoria_create(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.save():
            messages.success(request, "Categoría creada correctamente.")
            return redirect("inventario:categoria_list")
    else:
        form = CategoriaForm()
    return render(
        request, "inventario/categoria_form.html", {"form": form, "action": "Crear"}
    )


@login_required
def categoria_edit(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        form = CategoriaForm(request.POST, instance=categoria)
        if form.save():
            messages.success(request, "Categoría actualizada correctamente.")
            return redirect("inventario:categoria_list")
    else:
        form = CategoriaForm(instance=categoria)
    return render(
        request, "inventario/categoria_form.html", {"form": form, "action": "Editar"}
    )


@login_required
def categoria_delete(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        categoria.delete()
        messages.success(request, "Categoría eliminada correctamente.")
        return redirect("inventario:categoria_list")
    return render(
        request,
        "inventario/categoria_confirm_delete.html",
        {"object": categoria, "type": "categoria"},
    )


@login_required
def repuesto_list(request):
    query = request.GET.get("q", "")
    marca_id = request.GET.get("marca", "")
    modelo_id = request.GET.get("modelo", "")
    categoria_id = request.GET.get("categoria", "")
    critico = request.GET.get("critico", "")

    repuestos = Repuesto.objects.select_related("marca", "modelo", "categoria").filter(
        activo=True
    )

    if query:
        repuestos = repuestos.filter(
            Q(codigo__icontains=query) | Q(nombre__icontains=query)
        )
    if marca_id:
        repuestos = repuestos.filter(marca_id=marca_id)
    if modelo_id:
        repuestos = repuestos.filter(modelo_id=modelo_id)
    if categoria_id:
        repuestos = repuestos.filter(categoria_id=categoria_id)
    if critico:
        repuestos = repuestos.filter(stock_actual__lte=F("stock_minimo"))

    repuestos = repuestos.order_by("nombre")

    paginator = Paginator(repuestos, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    marcas = Marca.objects.filter(activa=True).order_by("nombre")
    modelos = Modelo.objects.select_related("marca").all()
    categorias = Categoria.objects.all().order_by("nombre")

    return render(
        request,
        "inventario/repuesto_list.html",
        {
            "page_obj": page_obj,
            "marcas": marcas,
            "modelos": modelos,
            "categorias": categorias,
            "query": query,
        },
    )


@login_required
def repuesto_create(request):
    if request.method == "POST":
        form = RepuestoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Repuesto creado correctamente.")
            return redirect("inventario:repuesto_list")
    else:
        form = RepuestoForm()
    return render(
        request, "inventario/repuesto_form.html", {"form": form, "action": "Crear"}
    )


@login_required
def repuesto_edit(request, pk):
    repuesto = get_object_or_404(Repuesto, pk=pk)
    if request.method == "POST":
        form = RepuestoForm(request.POST, request.FILES, instance=repuesto)
        if form.is_valid():
            form.save()
            messages.success(request, "Repuesto actualizado correctamente.")
            return redirect("inventario:repuesto_list")
    else:
        form = RepuestoForm(instance=repuesto)
    return render(
        request, "inventario/repuesto_form.html", {"form": form, "action": "Editar"}
    )


@login_required
def repuesto_delete(request, pk):
    repuesto = get_object_or_404(Repuesto, pk=pk)
    if request.method == "POST":
        repuesto.delete()
        messages.success(request, "Repuesto eliminado correctamente.")
        return redirect("inventario:repuesto_list")
    return render(
        request,
        "inventario/repuesto_confirm_delete.html",
        {"object": repuesto, "type": "repuesto"},
    )


@login_required
def repuesto_detail(request, pk):
    repuesto = get_object_or_404(
        Repuesto.objects.select_related("marca", "modelo", "categoria"), pk=pk
    )
    return render(request, "inventario/repuesto_detail.html", {"repuesto": repuesto})


def get_modelos(request):
    marca_id = request.GET.get("marca_id")
    if marca_id:
        modelos = Modelo.objects.filter(marca_id=marca_id).order_by("nombre")
        data = [{"id": m.id, "nombre": str(m)} for m in modelos]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)


def buscar_repuestos(request):
    query = request.GET.get("q", "")
    if len(query) < 2:
        return JsonResponse([], safe=False)

    repuestos = (
        Repuesto.objects.filter(activo=True, stock_actual__gt=0)
        .select_related("marca", "modelo", "categoria")
        .filter(
            Q(codigo__icontains=query)
            | Q(nombre__icontains=query)
            | Q(marca__nombre__icontains=query)
            | Q(categoria__nombre__icontains=query)
        )[:20]
    )

    data = [
        {
            "id": r.id,
            "codigo": r.codigo,
            "nombre": r.nombre,
            "marca": r.marca.nombre,
            "modelo": str(r.modelo) if r.modelo else "",
            "categoria": r.categoria.nombre,
            "precio_venta": float(r.precio_venta),
            "stock": r.stock_actual,
            "critico": r.esta_critico,
        }
        for r in repuestos
    ]
    return JsonResponse(data, safe=False)
