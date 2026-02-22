from django.urls import path
from . import views

app_name = "inventario"

urlpatterns = [
    path("marcas/", views.marca_list, name="marca_list"),
    path("marcas/crear/", views.marca_create, name="marca_create"),
    path("marcas/<int:pk>/editar/", views.marca_edit, name="marca_edit"),
    path("marcas/<int:pk>/eliminar/", views.marca_delete, name="marca_delete"),
    path("modelos/", views.modelo_list, name="modelo_list"),
    path("modelos/crear/", views.modelo_create, name="modelo_create"),
    path("modelos/<int:pk>/editar/", views.modelo_edit, name="modelo_edit"),
    path("modelos/<int:pk>/eliminar/", views.modelo_delete, name="modelo_delete"),
    path("categorias/", views.categoria_list, name="categoria_list"),
    path("categorias/crear/", views.categoria_create, name="categoria_create"),
    path("categorias/<int:pk>/editar/", views.categoria_edit, name="categoria_edit"),
    path(
        "categorias/<int:pk>/eliminar/", views.categoria_delete, name="categoria_delete"
    ),
    path("repuestos/", views.repuesto_list, name="repuesto_list"),
    path("repuestos/crear/", views.repuesto_create, name="repuesto_create"),
    path("repuestos/<int:pk>/", views.repuesto_detail, name="repuesto_detail"),
    path("repuestos/<int:pk>/editar/", views.repuesto_edit, name="repuesto_edit"),
    path("repuestos/<int:pk>/eliminar/", views.repuesto_delete, name="repuesto_delete"),
    path("api/modelos/", views.get_modelos, name="get_modelos"),
    path("api/buscar/", views.buscar_repuestos, name="buscar_repuestos"),
]
