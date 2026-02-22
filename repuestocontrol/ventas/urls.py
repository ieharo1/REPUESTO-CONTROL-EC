from django.urls import path
from . import views

app_name = "ventas"

urlpatterns = [
    path("", views.venta_list, name="venta_list"),
    path("crear/", views.venta_create, name="venta_create"),
    path("<int:pk>/", views.venta_detail, name="venta_detail"),
    path("<int:pk>/anular/", views.venta_anular, name="venta_anular"),
    path("<int:pk>/autorizar/", views.autorizar_factura, name="autorizar_factura"),
    path("<int:pk>/xml/", views.descargar_xml, name="descargar_xml"),
    path("<int:pk>/pdf/", views.descargar_pdf, name="descargar_pdf"),
    path("<int:pk>/verificar/", views.verificar_estado_sri, name="verificar"),
    path("clientes/", views.cliente_list, name="cliente_list"),
    path("clientes/crear/", views.cliente_create, name="cliente_create"),
    path("clientes/<int:pk>/editar/", views.cliente_edit, name="cliente_edit"),
    path("clientes/<int:pk>/eliminar/", views.cliente_delete, name="cliente_delete"),
    path("api/clientes/crear/", views.cliente_api_create, name="cliente_api_create"),
]
