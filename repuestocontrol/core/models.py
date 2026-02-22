from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class Configuracion(models.Model):
    """Configuración de la empresa para facturación electrónica SRI"""

    class TipoContribuyente(models.TextChoices):
        PERSONA_NATURAL = "persona_natural", "Persona Natural"
        SOCIEDAD = "sociedad", "Sociedad"

    class TipoRegimen(models.TextChoices):
        GENERAL = "general", "Régimen General"
        RIMPE = "rimpe", "RIMPE"
        RURAL = "rural", "Rural"

    class Ambiente(models.TextChoices):
        PRUEBAS = "1", "Pruebas"
        PRODUCCION = "2", "Producción"

    class TipoEmision(models.TextChoices):
        NORMAL = "1", "Normal"
        INDISPONIBLE = "2", "Indisponible"

    # Información de la Empresa (SRI)
    razon_social = models.CharField(max_length=200, verbose_name="Razón Social")
    nombre_comercial = models.CharField(
        max_length=200, blank=True, verbose_name="Nombre Comercial"
    )
    ruc = models.CharField(max_length=13, verbose_name="RUC", help_text="13 dígitos")
    direccion_matriz = models.TextField(verbose_name="Dirección Matriz")
    direccion_sucursal = models.TextField(blank=True, verbose_name="Dirección Sucursal")
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    email = models.EmailField(verbose_name="Email")

    # Configuración SRI
    establecimiento = models.CharField(
        max_length=3, default="001", verbose_name="Establecimiento"
    )
    punto_emision = models.CharField(
        max_length=3, default="001", verbose_name="Punto de Emisión"
    )

    # Secuenciales por tipo de comprobante
    secuencia_factura = models.PositiveIntegerField(
        default=1, verbose_name="Secuencial Factura"
    )
    secuencia_nota_credito = models.PositiveIntegerField(
        default=1, verbose_name="Secuencial Nota Crédito"
    )
    secuencia_nota_debito = models.PositiveIntegerField(
        default=1, verbose_name="Secuencial Nota Débito"
    )
    secuencia_guia_remision = models.PositiveIntegerField(
        default=1, verbose_name="Secuencial Guía Remisión"
    )
    secuencia_retencion = models.PositiveIntegerField(
        default=1, verbose_name="Secuencial Retención"
    )

    # Impuestos configurables - TARIFAS IVA
    iva_tarifa_12 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=12.00,
        verbose_name="Tarifa IVA 12%",
        help_text="Porcentaje IVA categoría gravada",
    )
    iva_tarifa_14 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="Tarifa IVA 14%",
        help_text="Porcentaje IVA categoría gravada (si aplica)",
    )
    ice_tarifa = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="Tarifa ICE (%)",
        help_text="Porcentaje Impuesto Consumos Especiales",
    )
    irbp_tarifa = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        verbose_name="Tarifa IRBP (%)",
        help_text="Porcentaje IRBP (solo aplicable en ciertos productos)",
    )

    # Contabilidad
    obligado_contabilidad = models.BooleanField(
        default=False, verbose_name="Obligado a llevar contabilidad"
    )
    tipo_contribuyente = models.CharField(
        max_length=20,
        choices=TipoContribuyente.choices,
        default=TipoContribuyente.SOCIEDAD,
        verbose_name="Tipo de Contribuyente",
    )
    regimen_tributario = models.CharField(
        max_length=20,
        choices=TipoRegimen.choices,
        default=TipoRegimen.GENERAL,
        verbose_name="Régimen Tributario",
    )
    contribuyente_especial = models.BooleanField(
        default=False, verbose_name="Contribuyente Especial"
    )
    resolucion_contribuyente = models.CharField(
        max_length=50, blank=True, verbose_name="Resolución Contribuyente Especial"
    )

    # Ambiente de trabajo
    ambiente = models.CharField(
        max_length=1,
        choices=Ambiente.choices,
        default=Ambiente.PRUEBAS,
        verbose_name="Ambiente",
    )
    tipo_emision = models.CharField(
        max_length=1,
        choices=TipoEmision.choices,
        default=TipoEmision.NORMAL,
        verbose_name="Tipo de Emisión",
    )

    # Certificado digital
    certificado_archivo = models.FileField(
        upload_to="certificados/",
        blank=True,
        null=True,
        verbose_name="Archivo certificado (.p12)",
    )
    certificado_password = models.CharField(
        max_length=100, blank=True, verbose_name="Clave certificado"
    )

    # Configuración adicional
    enviar_email_auto = models.BooleanField(
        default=True, verbose_name="Enviar email automáticamente al cliente"
    )
    plantilla_email = models.TextField(
        blank=True,
        verbose_name="Plantilla email",
        help_text="Use {{cliente}}, {{numero_factura}}, {{total}} para variables",
    )

    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración"
        verbose_name_plural = "Configuración"

    def __str__(self):
        return f"Config - {self.razon_social} ({self.ruc})"

    @classmethod
    def get_config(cls):
        """Obtiene la configuración activa"""
        config = cls.objects.filter(activo=True).first()
        if not config:
            config = cls.objects.first()
        return config

    def get_siguiente_secuencial(self, tipo="01"):
        """Obtiene y incrementa el secuencial según el tipo de comprobante"""
        campos = {
            "01": "secuencia_factura",
            "04": "secuencia_nota_credito",
            "05": "secuencia_nota_debito",
            "06": "secuencia_guia_remision",
            "07": "secuencia_retencion",
        }

        campo = campos.get(tipo, "secuencia_factura")
        seq = getattr(self, campo)
        setattr(self, campo, seq + 1)
        self.save(update_fields=[campo])
        return seq

    def generar_numero_factura(self, secuencial=None, tipo="01"):
        """Genera el número de comprobante: 001-001-000000001"""
        if secuencial is None:
            secuencial = self.get_siguiente_secuencial(tipo)
        return f"{self.establecimiento}-{self.punto_emision}-{str(secuencial).zfill(9)}"

    def get_certificado_path(self):
        """Obtiene la ruta del certificado"""
        if self.certificado_archivo:
            return self.certificado_archivo.path
        return None


class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        ADMINISTRADOR = "administrador", "Administrador"
        VENDEDOR = "vendedor", "Vendedor"

    rol = models.CharField(
        max_length=20, choices=Rol.choices, default=Rol.VENDEDOR, verbose_name="Rol"
    )
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")
    avatar = models.ImageField(
        upload_to="avatars/", blank=True, null=True, verbose_name="Avatar"
    )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"

    @property
    def is_admin(self):
        return self.rol == self.Rol.ADMINISTRADOR

    @property
    def is_vendedor(self):
        return self.rol == self.Rol.VENDEDOR
