"""
Módulo de Validación XSD para Comprobantes Electrónicos SRI Ecuador

Este módulo implementa la validación de documentos XML contra los esquemas XSD
oficiales del SRI para garantizar que los comprobantes cumplen con la estructura
tributaria requerida.

Esquemas XSD del SRI:
- factura.xsd: Estructura de facturas
- notaCredito.xsd: Notas de crédito
- notaDebito.xsd: Notas de débito
- guiaRemision.xsd: Guías de remisión
- retencion.xsd: Retenciones

Referencias oficiales:
- https://www.sri.gob.ec/biometria-web
- https://www.sri.gob.ec/comprobantes-electronicos
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum

from lxml import etree
from lxml.etree import XMLSyntaxError

logger = logging.getLogger(__name__)


class TipoComprobante(str, Enum):
    """Tipos de comprobantes electrónicos"""

    FACTURA = "01"
    NOTA_CREDITO = "04"
    NOTA_DEBITO = "05"
    GUIA_REMISION = "06"
    RETENCION = "07"
    COMPROBANTE_PUBLICO = "08"


class ErrorValidacionXSD(Exception):
    """Excepción para errores de validación XSD"""

    pass


class ValidadorXSD:
    """
    Validador de esquemas XSD para comprobantes electrónicos SRI

    Attributes:
        xsd_path: Ruta al directorio con archivos XSD
    """

    # Mapeo de tipos de comprobante a archivo XSD
    XSD_MAP = {
        TipoComprobante.FACTURA: "factura.xsd",
        TipoComprobante.NOTA_CREDITO: "notaCredito.xsd",
        TipoComprobante.NOTA_DEBITO: "notaDebito.xsd",
        TipoComprobante.GUIA_REMISION: "guiaRemision.xsd",
        TipoComprobante.RETENCION: "retencion.xsd",
    }

    def __init__(self, xsd_path: Optional[str] = None):
        """
        Inicializa el validador XSD

        Args:
            xsd_path: Ruta al directorio con archivos XSD
        """
        if xsd_path is None:
            # Usar directorio por defecto
            base_dir = Path(__file__).parent.parent
            xsd_path = base_dir / "xsd"

        self.xsd_path = Path(xsd_path)

        # Cargar esquemas XSD
        self._esquemas: Dict[str, etree.XMLSchema] = {}
        self._cargar_esquemas()

    def _cargar_esquemas(self) -> None:
        """Carga los esquemas XSD del directorio"""
        if not self.xsd_path.exists():
            logger.warning(f"Directorio XSD no encontrado: {self.xsd_path}")
            return

        for tipo, filename in self.XSD_MAP.items():
            xsd_file = self.xsd_path / filename
            if xsd_file.exists():
                try:
                    with open(xsd_file, "rb") as f:
                        schema_doc = etree.parse(f)
                        schema = etree.XMLSchema(schema_doc)
                        self._esquemas[str(tipo)] = schema
                        logger.info(f"Esquema cargado: {filename}")
                except Exception as e:
                    logger.error(f"Error al cargar {filename}: {str(e)}")
            else:
                logger.warning(f"Archivo XSD no encontrado: {xsd_file}")

    def validar_xml(
        self,
        xml_content: str,
        tipo_comprobante: TipoComprobante = TipoComprobante.FACTURA,
    ) -> Tuple[bool, List[str]]:
        """
        Valida un XML contra el esquema XSD correspondiente

        Args:
            xml_content: Contenido del XML a validar
            tipo_comprobante: Tipo de comprobante

        Returns:
            Tupla (es_válido, lista_errores)
        """
        errores = []

        try:
            # Parsear el XML
            doc = etree.fromstring(xml_content.encode("utf-8"))

        except XMLSyntaxError as e:
            return False, [f"XML mal formado: {str(e)}"]

        except Exception as e:
            return False, [f"Error al parsear XML: {str(e)}"]

        # Obtener esquema para el tipo de comprobante
        schema = self._esquemas.get(str(tipo_comprobante))

        if schema is None:
            logger.warning(
                f"Esquema no disponible para {tipo_comprobante}, "
                "validando estructura básica"
            )
            return self._validar_estructura_basica(doc)

        # Validar contra esquema
        if schema.validate(doc):
            logger.info(f"XML válido contra esquema {tipo_comprobante}")
            return True, []

        else:
            # Extraer errores de validación
            for error in schema.error_log:
                errores.append(f"Línea {error.line}: {error.message}")

            logger.warning(f"XML inválido: {len(errores)} errores encontrados")
            return False, errores

    def _validar_estructura_basica(self, doc: etree._Element) -> Tuple[bool, List[str]]:
        """
        Validación básica cuando no hay esquema disponible

        Args:
            doc: Elemento raíz del XML parseado

        Returns:
            Tupla (es_válido, lista_errores)
        """
        errores = []

        # Verificar elemento raíz
        root_tag = doc.tag

        if root_tag not in [
            "factura",
            "notaCredito",
            "notaDebito",
            "guiaRemision",
            "comprobanteRetencion",
        ]:
            errores.append(f"Elemento raíz desconocido: {root_tag}")

        # Verificar presencia de infoTributaria
        info_tributaria = doc.find(".//infoTributaria")
        if info_tributaria is None:
            errores.append("Falta elemento infoTributaria")

        # Verificar campos requeridos en infoTributaria
        if info_tributaria is not None:
            campos_requeridos = [
                "ambiente",
                "tipoEmision",
                "razonSocial",
                "ruc",
                "claveAcceso",
                "codDoc",
                "estab",
                "ptoEmision",
                "secuencial",
            ]

            for campo in campos_requeridos:
                elem = info_tributaria.find(campo)
                if elem is None or not elem.text:
                    errores.append(f"Falta campo en infoTributaria: {campo}")

        # Verificar presencia de infoFactura (para facturas)
        if root_tag == "factura":
            info_factura = doc.find(".//infoFactura")
            if info_factura is None:
                errores.append("Falta elemento infoFactura")

        return len(errores) == 0, errores

    def validar_factura(self, xml_content: str) -> Tuple[bool, List[str]]:
        """
        Valida específicamente una factura

        Args:
            xml_content: Contenido XML de la factura

        Returns:
            Tupla (es_válido, lista_errores)
        """
        return self.validar_xml(xml_content, TipoComprobante.FACTURA)

    def obtener_errores_detallados(self, xml_content: str) -> Dict[str, Any]:
        """
        Obtiene errores detallados de validación

        Args:
            xml_content: Contenido XML

        Returns:
            Diccionario con información detallada de errores
        """
        resultado = {
            "es_valido": False,
            "errores": [],
            "advertencias": [],
            "tipo_comprobante": None,
            "info_tributaria": {},
        }

        try:
            doc = etree.fromstring(xml_content.encode("utf-8"))

            # Determinar tipo de comprobante
            root_tag = doc.tag
            resultado["tipo_comprobante"] = root_tag

            # Extraer infoTributaria
            info_tributaria = doc.find(".//infoTributaria")
            if info_tributaria is not None:
                for child in info_tributaria:
                    tag = child.tag.replace(
                        "{http://www.sri.gob.ec/comprobantes/valores}", ""
                    )
                    resultado["info_tributaria"][tag] = child.text

            # Validar
            es_valido, errores = self.validar_xml(xml_content)
            resultado["es_valido"] = es_valido
            resultado["errores"] = errores

        except Exception as e:
            resultado["errores"].append(str(e))

        return resultado


def validar_comprobante_sri(
    xml_content: str, tipo: str = "01"
) -> Tuple[bool, List[str]]:
    """
    Función de conveniencia para validar comprobantes

    Args:
        xml_content: Contenido XML
        tipo: Tipo de comprobante (01=factura, etc.)

    Returns:
        Tupla (es_válido, lista_errores)
    """
    validador = ValidadorXSD()

    tipo_enum = (
        TipoComprobante(tipo)
        if tipo in [e.value for e in TipoComprobante]
        else TipoComprobante.FACTURA
    )

    return validador.validar_xml(xml_content, tipo_enum)


def validar_factura_sri(xml_content: str) -> Tuple[bool, List[str]]:
    """
    Función de conveniencia para validar facturas

    Args:
        xml_content: Contenido XML de la factura

    Returns:
        Tupla (es_válido, lista_errores)
    """
    validador = ValidadorXSD()
    return validador.validar_factura(xml_content)


# Esquema XSD para factura (versiones básicas para cuando no hay archivos)
# Estos esquemas definen la estructura mínima válida

XSD_FACTURA_MINIMO = """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:tns="http://www.sri.gob.ec/comprobantes/factura/v1"
           elementFormDefault="qualified"
           targetNamespace="http://www.sri.gob.ec/comprobantes/factura/v1">
    
    <xs:element name="factura">
        <xs:complexType>
            <xs:sequence>
                <xs:element ref="tns:infoTributaria"/>
                <xs:element ref="tns:infoFactura"/>
                <xs:element ref="tns:detalles" minOccurs="0"/>
            </xs:sequence>
            <xs:attribute name="id" type="xs:string" fixed="comprobante"/>
            <xs:attribute name="version" type="xs:string" fixed="1.1.0"/>
        </xs:complexType>
    </xs:element>
    
    <xs:element name="infoTributaria">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="ambiente" type="xs:string"/>
                <xs:element name="tipoEmision" type="xs:string"/>
                <xs:element name="razonSocial" type="xs:string"/>
                <xs:element name="nombreComercial" type="xs:string" minOccurs="0"/>
                <xs:element name="ruc" type="xs:string"/>
                <xs:element name="claveAcceso" type="xs:string"/>
                <xs:element name="codDoc" type="xs:string"/>
                <xs:element name="estab" type="xs:string"/>
                <xs:element name="ptoEmision" type="xs:string"/>
                <xs:element name="secuencial" type="xs:string"/>
                <xs:element name="dirMatriz" type="xs:string"/>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
    
    <xs:element name="infoFactura">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="fechaEmision" type="xs:string"/>
                <xs:element name="dirEstablecimiento" type="xs:string" minOccurs="0"/>
                <xs:element name="tipoIdentificacionComprador" type="xs:string"/>
                <xs:element name="razonSocialComprador" type="xs:string"/>
                <xs:element name="identificacionComprador" type="xs:string"/>
                <xs:element name="direccionComprador" type="xs:string" minOccurs="0"/>
                <xs:element name="telefonoComprador" type="xs:string" minOccurs="0"/>
                <xs:element name="emailComprador" type="xs:string" minOccurs="0"/>
                <xs:element name="obligadoContabilidad" type="xs:string" minOccurs="0"/>
                <xs:element name="contribuyenteEspecial" type="xs:string" minOccurs="0"/>
                <xs:element name="tipoProveedor" type="xs:string" minOccurs="0"/>
                <xs:element name="totalSinImpuestos" type="xs:string"/>
                <xs:element name="totalDescuento" type="xs:string" minOccurs="0"/>
                <xs:element name="totalImpuesto" type="xs:string" minOccurs="0"/>
                <xs:element name="importeTotal" type="xs:string"/>
                <xs:element name="moneda" type="xs:string" minOccurs="0"/>
                <xs:element name="pagos" type="xs:string" minOccurs="0"/>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
    
    <xs:element name="detalles">
        <xs:complexType>
            <xs:sequence>
                <xs:element name="detalle" maxOccurs="unbounded">
                    <xs:complexType>
                        <xs:sequence>
                            <xs:element name="codigoPrincipal" type="xs:string"/>
                            <xs:element name="descripcion" type="xs:string"/>
                            <xs:element name="cantidad" type="xs:string"/>
                            <xs:element name="precioUnitario" type="xs:string"/>
                            <xs:element name="descuento" type="xs:string" minOccurs="0"/>
                            <xs:element name="precioTotalSinImpuesto" type="xs:string"/>
                        </xs:sequence>
                    </xs:complexType>
                </xs:element>
            </xs:sequence>
        </xs:complexType>
    </xs:element>
</xs:schema>
"""
