from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


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
    secuencia_factura = models.PositiveIntegerField(
        default=1, verbose_name="Secuencial de Factura"
    )

    # Impuestos configurables
    iva_tarifa = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=12.00,
        verbose_name="Tarifa IVA (%)",
        help_text="Porcentaje del IVA (12%, 14%, 15%)",
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
    certificado_path = models.CharField(
        max_length=500, blank=True, verbose_name="Ruta certificado (.p12)"
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

    def get_siguiente_secuencial(self):
        """Obtiene ycrementa el secuencial"""
        seq = self.secuencia_factura
        self.secuencia_factura += 1
        self.save()
        return seq

    def generar_numero_factura(self, secuencial=None):
        """Genera el número de factura: 001-001-000000001"""
        if secuencial is None:
            secuencial = self.get_siguiente_secuencial()
        return f"{self.establecimiento}-{self.punto_emision}-{str(secuencial).zfill(9)}"


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
