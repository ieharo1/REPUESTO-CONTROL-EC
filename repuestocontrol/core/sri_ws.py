"""
Módulo de Conexión SOAP con Web Services del SRI Ecuador

Este módulo implementa la conexión real con los servicios web del SRI para:
- Recepción de comprobantes electrónicos
- Autorización de comprobantes

Ambientes disponibles:
- Pruebas: https://celcer.sri.gob.ec/comprobanteselectronicosws/services
- Producción: https://cel.sri.gob.ec/comprobanteselectronicosws/services

Servicios SOAP:
- RecepcionComprobantes: Para enviar comprobantes
- AutorizacionComprobantes: Para consultar estado de autorización
"""

import logging
import socket
import time
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from enum import Enum

from lxml import etree
from lxml.etree import tostring
import requests
from zeep import Client, Transport, exceptions as zeep_exceptions
from zeep.transports import Transport
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class AmbienteSRI(str, Enum):
    """Ambientes disponibles del SRI"""

    PRUEBAS = "1"
    PRODUCCION = "2"


class EstadoComprobante(str, Enum):
    """Estados posibles de un comprobante electrónico"""

    RECIBIDA = "RECIBIDA"
    DEVUELTA = "DEVUELTA"
    AUTORIZADA = "AUTORIZADA"
    NO_AUTORIZADA = "NO AUTORIZADA"
    RECEPTA = "RECEPTA"


class ErrorSRI(Exception):
    """Excepción base para errores del SRI"""

    pass


class ErrorConexionSRI(ErrorSRI):
    """Error de conexión con el SRI"""

    pass


class ErrorTimeoutSRI(ErrorSRI):
    """Timeout al comunicarse con el SRI"""

    pass


class ErrorValidacionSRI(ErrorSRI):
    """Error de validación del comprobante"""

    pass


class ErrorAutorizacionSRI(ErrorSRI):
    """Error en la autorización del comprobante"""

    pass


class ErrorRecepcionSRI(ErrorSRI):
    """Error en la recepción del comprobante"""

    pass


class SRIWebService:
    """
    Cliente SOAP para conectar con los servicios del SRI

    Attributes:
        ambiente: Ambiente de trabajo ('1' pruebas, '2' producción)
        timeout: Timeout para conexiones en segundos
        reintentos: Número de reintentos automáticos
    """

    # URLs de los servicios web
    WSDL_RECEPCION_PRUEBAS = "https://celcer.sri.gob.ec/comprobanteselectronicosws/services/RecepcionComprobantes?wsdl"
    WSDL_AUTORIZACION_PRUEBAS = "https://celcer.sri.gob.ec/comprobanteselectronicosws/services/AutorizacionComprobantes?wsdl"

    WSDL_RECEPCION_PRODUCCION = "https://cel.sri.gob.ec/comprobanteselectronicosws/services/RecepcionComprobantes?wsdl"
    WSDL_AUTORIZACION_PRODUCCION = "https://cel.sri.gob.ec/comprobanteselectronicosws/services/AutorizacionComprobantes?wsdl"

    # Tiempos de espera
    DEFAULT_TIMEOUT = 60
    MAX_REINTENTOS = 3
    RETRY_DELAY = 2

    def __init__(
        self,
        ambiente: str = "1",
        timeout: int = DEFAULT_TIMEOUT,
        reintentos: int = MAX_REINTENTOS,
    ):
        """
        Inicializa el cliente SOAP del SRI

        Args:
            ambiente: Ambiente de trabajo ('1' pruebas, '2' producción)
            timeout: Timeout en segundos para cada solicitud
            reintentos: Número de reintentos automáticos en caso de error
        """
        self.ambiente = ambiente
        self.timeout = timeout
        self.reintentos = reintentos

        # Inicializar clientes SOAP
        self._cliente_recepcion = None
        self._cliente_autorizacion = None

        self._inicializar_clientes()

    def _inicializar_clientes(self) -> None:
        """Inicializa los clientes SOAP"""
        try:
            # Configurar sesión con reintentos
            session = requests.Session()
            retry_strategy = Retry(
                total=self.reintentos,
                backoff_factor=1,
                status_forcelist=[500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("https://", adapter)
            session.mount("http://", adapter)

            transport = Transport(session=session, timeout=self.timeout)

            # Seleccionar URLs según ambiente
            if self.ambiente == AmbienteSRI.PRUEBAS:
                wsdl_recepcion = self.WSDL_RECEPCION_PRUEBAS
                wsdl_autorizacion = self.WSDL_AUTORIZACION_PRUEBAS
            else:
                wsdl_recepcion = self.WSDL_RECEPCION_PRODUCCION
                wsdl_autorizacion = self.WSDL_AUTORIZACION_PRODUCCION

            logger.info(f"Inicializando cliente SRI - Ambiente: {self.ambiente}")
            logger.debug(f"WSDL Recepción: {wsdl_recepcion}")
            logger.debug(f"WSDL Autorización: {wsdl_autorizacion}")

            # Crear clientes SOAP
            self._cliente_recepcion = Client(wsdl_recepcion, transport=transport)
            self._cliente_autorizacion = Client(wsdl_autorizacion, transport=transport)

            logger.info("Clientes SOAP inicializados correctamente")

        except Exception as e:
            logger.error(f"Error al inicializar clientes SOAP: {str(e)}")
            raise ErrorConexionSRI(f"No se pudo inicializar conexión con SRI: {str(e)}")

    def _reintentar(self, func, *args, **kwargs):
        """
        Ejecuta una función con reintentos automáticos

        Args:
            func: Función a ejecutar
            *args, **kwargs: Argumentos de la función

        Returns:
            Resultado de la función

        Raises:
            ErrorTimeoutSRI: Si hay timeout
            ErrorConexionSRI: Si hay error de conexión después de reintentos
        """
        ultimo_error = None

        for intento in range(self.reintentos):
            try:
                return func(*args, **kwargs)
            except socket.timeout as e:
                ultimo_error = e
                logger.warning(f"Timeout en intento {intento + 1}/{self.reintentos}")
                if intento < self.reintentos - 1:
                    time.sleep(self.RETRY_DELAY * (intento + 1))
            except requests.exceptions.Timeout as e:
                ultimo_error = e
                logger.warning(f"Timeout en intento {intento + 1}/{self.reintentos}")
                if intento < self.reintentos - 1:
                    time.sleep(self.RETRY_DELAY * (intento + 1))
            except requests.exceptions.ConnectionError as e:
                ultimo_error = e
                logger.warning(
                    f"Error de conexión en intento {intento + 1}/{self.reintentos}"
                )
                if intento < self.reintentos - 1:
                    time.sleep(self.RETRY_DELAY * (intento + 1))

        if isinstance(ultimo_error, socket.timeout):
            raise ErrorTimeoutSRI(
                f"Timeout después de {self.reintentos} intentos: {str(ultimo_error)}"
            )
        raise ErrorConexionSRI(
            f"Error de conexión después de {self.reintentos} intentos: {str(ultimo_error)}"
        )

    def enviar_comprobante(self, xml_content: str) -> Dict[str, Any]:
        """
        Envía un comprobante electrónico al SRI para recepción

        Args:
            xml_content: Contenido del XML del comprobante

        Returns:
            Diccionario con el resultado de la recepción:
            {
                'estado': 'RECIBIDA' | 'DEVUELTA',
                'mensajes': [...],
                'comprobante': '...'
            }

        Raises:
            ErrorRecepcionSRI: Si hay error en la recepción
        """
        logger.info("Enviando comprobante al SRI...")
        logger.debug(f"Tamaño XML: {len(xml_content)} bytes")

        try:

            def _enviar():
                return self._cliente_recepcion.service.validarComprobante(
                    xml=xml_content
                )

            respuesta = self._reintentar(_enviar)

            # Parsear respuesta
            resultado = self._parsear_respuesta_recepcion(respuesta)

            logger.info(
                f"Respuesta recepción: {resultado.get('estado', 'DESCONOCIDO')}"
            )

            return resultado

        except ErrorTimeoutSRI:
            raise
        except ErrorConexionSRI:
            raise
        except Exception as e:
            logger.error(f"Error al enviar comprobante: {str(e)}")
            raise ErrorRecepcionSRI(f"Error al enviar comprobante: {str(e)}")

    def _parsear_respuesta_recepcion(self, respuesta) -> Dict[str, Any]:
        """
        Parsea la respuesta del servicio de recepción

        Args:
            respuesta: Respuesta SOAP cruda

        Returns:
            Diccionario con datos parseados
        """
        resultado = {"estado": "DESCONOCIDO", "mensajes": [], "comprobante": ""}

        try:
            # La respuesta puede variar según el tipo
            # Generalmente contiene: estado, mensajes, comprobante

            if hasattr(respuesta, "estado"):
                resultado["estado"] = str(respuesta.estado)

            if hasattr(respuesta, "comprobantes"):
                # Procesar comprobantes
                pass

            # Procesar mensajes de error o advertencias
            if hasattr(respuesta, "mensajes") or hasattr(respuesta, "mensaje"):
                mensajes_raw = getattr(respuesta, "mensajes", None) or getattr(
                    respuesta, "mensaje", None
                )
                if mensajes_raw:
                    for msg in mensajes_raw:
                        resultado["mensajes"].append(
                            {
                                "tipo": getattr(msg, "tipo", ""),
                                "mensaje": getattr(msg, "mensaje", ""),
                                "informacion": getattr(msg, "informacionAdicional", ""),
                            }
                        )

            # Determinar estado
            estado_str = str(resultado["estado"]).upper()
            if "RECIBIDA" in estado_str:
                resultado["estado"] = EstadoComprobante.RECIBIDA
            elif "DEVUELTA" in estado_str:
                resultado["estado"] = EstadoComprobante.DEVUELTA

        except Exception as e:
            logger.warning(f"Error al parsear respuesta: {str(e)}")

        return resultado

    def autorizacion_comprobante(self, clave_acceso: str) -> Dict[str, Any]:
        """
        Consulta la autorización de un comprobante por clave de acceso

        Args:
            clave_acceso: Clave de acceso del comprobante (49 dígitos)

        Returns:
            Diccionario con resultado de autorización:
            {
                'estado': 'AUTORIZADA' | 'NO AUTORIZADA' | 'EN PROCESO',
                'numero_autorizacion': '...',
                'fecha_autorizacion': '...',
                'mensajes': [...],
                'xml': '...'
            }

        Raises:
            ErrorAutorizacionSRI: Si hay error en la autorización
        """
        logger.info(f"Consultando autorización para: {clave_acceso}")

        try:

            def _autorizar():
                return self._cliente_autorizacion.service.autorizacionComprobante(
                    claveAcceso=clave_acceso
                )

            respuesta = self._reintentar(_autorizar)

            resultado = self._parsear_respuesta_autorizacion(respuesta, clave_acceso)

            logger.info(
                f"Estado autorización: {resultado.get('estado', 'DESCONOCIDO')}"
            )

            return resultado

        except ErrorTimeoutSRI:
            raise
        except ErrorConexionSRI:
            raise
        except Exception as e:
            logger.error(f"Error al consultar autorización: {str(e)}")
            raise ErrorAutorizacionSRI(f"Error al consultar autorización: {str(e)}")

    def autorizacion_comprobante_lote(self, claves_acceso: list[str]) -> Dict[str, Any]:
        """
        Consulta la autorización de múltiples comprobantes

        Args:
            claves_acceso: Lista de claves de acceso

        Returns:
            Diccionario con autorizaciones
        """
        logger.info(
            f"Consultando autorización en lote: {len(claves_acceso)} comprobantes"
        )

        try:

            def _autorizar_lote():
                return self._cliente_autorizacion.service.autorizacionComprobanteLote(
                    claveAccesoComprobantes=claves_acceso
                )

            respuesta = self._reintentar(_autorizar_lote)

            # Parsear respuesta de lote
            resultado = self._parsear_respuesta_autorizacion_lote(respuesta)

            return resultado

        except Exception as e:
            logger.error(f"Error en autorización por lote: {str(e)}")
            raise ErrorAutorizacionSRI(f"Error en autorización por lote: {str(e)}")

    def _parsear_respuesta_autorizacion(
        self, respuesta, clave_acceso: str
    ) -> Dict[str, Any]:
        """
        Parsea la respuesta del servicio de autorización

        Args:
            respuesta: Respuesta SOAP cruda
            clave_acceso: Clave de acceso consultada

        Returns:
            Diccionario con datos parseados
        """
        resultado = {
            "estado": "EN PROCESO",
            "numero_autorizacion": "",
            "fecha_autorizacion": "",
            "mensajes": [],
            "xml": "",
            "clave_acceso": clave_acceso,
        }

        try:
            # La respuesta puede tener diferentes estructuras
            # Dependiendo de si hay auth-response o no

            autorizacion = None

            if hasattr(respuesta, "autorizacionComprobante"):
                autorizacion = respuesta.autorizacionComprobante
            elif hasattr(respuesta, "autorizaciones"):
                autorizaciones = respuesta.autorizaciones
                if autorizaciones and len(autorizaciones) > 0:
                    autorizacion = autorizaciones[0]

            if autorizacion:
                # Extraer datos de autorización
                if hasattr(autorizacion, "estado"):
                    estado = str(autorizacion.estado).upper()
                    if "AUTORIZ" in estado:
                        resultado["estado"] = EstadoComprobante.AUTORIZADA
                    elif "NO AUTORIZ" in estado:
                        resultado["estado"] = EstadoComprobante.NO_AUTORIZADA
                    else:
                        resultado["estado"] = estado

                if hasattr(autorizacion, "numeroAutorizacion"):
                    resultado["numero_autorizacion"] = str(
                        autorizacion.numeroAutorizacion
                    )

                if hasattr(autorizacion, "fechaAutorizacion"):
                    resultado["fecha_autorizacion"] = str(
                        autorizacion.fechaAutorizacion
                    )

                if hasattr(autorizacion, "comprobante"):
                    resultado["xml"] = str(autorizacion.comprobante)

                # Mensajes
                if hasattr(autorizacion, "mensajes"):
                    for msg in autorizacion.mensajes:
                        resultado["mensajes"].append(
                            {
                                "tipo": getattr(msg, "tipo", ""),
                                "identificador": getattr(msg, "identificador", ""),
                                "mensaje": getattr(msg, "mensaje", ""),
                                "informacion": getattr(msg, "informacionAdicional", ""),
                            }
                        )

        except Exception as e:
            logger.warning(f"Error al parsear autorización: {str(e)}")

        return resultado

    def _parsear_respuesta_autorizacion_lote(self, respuesta) -> Dict[str, Any]:
        """Parsea respuesta de autorización por lote"""
        resultado = {"autorizaciones": [], "fecha_consula": datetime.now().isoformat()}

        try:
            if hasattr(respuesta, "autorizaciones"):
                for auth in respuesta.autorizaciones:
                    resultado["autorizaciones"].append(
                        {
                            "clave_acc": getattr(auth, "claveAccesoComprobante", ""),
                            "estado": getattr(auth, "estado", ""),
                        }
                    )
        except Exception as e:
            logger.warning(f"Error al parsear autorización lote: {str(e)}")

        return resultado

    def obtener_estado_comprobante(self, clave_acceso: str) -> Tuple[str, str]:
        """
        Obtiene el estado simplificado de un comprobante

        Args:
            clave_acceso: Clave de acceso

        Returns:
            Tupla (estado, mensaje)
        """
        try:
            resultado = self.autorizacion_comprobante(clave_acceso)
            return resultado.get("estado", "DESCONOCIDO"), ""
        except ErrorSRI as e:
            return "ERROR", str(e)


def crear_cliente_sri(
    ambiente: str = "1", timeout: int = 60, reintentos: int = 3
) -> SRIWebService:
    """
    Factory function para crear cliente SRI

    Args:
        ambiente: Ambiente de trabajo
        timeout: Timeout en segundos
        reintentos: Número de reintentos

    Returns:
        Instancia de SRIWebService
    """
    return SRIWebService(ambiente, timeout, reintentos)


def procesar_comprobante(
    xml_content: str, clave_acceso: str, ambiente: str = "1", timeout: int = 60
) -> Dict[str, Any]:
    """
    Procesa un comprobante electrónico completo:
    1. Envía a recepción
    2. Consulta autorización

    Args:
        xml_content: Contenido XML del comprobante
        clave_acceso: Clave de acceso
        ambiente: Ambiente de trabajo
        timeout: Timeout en segundos

    Returns:
        Diccionario con resultado completo
    """
    logger.info("=" * 50)
    logger.info("INICIANDO PROCESAMIENTO DE COMPROBANTE")
    logger.info(f"Clave acceso: {clave_acceso}")
    logger.info(f"Ambiente: {'PRUEBAS' if ambiente == '1' else 'PRODUCCIÓN'}")
    logger.info("=" * 50)

    sri = crear_cliente_sri(ambiente, timeout)

    resultado = {
        "clave_acceso": clave_acceso,
        "recepcion": None,
        "autorizacion": None,
        "estado_final": "PENDIENTE",
        "errores": [],
    }

    try:
        # Paso 1: Enviar a recepción
        logger.info("[1/2] Enviando comprobante a recepción...")
        recepcion = sri.enviar_comprobante(xml_content)
        resultado["recepcion"] = recepcion

        if recepcion.get("estado") == EstadoComprobante.DEVUELTA:
            resultado["estado_final"] = "DEVUELTO"
            resultado["errores"].append("Comprobante devuelto")
            logger.warning("Comprobante DEVUELTO")
            return resultado

        # Paso 2: Consultar autorización
        logger.info("[2/2] Consultando autorización...")
        autorizacion = sri.autorizacion_comprobante(clave_acceso)
        resultado["autorizacion"] = autorizacion

        resultado["estado_final"] = autorizacion.get("estado", "DESCONOCIDO")

        logger.info(f"Estado final: {resultado['estado_final']}")

    except ErrorSRI as e:
        logger.error(f"Error del SRI: {str(e)}")
        resultado["errores"].append(str(e))
        resultado["estado_final"] = "ERROR"

    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        resultado["errores"].append(str(e))
        resultado["estado_final"] = "ERROR"

    logger.info("=" * 50)
    logger.info("FINALIZANDO PROCESAMIENTO")
    logger.info(f"Estado: {resultado['estado_final']}")
    logger.info("=" * 50)

    return resultado
