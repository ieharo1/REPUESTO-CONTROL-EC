"""
Módulo de Procesamiento Completo de Facturación Electrónica SRI

Este módulo integra todos los componentes para el procesamiento completo
de comprobantes electrónicos:
1. Generación de clave de acceso
2. Generación de XML
3. Validación XSD
4. Firma digital
5. Envío al SRI
6. Autorización
7. Generación de PDF RIDE
8. Envío de email

Flujo principal:
1. Crear comprobante XML
2. Validar contra XSD
3. Firmar digitalmente
4. Enviar al SRI (recepción)
5. Consultar autorización
6. Generar PDF RIDE
7. Enviar email al cliente
"""

import logging
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from enum import Enum

from django.conf import settings
from django.db import transaction
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


class EstadoProcesamiento(str, Enum):
    """Estados del procesamiento"""

    PENDIENTE = "pendiente"
    XML_GENERADO = "xml_generado"
    VALIDADO = "validado"
    FIRMADO = "firmado"
    ENVIADO_SRI = "enviado_sri"
    AUTORIZADO = "autorizado"
    DEVUELTO = "devuelto"
    ERROR = "error"


class ErrorFacturacionElectronica(Exception):
    """Excepción base para errores de facturación electrónica"""

    pass


class ErrorValidacionXML(ErrorFacturacionElectronica):
    """Error en validación XSD"""

    pass


class ErrorFirmaDigital(ErrorFacturacionElectronica):
    """Error en firma digital"""

    pass


class ErrorEnvioSRI(ErrorFacturacionElectronica):
    """Error en envío al SRI"""

    pass


from enum import Enum


class ProcesadorFacturaElectronica:
    """
    Procesador completo de facturas electrónicas

    Integra todos los componentes del sistema de facturación electrónica
    """

    def __init__(self):
        # Importar módulos
        from repuestocontrol.core.sri import (
            generar_xml_factura,
            generar_clave_acceso,
            formatear_numero_factura,
        )
        from repuestocontrol.core.validacion_xsd import validar_factura_sri
        from repuestocontrol.core.firma_digital import FirmaDigital
        from repuestocontrol.core.sri_ws import procesar_comprobante, SRIWebService
        from repuestocontrol.core.generador_pdf import generar_pdf_rid
        from repuestocontrol.core.email_comprobantes import (
            enviar_comprobante_electronico,
        )

        self.generar_xml = generar_xml_factura
        self.generar_clave = generar_clave_acceso
        self.formatear_numero = formatear_numero_factura
        self.validar_xsd = validar_factura_sri
        self.FirmaDigital = FirmaDigital
        self.procesar_sri = procesar_comprobante
        self.SRIWebService = SRIWebService
        self.generar_pdf = generar_pdf_rid
        self.enviar_email = enviar_comprobante_electronico

    def procesar_factura(
        self,
        venta,
        config,
        firmar: bool = True,
        enviar_sri: bool = True,
        enviar_email: bool = True,
    ) -> Dict[str, Any]:
        """
        Procesa una factura electrónica de forma completa

        Args:
            venta: Instancia del modelo Venta
            config: Instancia de Configuracion
            firmar: Si True, firma digitalmente
            enviar_sri: Si True, envía al SRI
            enviar_email: Si True, envía email al cliente

        Returns:
            Diccionario con resultado del procesamiento
        """
        logger.info("=" * 60)
        logger.info(f"INICIANDO PROCESAMIENTO FACTURA ELECTRÓNICA")
        logger.info(f"Venta: {venta.numero}")
        logger.info(f"Cliente: {venta.cliente_nombre}")
        logger.info("=" * 60)

        resultado = {
            "success": False,
            "estado": "pendiente",
            "clave_acceso": "",
            "numero_factura": "",
            "numero_autorizacion": "",
            "fecha_autorizacion": "",
            "xml": "",
            "xml_firmado": "",
            "pdf": None,
            "errores": [],
            "mensajes": [],
        }

        try:
            # Paso 1: Generar XML
            logger.info("[1/6] Generando XML...")
            xml_data = self.generar_xml(venta, config)
            resultado["xml"] = xml_data["xml"]
            resultado["clave_acceso"] = xml_data["clave_acceso"]
            resultado["numero_factura"] = xml_data["numero_factura"]
            resultado["estado"] = "xml_generado"
            logger.info(f"XML generado - Clave: {resultado['clave_acceso']}")

            # Paso 2: Validar XSD
            logger.info("[2/6] Validando contra XSD...")
            es_valido, errores_xsd = self.validar_xsd(xml_data["xml"])

            if not es_valido:
                resultado["errores"].extend(errores_xsd)
                resultado["estado"] = "error_validacion"
                logger.warning(f"Validación XSD falló: {errores_xsd}")

                # En ambiente de pruebas, continuar de todas formas
                if config.ambiente != "1":  # No es pruebas
                    raise ErrorValidacionXML(f"Validación XSD falló: {errores_xsd}")
                else:
                    logger.warning("Ambiente PRUEBAS: continuando despite XSD error")

            resultado["estado"] = "validado"

            # Paso 3: Firmar digitalmente
            if firmar:
                logger.info("[3/6] Firmando digitalmente...")
                xml_firmado = self._firmar_xml(xml_data["xml"], config)
                resultado["xml_firmado"] = xml_firmado
                resultado["estado"] = "firmado"
            else:
                resultado["xml_firmado"] = xml_data["xml"]

            # Paso 4: Enviar al SRI
            if enviar_sri:
                logger.info("[4/6] Enviando al SRI...")
                resultado_sri = self._enviar_al_sri(
                    resultado["xml_firmado"], resultado["clave_acceso"], config.ambiente
                )

                resultado["estado"] = resultado_sri.get("estado_final", "error")
                resultado["numero_autorizacion"] = resultado_sri.get(
                    "autorizacion", {}
                ).get("numero_autorizacion", "")
                resultado["fecha_autorizacion"] = resultado_sri.get(
                    "autorizacion", {}
                ).get("fecha_autorizacion", "")

                if resultado_sri.get("errores"):
                    resultado["errores"].extend(resultado_sri["errores"])

                # Guardar XML autorizado si existe
                if resultado_sri.get("autorizacion", {}).get("xml"):
                    resultado["xml_autorizado"] = resultado_sri["autorizacion"]["xml"]
            else:
                # Simular autorización en pruebas
                if config.ambiente == "1":
                    resultado["estado"] = "autorizado"
                    resultado["numero_autorizacion"] = resultado["clave_acceso"]
                    resultado["fecha_autorizacion"] = datetime.now().strftime(
                        "%d/%m/%Y %H:%M:%S"
                    )
                    resultado["xml_autorizado"] = resultado["xml_firmado"]

            # Paso 5: Generar PDF RIDE
            logger.info("[5/6] Generando PDF RIDE...")
            try:
                pdf_bytes = self.generar_pdf(venta, config)
                resultado["pdf"] = pdf_bytes
            except Exception as e:
                logger.error(f"Error al generar PDF: {str(e)}")
                resultado["mensajes"].append(f"PDF no generado: {str(e)}")

            # Paso 6: Enviar email
            if enviar_email and resultado["pdf"]:
                logger.info("[6/6] Enviando email al cliente...")
                try:
                    self._enviar_email_cliente(
                        venta,
                        resultado["xml_firmado"].encode("utf-8"),
                        resultado["pdf"],
                    )
                    resultado["mensajes"].append("Email enviado")
                except Exception as e:
                    logger.error(f"Error al enviar email: {str(e)}")
                    resultado["mensajes"].append(f"Email no enviado: {str(e)}")

            # Determinar éxito
            resultado["success"] = resultado["estado"] == "autorizado"

            if resultado["success"]:
                logger.info("FACTURA AUTORIZADA CORRECTAMENTE")
            else:
                logger.warning(f"Estado final: {resultado['estado']}")

        except Exception as e:
            logger.error(f"Error en procesamiento: {str(e)}")
            resultado["errores"].append(str(e))
            resultado["estado"] = "error"

        logger.info("=" * 60)
        logger.info(f"FINALIZADO - Estado: {resultado['estado']}")
        logger.info("=" * 60)

        return resultado

    def _firmar_xml(self, xml_content: str, config) -> str:
        """
        Firma el XML con el certificado digital

        Args:
            xml_content: Contenido XML
            config: Configuración

        Returns:
            XML firmado
        """
        try:
            # Verificar que existe certificado
            if not config.certificado_path:
                raise ErrorFirmaDigital("Certificado digital no configurado")

            if not os.path.exists(config.certificado_path):
                raise ErrorFirmaDigital(
                    f"Certificado no encontrado: {config.certificado_path}"
                )

            # Crear instancia de firma
            firma = self.FirmaDigital(
                certificado_path=config.certificado_path,
                contrasena=config.certificado_password,
                ambiente=config.ambiente,
            )

            # Firmar
            xml_firmado = firma.firmar_xml(xml_content)

            logger.info("XML firmado correctamente")
            return xml_firmado

        except Exception as e:
            logger.error(f"Error al firmar: {str(e)}")
            raise ErrorFirmaDigital(f"Error al firmar: {str(e)}")

    def _enviar_al_sri(
        self, xml_content: str, clave_acceso: str, ambiente: str
    ) -> Dict[str, Any]:
        """
        Envía el comprobante al SRI y consulta autorización

        Args:
            xml_content: Contenido XML firmado
            clave_acceso: Clave de acceso
            ambiente: Ambiente (1=pruebas, 2=producción)

        Returns:
            Resultado del procesamiento
        """
        try:
            resultado = self.procesar_sri(
                xml_content=xml_content,
                clave_acceso=clave_acceso,
                ambiente=ambiente,
                timeout=60,
            )

            return resultado

        except Exception as e:
            logger.error(f"Error al enviar al SRI: {str(e)}")
            raise ErrorEnvioSRI(f"Error al enviar al SRI: {str(e)}")

    def _enviar_email_cliente(
        self, venta, xml_content: bytes, pdf_content: bytes
    ) -> bool:
        """
        Envía el comprobante al cliente por email

        Args:
            venta: Instancia de Venta
            xml_content: Contenido XML
            pdf_content: Contenido PDF

        Returns:
            True si fue exitoso
        """
        try:
            return self.enviar_email(venta, xml_content, pdf_content)
        except Exception as e:
            logger.error(f"Error al enviar email: {str(e)}")
            return False

    def verificar_estado_sri(
        self, clave_acceso: str, ambiente: str = "1"
    ) -> Dict[str, Any]:
        """
        Verifica el estado de un comprobante en el SRI

        Args:
            clave_acceso: Clave de acceso
            ambiente: Ambiente

        Returns:
            Estado del comprobante
        """
        try:
            sri = self.SRIWebService(ambiente=ambiente)
            resultado = sri.autorizacion_comprobante(clave_acceso)

            return {
                "success": True,
                "estado": resultado.get("estado", "DESCONOCIDO"),
                "numero_autorizacion": resultado.get("numero_autorizacion", ""),
                "fecha_autorizacion": resultado.get("fecha_autorizacion", ""),
                "xml": resultado.get("xml", ""),
                "mensajes": resultado.get("mensajes", []),
            }

        except Exception as e:
            logger.error(f"Error al verificar estado: {str(e)}")
            return {"success": False, "error": str(e)}


def procesar_factura_electronica(venta, config, **kwargs) -> Dict[str, Any]:
    """
    Función de conveniencia para procesar factura electrónica

    Args:
        venta: Instancia de Venta
        config: Instancia de Configuracion
        **kwargs: Argumentos adicionales

    Returns:
        Resultado del procesamiento
    """
    procesador = ProcesadorFacturaElectronica()
    return procesador.procesar_factura(venta, config, **kwargs)


def verificar_estado_factura(clave_acceso: str, ambiente: str = "1") -> Dict[str, Any]:
    """
    Función de conveniencia para verificar estado en SRI

    Args:
        clave_acceso: Clave de acceso
        ambiente: Ambiente

    Returns:
        Estado del comprobante
    """
    procesador = ProcesadorFacturaElectronica()
    return procesador.verificar_estado_sri(clave_acceso, ambiente)
