"""
Módulo de Envío de Emails para Comprobantes Electrónicos

Este módulo implementa el envío de emails con los comprobantes electrónicos
autorizados por el SRI, incluyendo:
- XML del comprobante firmado y autorizado
- PDF RIDE del comprobante
- Configuración SMTP flexible (Gmail, servidor corporativo, etc.)
"""

import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
from pathlib import Path
from io import BytesIO

from django.core.mail import send_mail, EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings

logger = logging.getLogger(__name__)


class ErrorEmail(Exception):
    """Excepción para errores de envío de email"""

    pass


class ConfiguracionEmail:
    """
    Configuración SMTP para envío de comprobantes electrónicos

    Los valores se leen desde variables de entorno:
    - EMAIL_HOST: Servidor SMTP (smtp.gmail.com, etc.)
    - EMAIL_PORT: Puerto SMTP (587, 465, etc.)
    - EMAIL_HOST_USER: Usuario SMTP
    - EMAIL_HOST_PASSWORD: Contraseña SMTP
    - EMAIL_USE_TLS: Usar TLS (True/False)
    - EMAIL_USE_SSL: Usar SSL (True/False)
    - EMAIL_DEFAULT_FROM: Email remitente por defecto
    """

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Obtiene la configuración de email desde settings"""
        return {
            "host": getattr(settings, "EMAIL_HOST", "smtp.gmail.com"),
            "port": getattr(settings, "EMAIL_PORT", 587),
            "username": getattr(settings, "EMAIL_HOST_USER", ""),
            "password": getattr(settings, "EMAIL_HOST_PASSWORD", ""),
            "use_tls": getattr(settings, "EMAIL_USE_TLS", True),
            "use_ssl": getattr(settings, "EMAIL_USE_SSL", False),
            "from_email": getattr(
                settings,
                "DEFAULT_FROM_EMAIL",
                getattr(settings, "EMAIL_HOST_USER", "noreply@empresa.com"),
            ),
            "timeout": getattr(settings, "EMAIL_TIMEOUT", 30),
        }

    @classmethod
    def is_configured(cls) -> bool:
        """Verifica si el email está configurado"""
        config = cls.get_config()
        return bool(config["username"] and config["password"])


class GestorEmailComprobantes:
    """
    Gestor de envío de emails con comprobantes electrónicos

    Attributes:
        config: Configuración SMTP
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa el gestor de emails

        Args:
            config: Configuración SMTP opcional
        """
        self.config = config or ConfiguracionEmail.get_config()

    def verificar_conexion(self) -> bool:
        """
        Verifica la conexión con el servidor SMTP

        Returns:
            True si la conexión es exitosa
        """
        try:
            backend = EmailBackend(
                host=self.config["host"],
                port=self.config["port"],
                username=self.config["username"],
                password=self.config["password"],
                use_tls=self.config["use_tls"],
                use_ssl=self.config["use_ssl"],
                timeout=self.config["timeout"],
                fail_silently=False,
            )

            # Intentar abrir conexión
            connection = backend.open()
            backend.close()

            return connection is True

        except Exception as e:
            logger.error(f"Error al verificar conexión SMTP: {str(e)}")
            return False

    def enviar_comprobante(
        self,
        destinatario: str,
        numero_factura: str,
        xml_content: bytes,
        pdf_content: Optional[bytes] = None,
        datos_extra: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Envía un comprobante electrónico por email

        Args:
            destinatario: Email del destinatario
            numero_factura: Número de la factura
            xml_content: Contenido del XML autorizado
            pdf_content: Contenido del PDF RIDE (opcional)
            datos_extra: Datos adicionales para el email

        Returns:
            True si el envío fue exitoso
        """
        datos = datos_extra or {}

        # Preparar asunto
        asunto = f"Comprobante Electrónico - Factura {numero_factura}"

        # Preparar cuerpo del email
        cuerpo = self._generar_cuerpo_email(numero_factura, datos)

        try:
            # Crear email multipart
            email = EmailMultiAlternatives(
                subject=asunto,
                body=cuerpo,
                from_email=self.config["from_email"],
                to=[destinatario],
                connection=self._get_connection(),
            )

            # Adjuntar XML
            email.attach(
                filename=f"{numero_factura}.xml",
                content=xml_content,
                mimetype="application/xml",
            )

            # Adjuntar PDF si está disponible
            if pdf_content:
                email.attach(
                    filename=f"{numero_factura}.pdf",
                    content=pdf_content,
                    mimetype="application/pdf",
                )

            # Enviar
            email.send(fail_silently=False)

            logger.info(f"Email enviado correctamente a {destinatario}")
            return True

        except Exception as e:
            logger.error(f"Error al enviar email: {str(e)}")
            raise ErrorEmail(f"Error al enviar email: {str(e)}")

    def _get_connection(self):
        """Obtiene una conexión SMTP"""
        return EmailBackend(
            host=self.config["host"],
            port=self.config["port"],
            username=self.config["username"],
            password=self.config["password"],
            use_tls=self.config["use_tls"],
            use_ssl=self.config["use_ssl"],
            timeout=self.config["timeout"],
            fail_silently=False,
        )

    def _generar_cuerpo_email(self, numero_factura: str, datos: Dict[str, Any]) -> str:
        """
        Genera el cuerpo del email

        Args:
            numero_factura: Número de factura
            datos: Datos adicionales

        Returns:
            Cuerpo del email en texto plano
        """
        razon_social = datos.get("razon_social", "Empresa")
        cliente = datos.get("cliente", "Cliente")
        total = datos.get("total", "0.00")
        fecha = datos.get("fecha", "")

        cuerpo = f"""
Estimado/a cliente,

Se le hace llegar su comprobante electrónico.

DATOS DEL COMPROBANTE:
- Número: {numero_factura}
- Fecha: {fecha}
- Cliente: {cliente}
- Total: ${total}

Este comprobante ha sido autorizado por el SRI.

Archivos adjuntos:
- Comprobante electrónico en formato XML
- Representación impresa (PDF)

Por favor conserve este documento para sus registros.

Saludos cordiales,
{razon_social}

---
Este es un correo automático, por favor no responder directamente.
"""

        return cuerpo.strip()

    def enviar_email_test(self, destinatario: str) -> bool:
        """
        Envía un email de prueba

        Args:
            destinatario: Email de prueba

        Returns:
            True si fue exitoso
        """
        try:
            send_mail(
                subject="Prueba de configuración - Facturación Electrónica",
                message="Esta es una prueba de configuración del sistema de facturación electrónica.",
                from_email=self.config["from_email"],
                recipient_list=[destinatario],
                fail_silently=False,
                connection=self._get_connection(),
            )
            return True
        except Exception as e:
            logger.error(f"Error en email de prueba: {str(e)}")
            return False


def enviar_comprobante_electronico(
    venta,
    xml_content: bytes,
    pdf_content: Optional[bytes] = None,
) -> bool:
    """
    Función de conveniencia para enviar comprobante electrónico

    Args:
        venta: Instancia del modelo Venta
        xml_content: Contenido XML del comprobante
        pdf_content: Contenido PDF del RIDE

    Returns:
        True si el envío fue exitoso
    """
    # Obtener email del cliente
    destinatario = venta.cliente_email

    if not destinatario:
        logger.warning(f"Cliente sin email, no se puede enviar comprobante")
        return False

    # Verificar configuración
    if not ConfiguracionEmail.is_configured():
        logger.error("Email no configurado")
        return False

    # Crear gestor
    gestor = GestorEmailComprobantes()

    # Datos extras
    from repuestocontrol.core.models import Configuracion

    config = Configuracion.get_config()

    datos_extra = {
        "razon_social": config.razon_social if config else "Empresa",
        "cliente": venta.cliente_nombre,
        "total": str(venta.total),
        "fecha": venta.created_at.strftime("%d/%m/%Y"),
    }

    # Enviar
    try:
        return gestor.enviar_comprobante(
            destinatario=destinatario,
            numero_factura=venta.numero_factura,
            xml_content=xml_content,
            pdf_content=pdf_content,
            datos_extra=datos_extra,
        )
    except ErrorEmail as e:
        logger.error(f"Error al enviar comprobante: {str(e)}")
        return False


def test_configuracion_email(email_test: str) -> Dict[str, Any]:
    """
    Prueba la configuración de email

    Args:
        email_test: Email para probar

    Returns:
        Diccionario con resultado
    """
    resultado = {"success": False, "message": "", "details": {}}

    if not ConfiguracionEmail.is_configured():
        resultado["message"] = "Email no configurado"
        return resultado

    gestor = GestorEmailComprobantes()

    # Probar conexión
    try:
        if gestor.verificar_conexion():
            resultado["details"]["conexion"] = "OK"
        else:
            resultado["message"] = "No se pudo conectar al servidor SMTP"
            return resultado
    except Exception as e:
        resultado["message"] = f"Error de conexión: {str(e)}"
        return resultado

    # Probar envío
    try:
        if gestor.enviar_email_test(email_test):
            resultado["success"] = True
            resultado["message"] = "Email de prueba enviado correctamente"
        else:
            resultado["message"] = "Error al enviar email de prueba"
    except Exception as e:
        resultado["message"] = f"Error: {str(e)}"

    return resultado
