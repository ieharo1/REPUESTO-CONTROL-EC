from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from repuestocontrol.inventario.models import Repuesto


class Cliente(models.Model):
    class TipoIdentificacion(models.TextChoices):
        CONSUMIDOR_FINAL = "consumidor_final", "Consumidor Final"
        RUC = "ruc", "RUC"
        CEDULA = "cedula", "Cédula"
        PASAPORTE = "pasaporte", "Pasaporte"

    nombre = models.CharField(max_length=200, verbose_name="Nombre/Razón Social")
    cedula = models.CharField(
        max_length=20, blank=True, verbose_name="Cédula/RUC/Pasaporte"
    )
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    email = models.EmailField(blank=True, verbose_name="Email")
    direccion = models.TextField(blank=True, verbose_name="Dirección")
    tipo_identificacion = models.CharField(
        max_length=20,
        choices=TipoIdentificacion.choices,
        default=TipoIdentificacion.CONSUMIDOR_FINAL,
        verbose_name="Tipo de Identificación",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Venta(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        COMPLETADA = "completada", "Completada"
        CANCELADA = "cancelada", "Cancelada"
        ANULADA = "anulada", "Anulada"

    class MetodoPago(models.TextChoices):
        EFECTIVO = "efectivo", "Efectivo"
        TRANSFERENCIA = "transferencia", "Transferencia"
        TARJETA_DEBITO = "tarjeta_debito", "Tarjeta Débito"
        TARJETA_CREDITO = "tarjeta_credito", "Tarjeta Crédito"
        CHEQUE = "cheque", "Cheque"
        DIPLOMATICO = "diplomatico", "Diplomático"
        COMPENSACION = "compensacion", "Compensación"
        OTROS = "otros", "Otros"

    numero = models.CharField(
        max_length=20, unique=True, verbose_name="Número de venta"
    )

    numero_factura = models.CharField(
        max_length=17, blank=True, verbose_name="Número de Factura (SRI)"
    )
    secuencia_factura = models.PositiveIntegerField(
        default=1, verbose_name="Secuencial de Factura"
    )
    clave_acceso = models.CharField(
        max_length=49, blank=True, verbose_name="Clave de Acceso SRI"
    )
    estado_sri = models.CharField(
        max_length=20, default="pendiente", verbose_name="Estado SRI"
    )

    # Autorización SRI
    numero_autorizacion = models.CharField(
        max_length=49, blank=True, verbose_name="Número de Autorización"
    )
    fecha_autorizacion = models.CharField(
        max_length=30, blank=True, verbose_name="Fecha de Autorización"
    )
    xml_content = models.TextField(blank=True, verbose_name="XML del comprobante")
    xml_firmado = models.TextField(blank=True, verbose_name="XML firmado")

    establecimiento = models.CharField(
        max_length=3, default="001", verbose_name="Establecimiento"
    )
    punto_emision = models.CharField(
        max_length=3, default="001", verbose_name="Punto de Emisión"
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ventas",
        verbose_name="Cliente",
    )

    cliente_nombre = models.CharField(
        max_length=200, blank=True, verbose_name="Nombre del Cliente (Factura)"
    )
    cliente_identificacion = models.CharField(
        max_length=20, blank=True, verbose_name="Identificación del Cliente"
    )
    cliente_tipo_identificacion = models.CharField(
        max_length=20, blank=True, verbose_name="Tipo Identificación"
    )
    cliente_direccion = models.TextField(blank=True, verbose_name="Dirección Cliente")
    cliente_telefono = models.CharField(
        max_length=20, blank=True, verbose_name="Teléfono Cliente"
    )
    cliente_email = models.EmailField(blank=True, verbose_name="Email Cliente")

    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="ventas",
        verbose_name="Vendedor",
    )

    subtotal_12 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Subtotal 12%"
    )
    subtotal_0 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Subtotal 0%"
    )
    descuento = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Descuento"
    )
    iva = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="IVA"
    )
    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Total"
    )

    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        default=MetodoPago.EFECTIVO,
        verbose_name="Método de pago",
    )
    forma_pago_sri = models.CharField(
        max_length=2, default="01", verbose_name="Forma de Pago SRI"
    )

    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE,
        verbose_name="Estado",
    )
    notas = models.TextField(blank=True, verbose_name="Notas")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Venta"
        verbose_name_plural = "Ventas"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Venta {self.numero}"

    @property
    def ganancia(self):
        total_ganancia = 0
        for detalle in self.detalles.all():
            total_ganancia += (
                float(detalle.precio_unitario) - float(detalle.repuesto.precio_compra)
            ) * detalle.cantidad
        return total_ganancia


class DetalleVenta(models.Model):
    venta = models.ForeignKey(
        Venta, on_delete=models.CASCADE, related_name="detalles", verbose_name="Venta"
    )
    repuesto = models.ForeignKey(
        Repuesto,
        on_delete=models.PROTECT,
        related_name="ventas",
        verbose_name="Repuesto",
    )
    cantidad = models.PositiveIntegerField(
        default=1, validators=[MinValueValidator(1)], verbose_name="Cantidad"
    )
    precio_unitario = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Precio unitario"
    )
    descuento_item = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Descuento (%)",
        validators=[MaxValueValidator(100)],
    )
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Subtotal"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Detalle de venta"
        verbose_name_plural = "Detalles de venta"

    def __str__(self):
        return f"{self.repuesto.nombre} x{self.cantidad}"

    def save(self, *args, **kwargs):
        from decimal import Decimal

        descuento_decimal = Decimal(str(self.descuento_item)) / Decimal("100")
        precio_con_descuento = self.precio_unitario * (Decimal("1") - descuento_decimal)
        self.subtotal = self.cantidad * precio_con_descuento
        super().save(*args, **kwargs)
