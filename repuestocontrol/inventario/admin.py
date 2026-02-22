from django.contrib import admin
from .models import Marca, Modelo, Categoria, Repuesto


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "pais", "activa", "created_at"]
    list_filter = ["activa"]
    search_fields = ["nombre", "pais"]


@admin.register(Modelo)
class ModeloAdmin(admin.ModelAdmin):
    list_display = ["nombre", "marca", "anio_inicio", "anio_fin"]
    list_filter = ["marca"]
    search_fields = ["nombre", "marca__nombre"]


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "descripcion"]
    search_fields = ["nombre"]


@admin.register(Repuesto)
class RepuestoAdmin(admin.ModelAdmin):
    list_display = [
        "codigo",
        "nombre",
        "marca",
        "modelo",
        "categoria",
        "precio_venta",
        "stock_actual",
        "stock_minimo",
    ]
    list_filter = ["marca", "categoria", "activo"]
    search_fields = ["codigo", "nombre", "marca__nombre"]
    readonly_fields = ["created_at", "updated_at"]
