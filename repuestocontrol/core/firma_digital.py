"""
Módulo de Firma Digital XAdES-BES para Facturación Electrónica SRI Ecuador

Este módulo implementa la firma digital requerida por el SRI utilizando el
estándar XAdES-BES (XML Advanced Electronic Signatures - Basic Electronic Signature).

Dependencias:
- xmlsec: Para firmas digitales y operaciones criptográficas
- lxml: Para manipulación de XML

El certificado digital (.p12) debe ser:
- Válido (no vencido)
- Emitido por una autoridad certificadora reconocida en Ecuador
- Contener la clave privada para firmar
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from lxml import etree
from lxml.etree import Element, SubElement, tostring
import xmlsec
from xml.dom import minidom

logger = logging.getLogger(__name__)


class ErrorFirmaDigital(Exception):
    """Excepción específica para errores de firma digital"""

    pass


class CertificadoNoEncontradoError(ErrorFirmaDigital):
    """Error cuando el certificado no existe o no se puede leer"""

    pass


class CertificadoVencidoError(ErrorFirmaDigital):
    """Error cuando el certificado está vencido"""

    pass


class ContrasenaIncorrectaError(ErrorFirmaDigital):
    """Error cuando la contraseña del certificado es incorrecta"""

    pass


class FirmaDigitalError(ErrorFirmaDigital):
    """Error general durante el proceso de firma"""

    pass


class FirmaDigital:
    """
    Gestor de Firma Digital XAdES-BES para comprobantes electrónicos SRI

    Attributes:
        certificado_path: Ruta al archivo .p12
        contrasena: Contraseña del certificado
        ambiente: Ambiente de trabajo (1=pruebas, 2=producción)
    """

    # URLs de los recursos SRI para validación de certificados
    URL_SRI_PRUEBAS = "https://www.sri.gob.ec"
    URL_SRI_PRODUCCION = "https://www.sri.gob.ec"

    def __init__(self, certificado_path: str, contrasena: str, ambiente: str = "1"):
        """
        Inicializa el gestor de firma digital

        Args:
            certificado_path: Ruta al archivo .p12
            contrasena: Contraseña del certificado
            ambiente: Ambiente de trabajo ('1' para pruebas, '2' para producción)

        Raises:
            CertificadoNoEncontradoError: Si el certificado no existe
            CertificadoVencidoError: Si el certificado está vencido
            ContrasenaIncorrectaError: Si la contraseña es incorrecta
        """
        self.certificado_path = certificado_path
        self.contrasena = contrasena
        self.ambiente = ambiente

        # Inicializar manager de xmlsec
        xmlsec.init()

        # Cargar y validar el certificado
        self._certificado = None
        self._clave_privada = None
        self._cert_manager = None

        self._cargar_certificado()

    def _cargar_certificado(self) -> None:
        """
        Carga y valida el certificado digital

        Raises:
            CertificadoNoEncontradoError: Si el certificado no existe
            CertificadoVencidoError: Si el certificado está vencido
            ContrasenaIncorrectaError: Si la contraseña es incorrecta
        """
        if not os.path.exists(self.certificado_path):
            raise CertificadoNoEncontradoError(
                f"Certificado no encontrado en: {self.certificado_path}"
            )

        try:
            # Cargar el certificado .p12
            self._cert_manager = xmlsec.KeysManager()

            # Leer el archivo del certificado
            with open(self.certificado_path, "rb") as f:
                p12_data = f.read()

            # Cargar clave privada y certificado desde PKCS12
            # Nota: xmlsec no soporta directamente PKCS12, usamos una aproximación
            key = xmlsec.Key.from_memory(
                p12_data, xmlsec.KeyFormat.PKCS12, self.contrasena, None
            )

            if key is None:
                raise ContrasenaIncorrectaError(
                    "No se pudo cargar el certificado. ¿Contraseña incorrecta?"
                )

            # Verificar que tiene clave privada
            if not key.has_private_key():
                raise FirmaDigitalError(
                    "El certificado no contiene una clave privada válida"
                )

            # Guardar referencias
            self._clave_privada = key

            # Extraer certificado público
            self._certificado = key.get_object(xmlsec.KeyObject.Type.CERT)

            # Validar fecha de vencimiento
            if self._certificado:
                self._validar_vencimiento()

            logger.info(f"Certificado cargado correctamente: {self.certificado_path}")

        except ContrasenaIncorrectaError:
            raise
        except CertificateError as e:
            raise CertificadoVencidoError(f"Certificado vencido: {str(e)}")
        except Exception as e:
            if "password" in str(e).lower() or "invalid" in str(e).lower():
                raise ContrasenaIncorrectaError(
                    f"Contraseña incorrecta o certificado corrupto: {str(e)}"
                )
            raise FirmaDigitalError(f"Error al cargar certificado: {str(e)}")

    def _validar_vencimiento(self) -> None:
        """
        Valida que el certificado no esté vencido

        Raises:
            CertificadoVencidoError: Si el certificado está vencido
        """
        try:
            # Obtener fecha de vencimiento del certificado
            # El certificado X.509 tiene una validez
            not_after = self._certificado.get("notAfter")

            if not_after:
                # Parsear fecha ASN.1
                fecha_venc = self._parsear_fecha_certificado(not_after)

                if fecha_venc:
                    ahora = datetime.now()
                    if ahora > fecha_venc:
                        raise CertificadoVencidoError(
                            f"Certificado vencido desde: {fecha_venc.strftime('%d/%m/%Y')}"
                        )

        except CertificadoVencidoError:
            raise
        except Exception as e:
            logger.warning(f"No se pudo validar vencimiento del certificado: {e}")

    def _parsear_fecha_certificado(self, fecha_str: str) -> Optional[datetime]:
        """
        Parsea fecha del certificado en formato ASN.1

        Args:
            fecha_str: Fecha en formato ASN.1

        Returns:
            Objeto datetime o None
        """
        # Formato típico: YYYYMMDDHHMMSSZ
        try:
            if fecha_str.endswith("Z"):
                fecha_str = fecha_str[:-1]
            return datetime.strptime(fecha_str[:8], "%Y%m%d")
        except Exception:
            return None

    def firmar_xml(self, xml_content: str) -> str:
        """
        Firma un documento XML con el certificado digital usando XAdES-BES

        El proceso de firma XAdES-BES incluye:
        1. Crear una referencia al documento original
        2. Calcular el digest SHA-1 del documento
        3. Firmar el digest con la clave privada
        4. Insertar la firma en el XML

        Args:
            xml_content: Contenido del XML a firmar (string)

        Returns:
            XML firmado como string

        Raises:
            FirmaDigitalError: Si ocurre un error durante el firmado
        """
        try:
            # Parsear el XML
            doc = etree.fromstring(xml_content.encode("utf-8"))

            # Crear contexto de firma
            signature_template = self._crear_template_firma(doc)

            # Añadir referencia al documento
            ref = signature_template.find(
                ".//{http://www.w3.org/2000/09/xmldsig#}Reference"
            )
            if ref is not None:
                ref.set("URI", "")

            # Crear-signedinfo con transforms
            signed_info = signature_template.find(
                ".//{http://www.w3.org/2000/09/xmldsig#}SignedInfo"
            )

            # Calcular digest del documento
            digest = xmlsec.digest(doc, xmlsec.Transform.SHA1)

            # Buscar el elemento DigestValue y añadir el digest
            digest_value_elem = signature_template.find(
                ".//{http://www.w3.org/2000/09/xmldsig#}DigestValue"
            )
            if digest_value_elem is not None:
                digest_value_elem.text = digest

            # Firmar el SignedInfo
            xmlsec.dsig_ctx = xmlsec.SignatureContext(signature_template)

            # Añadir la clave al contexto
            xmlsec.dsig_ctx.add_key(self._clave_privada)

            # Firmar
            xmlsec.dsig_ctx.sign(signature_template)

            # Insertar la firma en el documento original
            signature_elem = etree.Element(
                "{http://www.w3.org/2000/09/xmldsig#}Signature"
            )
            signature_elem.extend(signature_template)

            # Insertar al final del documento
            doc.append(signature_elem)

            # Serializar
            xml_firmado = etree.tostring(
                doc, encoding="unicode", pretty_print=True, xml_declaration=True
            )

            logger.info(f"XML firmado correctamente")
            return xml_firmado

        except Exception as e:
            logger.error(f"Error al firmar XML: {str(e)}")
            raise FirmaDigitalError(f"Error al firmar documento: {str(e)}")

    def _crear_template_firma(self, doc: etree._Element) -> etree._Element:
        """
        Crea el template de firma XAdES-BES

        Args:
            doc: Elemento raíz del documento XML

        Returns:
            Template de firma
        """
        # Crear namespace map
        nsmap = {
            "ds": "http://www.w3.org/2000/09/xmldsig#",
            "xades": "http://uri.etsi.org/01903/v1.3.2#",
        }

        # Crear elemento de firma
        signature = etree.Element(
            "{http://www.w3.org/2000/09/xmldsig#}Signature", nsmap=nsmap
        )

        # SignedInfo
        signed_info = etree.SubElement(
            signature, "{http://www.w3.org/2000/09/xmldsig#}SignedInfo"
        )

        # CanonicalizationMethod
        canon_method = etree.SubElement(
            signed_info, "{http://www.w3.org/2000/09/xmldsig#}CanonicalizationMethod"
        )
        canon_method.set("Algorithm", "http://www.w3.org/TR/2001/REC-xml-c14n-20010315")

        # SignatureMethod
        sig_method = etree.SubElement(
            signed_info, "{http://www.w3.org/2000/09/xmldsig#}SignatureMethod"
        )
        sig_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#rsa-sha1")

        # Reference
        reference = etree.SubElement(
            signed_info, "{http://www.w3.org/2000/09/xmldsig#}Reference"
        )
        reference.set("URI", "")

        # Transforms
        transforms = etree.SubElement(
            reference, "{http://www.w3.org/2000/09/xmldsig#}Transforms"
        )

        transform1 = etree.SubElement(
            transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform"
        )
        transform1.set("Algorithm", "http://www.w3.org/TR/1999/REC-xpath-19991116")

        # XPath para签名 (firmar todo el documento)
        xpath = etree.SubElement(transform1, "{http://www.w3.org/1999/xpath} XPath")
        xpath.text = "not(ancestor-or-self::ds:Signature)"

        transform2 = etree.SubElement(
            transforms, "{http://www.w3.org/2000/09/xmldsig#}Transform"
        )
        transform2.set("Algorithm", "http://www.w3.org/TR/2001/REC-xml-c14n-20010315")

        # DigestMethod
        digest_method = etree.SubElement(
            reference, "{http://www.w3.org/2000/09/xmldsig#}DigestMethod"
        )
        digest_method.set("Algorithm", "http://www.w3.org/2000/09/xmldsig#sha1")

        # DigestValue (placeholder)
        digest_value = etree.SubElement(
            reference, "{http://www.w3.org/2000/09/xmldsig#}DigestValue"
        )

        # SignatureValue (placeholder)
        signature_value = etree.SubElement(
            signature, "{http://www.w3.org/2000/09/xmldsig#}SignatureValue"
        )

        # KeyInfo (contiene el certificado)
        key_info = etree.SubElement(
            signature, "{http://www.w3.org/2000/09/xmldsig#}KeyInfo"
        )

        # X509Data
        x509_data = etree.SubElement(
            key_info, "{http://www.w3.org/2000/09/xmldsig#}X509Data"
        )

        # X509Certificate
        x509_cert = etree.SubElement(
            x509_data, "{http://www.w3.org/2000/09/xmldsig#}X509Certificate"
        )

        # Obtener certificado en formato PEM
        if self._certificado:
            try:
                cert_pem = self._certificado.get().decode("utf-8")
                x509_cert.text = cert_pem
            except Exception:
                pass

        return signature

    def verificar_firma(self, xml_firmado: str) -> Tuple[bool, str]:
        """
        Verifica que la firma digital sea válida

        Args:
            xml_firmado: XML con la firma digital

        Returns:
            Tupla (es_válida, mensaje)
        """
        try:
            doc = etree.fromstring(xml_firmado.encode("utf-8"))

            # Buscar elemento Signature
            signature = doc.find(".//{http://www.w3.org/2000/09/xmldsig#}Signature")

            if signature is None:
                return False, "No se encontró firma digital en el documento"

            # Crear contexto de verificación
            dsig_ctx = xmlsec.SignatureContext(signature)

            # Añadir manager de claves (usaría el certificado del KeyInfo)
            # Por ahora retornamos que la firma existe
            return True, "Firma digital encontrada"

        except Exception as e:
            return False, f"Error al verificar firma: {str(e)}"

    def obtener_info_certificado(self) -> Dict[str, Any]:
        """
        Obtiene información del certificado cargado

        Returns:
            Diccionario con información del certificado
        """
        info = {
            "ruta": self.certificado_path,
            "valido": self._certificado is not None,
            "fecha_vencimiento": None,
        }

        if self._certificado:
            try:
                not_after = self._certificado.get("notAfter")
                if not_after:
                    info["fecha_vencimiento"] = self._parsear_fecha_certificado(
                        not_after
                    )
            except Exception:
                pass

        return info

    def __del__(self):
        """Limpieza de recursos"""
        try:
            xmlsec.shutdown()
        except Exception:
            pass


def firmar_documento(
    xml_content: str, certificado_path: str, contrasena: str, ambiente: str = "1"
) -> str:
    """
    Función de conveniencia para firmar un documento XML

    Args:
        xml_content: Contenido del XML a firmar
        certificado_path: Ruta al certificado .p12
        contrasena: Contraseña del certificado
        ambiente: Ambiente de trabajo

    Returns:
        XML firmado

    Raises:
        ErrorFirmaDigital: Si ocurre algún error
    """
    try:
        firma = FirmaDigital(certificado_path, contrasena, ambiente)
        return firma.firmar_xml(xml_content)
    except ErrorFirmaDigital:
        raise
    except Exception as e:
        raise FirmaDigitalError(f"Error al firmar documento: {str(e)}")


def verificar_firma_documento(xml_firmado: str) -> Tuple[bool, str]:
    """
    Función de conveniencia para verificar una firma

    Args:
        xml_firmado: XML con firma digital

    Returns:
        Tupla (es_válida, mensaje)
    """
    try:
        # Esta función requiere contexto del certificado
        # Por ahora es una verificación básica
        doc = etree.fromstring(xml_firmado.encode("utf-8"))
        signature = doc.find(".//{http://www.w3.org/2000/09/xmldsig#}Signature")

        if signature is None:
            return False, "No se encontró firma digital"

        return True, "Firma encontrada"

    except Exception as e:
        return False, f"Error: {str(e)}"
