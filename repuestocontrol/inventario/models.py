from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


class Marca(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    pais = models.CharField(max_length=100, blank=True, verbose_name="País de origen")
    activa = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Marca"
        verbose_name_plural = "Marcas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Modelo(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Nombre del modelo")
    marca = models.ForeignKey(
        Marca, on_delete=models.CASCADE, related_name="modelos", verbose_name="Marca"
    )
    anio_inicio = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Año inicio"
    )
    anio_fin = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Año fin"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Modelo"
        verbose_name_plural = "Modelos"
        ordering = ["marca", "nombre"]
        unique_together = ["nombre", "marca"]

    def __str__(self):
        return f"{self.marca.nombre} {self.nombre}"


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Repuesto(models.Model):
    class Ubicacion(models.TextChoices):
        BODEGA_A = "bodega_a", "Bodega A"
        BODEGA_B = "bodega_b", "Bodega B"
        BODEGA_C = "bodega_c", "Bodega C"
        ESTANTE_1 = "estante_1", "Estante 1"
        ESTANTE_2 = "estante_2", "Estante 2"
        ESTANTE_3 = "estante_3", "Estante 3"

    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código interno")
    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    marca = models.ForeignKey(
        Marca,
        on_delete=models.PROTECT,
        related_name="repuestos",
        verbose_name="Marca compatible",
    )
    modelo = models.ForeignKey(
        Modelo,
        on_delete=models.PROTECT,
        related_name="repuestos",
        verbose_name="Modelo compatible",
        null=True,
        blank=True,
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="repuestos",
        verbose_name="Categoría",
    )
    precio_compra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Precio de compra",
    )
    precio_venta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Precio de venta",
    )
    stock_actual = models.PositiveIntegerField(default=0, verbose_name="Stock actual")
    stock_minimo = models.PositiveIntegerField(default=5, verbose_name="Stock mínimo")
    ubicacion = models.CharField(
        max_length=50,
        choices=Ubicacion.choices,
        blank=True,
        verbose_name="Ubicación en bodega",
    )
    imagen = models.ImageField(
        upload_to="repuestos/", blank=True, null=True, verbose_name="Imagen"
    )
    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Repuesto"
        verbose_name_plural = "Repuestos"
        ordering = ["nombre"]
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["nombre"]),
            models.Index(fields=["marca", "modelo"]),
            models.Index(fields=["categoria"]),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    @property
    def esta_critico(self):
        return self.stock_actual <= self.stock_minimo

    @property
    def ganancia(self):
        return self.precio_venta - self.precio_compra
