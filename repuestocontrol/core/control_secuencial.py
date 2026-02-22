"""
Módulo de Control Secuencial para Facturación Electrónica

Este módulo implementa el control secuencial robusto para la numeración
de comprobantes electrónicos, considerando:
- Incremento automático
- Bloqueo contra duplicidad
- Soporte multi-establecimiento
- Transacciones atómicas
- Protección ante concurrencia
"""

import logging
from decimal import Decimal
from typing import Optional, Tuple
from django.db import transaction
from django.db.models import F
from django.core.cache import cache

logger = logging.getLogger(__name__)


class ErrorSecuencial(Exception):
    """Excepción para errores de secuencial"""
    pass


class SecuencialYaExisteError(ErrorSecuencial):
    """Error cuando el secuencial ya existe"""
    pass


class SecuencialNoValidoError(ErrorSecuencial):
    """Error cuando el secuencial no es válido"""
    pass


class GestorSecuencial:
    """
    Gestor de secuenciales para comprobantes electrónicos
    
    Implementa control de concurrencia usando:
    - Transacciones atómicas
    - Select for update
    - Cacheo de secuenciales
    """
    
    # Configuración
    MAX_SECUENCIAL = 999999999
    MIN_SECUENCIAL = 1
    CACHE_TIMEOUT = 300  # 5 minutos
    
    def __init__(self):
        self._cache_key_prefix = "sri_secuencial_"
    
    def obtener_sigiente_secuencial(
        self,
        configuracion,
        tipo_comprobante: str = "01"
    ) -> int:
        """
        Obtiene el siguiente secuencial de forma segura
        
        Args:
            configuracion: Instancia de Configuracion
            tipo_comprobante: Tipo de comprobante (01=factura, etc.)
            
        Returns:
            siguiente número secuencial
            
        Raises:
            ErrorSecuencial: Si hay error al obtener secuencial
        """
        key = self._get_cache_key(configuracion.id, tipo_comu probante)
        
        # Intentar obtener de cache
        secuencial = cache.get(key)
        if secuencial:
            logger.debug(f"Secuencial obtenido de cache: {secuencial}")
            return secuencial
        
        # Obtener de base de datos con bloqueo
        try:
            with transaction.atomic():
                # Bloquear el registro
                config = type(configuracion).objects.select_for_update().get(
                    pk=configuracion.id
                )
                
                # Determinar campo de secuencial
                campo_secuencial = self._get_campo_secuencial(tipo_comprobante)
                
                # Obtener valor actual
                secuencial_actual = getattr(config, campo_secuencial, 1) or 1
                
                # Validar rango
                if secuencial_actual > self.MAX_SECUENCIAL:
                    raise ErrorSecuencial(
                        f"Secuencial máximo alcanzado: {self.MAX_SECUENCIAL}"
                    )
                
                # Incrementar
                nuevo_secuencial = secuencial_actual + 1
                
                # Guardar
                setattr(config, campo_secuencial, nuevo_secuencial)
                config.save(update_fields=[campo_secuencial])
                
                # Guardar en cache
                cache.set(key, nuevo_secuencial, self.CACHE_TIMEOUT)
                
                logger.info(
                    f"Nuevo secuencial: {nuevo_secuencial} "
                    f"(tipo: {tipo_comprobante})"
                )
                
                return nuevo_secuencial
                
        except ErrorSecuencial:
            raise
        except Exception as e:
            logger.error(f"Error al obtener secuencial: {str(e)}")
            raise ErrorSecuencial(f"Error al obtener secuencial: {str(e)}")
    
    def obtener_secuencial_actual(
        self,
        configuracion,
        tipo_comprobante: str = "01"
    ) -> int:
        """
        Obtiene el secuencial actual sin incrementar
        
        Args:
            configuracion: Instancia de Configuracion
            tipo_comprobante: Tipo de comprobante
            
        Returns:
            Secuencial actual
        """
        campo = self._get_campo_secuencial(tipo_comprobante)
        return getattr(configuracion, campo, 1) or 1
    
    def validar_secuencial(
        self,
        secuencial: int,
        establecimiento: str,
        punto_emision: str
    ) -> Tuple[bool, str]:
        """
        Valida que un secuencial sea válido
        
        Args:
            secuencial: Número secuencial
            establecimiento: Código de establecimiento
            punto_emision: Código de punto de emisión
            
        Returns:
            Tupla (es_válido, mensaje)
        """
        # Validar formato
        if not secuencial or secuencial < self.MIN_SECUENCIAL:
            return False, f"Secuencial mínimo: {self.MIN_SECUENCIAL}"
        
        if secuencial > self.MAX_SECUENCIAL:
            return False, f"Secuencial máximo: {self.MAX_SECUENCIAL}"
        
        # Validar establecimiento y punto emisión
        if not establecimiento or len(establecimiento) != 3:
            return False, "Establecimiento debe tener 3 dígitos"
        
        if not punto_emision or len(punto_emision) != 3:
            return False, "Punto de emisión debe tener 3 dígitos"
        
        return True, "OK"
    
    def formatear_numero_comprobante(
        self,
        establecimiento: str,
        punto_emision: str,
        secuencial: int
    ) -> str:
        """
        Formatea el número de comprobante
        
        Args:
            establecimiento: Código de establecimiento
            punto_emision: Código de punto de emisión
            secuencial: Número secuencial
            
        Returns:
            Número formateado: 001-001-000000001
        """
        return f"{establecimiento}-{punto_emision}-{str(secuencial).zfill(9)}"
    
    def _get_campo_secuencial(self, tipo_comprobante: str) -> str:
        """
        Obtiene el nombre del campo de secuencial según el tipo
        
        Args:
            tipo_comprobante: Tipo de comprobante
            
        Returns:
            Nombre del campo
        """
        campos = {
            "01": "secuencia_factura",
            "04": "secuencia_nota_credito",
            "05": "secuencia_nota_debito",
            "06": "secuencia_guia_remision",
            "07": "secuencia_retencion",
        }
        
        return campos.get(tipo_comprobante, "secuencia_factura")
    
    def _get_cache_key(self, config_id: int, tipo: str) -> str:
        """Obtiene la clave de cache"""
        return f"{self._cache_key_prefix}{config_id}_{tipo}"
    
    def reiniciar_secuencial(
        self,
        configuracion,
        tipo_comprobante: str = "01",
        nuevo_valor: int = 1
    ) -> bool:
        """
        Reinicia el secuencial a un valor específico
        
        Args:
            configuracion: Instancia de Configuracion
            tipo_comprobante: Tipo de comprobante
            nuevo_valor: Nuevo valor del secuencial
            
        Returns:
            True si fue exitoso
        """
        try:
            with transaction.atomic():
                config = type(configuracion).objects.select_for_update().get(
                    pk=configuracion.id
                )
                
                campo = self._get_campo_secuencial(tipo_comprobante)
                setattr(config, campo, nuevo_valor)
                config.save(update_fields=[campo])
                
                # Limpiar cache
                key = self._get_cache_key(configuracion.id, tipo_comprobante)
                cache.delete(key)
                
                logger.info(f"Secuencial reiniciado a {nuevo_valor}")
                return True
                
        except Exception as e:
            logger.error(f"Error al reiniciar secuencial: {str(e)}")
            return False


def obtener_siguiente_secuencial(configuracion, tipo: str = "01") -> int:
    """
    Función de conveniencia para obtener siguiente secuencial
    
    Args:
        configuracion: Instancia de Configuracion
        tipo: Tipo de comprobante
        
    Returns:
        Siguiente secuencial
    """
    gestor = GestorSecuencial()
    return gestor.obtener_sigiente_secuencial(configuracion, tipo)


def formatear_numero_factura(
    establecimiento: str,
    punto_emision: str,
    secuencial: int
) -> str:
    """
    Función de conveniencia para formatear número de factura
    
    Args:
        establecimiento: Código establecimiento
        punto_emision: Código punto emisión
        secuencial: Número secuencial
        
    Returns:
        Número formateado
    """
    return f"{establecimiento}-{punto_emision}-{str(secuencial).zfill(9)}"
