from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("clientes/", views.listar_clientes, name="listar_clientes"),
    path("clientes/nuevo/", views.crear_cliente, name="crear_cliente"),
    path("clientes/editar/<int:pk>/", views.editar_cliente, name="editar_cliente"),
    path("clientes/eliminar/<int:pk>/", views.eliminar_cliente, name="eliminar_cliente"),
]
