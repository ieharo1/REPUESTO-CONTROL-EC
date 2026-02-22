from django.contrib import admin
from .models import Cliente, Venta, DetalleVenta


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ["nombre", "cedula", "tipo_identificacion", "telefono", "email"]
    search_fields = ["nombre", "cedula", "telefono"]
    list_filter = ["tipo_identificacion"]


class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 0
    readonly_fields = ["repuesto", "cantidad", "precio_unitario", "subtotal"]


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = [
        "numero",
        "numero_factura",
        "cliente",
        "vendedor",
        "total",
        "metodo_pago",
        "estado",
        "estado_sri",
        "created_at",
    ]
    list_filter = ["estado", "metodo_pago", "estado_sri", "created_at"]
    search_fields = ["numero", "numero_factura", "cliente__nombre"]
    readonly_fields = [
        "numero",
        "numero_factura",
        "subtotal_12",
        "subtotal_0",
        "iva",
        "total",
        "created_at",
        "updated_at",
    ]
    inlines = [DetalleVentaInline]
