from django.shortcuts import render, redirect, get_object_or_404
from .models import Cliente
from .forms import ClienteForm
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from datetime import datetime

@login_required
def home(request):
    return render(request, "core/home.html", {"year": datetime.now().year})
@login_required
def listar_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, "core/clientes_list.html", {"clientes": clientes})

@login_required
def crear_cliente(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("listar_clientes")
    else:
        form = ClienteForm()
    return render(request, "core/cliente_form.html", {"form": form})

@login_required
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect("listar_clientes")
    else:
        form = ClienteForm(instance=cliente)
    return render(request, "core/cliente_form.html", {"form": form})

@login_required
def eliminar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == "POST":
        cliente.delete()
        return redirect("listar_clientes")
    return render(request, "core/cliente_confirm_delete.html", {"cliente": cliente})