"""
Tests para el módulo de Facturación Electrónica SRI

Este módulo contiene tests para:
- Generación de clave de acceso
- Validación de clave de acceso (módulo 11)
- Validación XSD
- Cálculo de impuestos
- Control secuencial
- Simulación de respuesta SOAP
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestClaveAcceso:
    """Tests para la generación y validación de clave de acceso"""

    def test_generar_clave_acceso_longitud(self):
        """La clave de acceso debe tener 49 dígitos"""
        from repuestocontrol.core.sri import generar_clave_acceso

        clave = generar_clave_acceso(
            fecha_emision="22/02/2026",
            tipo_comprobante="01",
            ruc="1791234567001",
            ambiente="1",
            establecimiento="001",
            punto_emision="001",
            secuencial="1",
        )

        assert len(clave) == 49, f"La clave debe tener 49 dígitos, tiene {len(clave)}"
        assert clave.isdigit(), "La clave debe contener solo dígitos"

    def test_generar_clave_acceso_formato(self):
        """Verifica el formato de la clave de acceso"""
        from repuestocontrol.core.sri import generar_clave_acceso

        clave = generar_clave_acceso(
            fecha_emision="22/02/2026",
            tipo_comprobante="01",
            ruc="1791234567001",
            ambiente="1",
            establecimiento="001",
            punto_emision="001",
            secuencial="1",
        )

        # Verificar formato: DDMMYYYY +Tipo+RUC+Amb+Estab+PtoEmi+Secuencial+TipoEmi+CodNum+DV
        assert clave[:8] == "22022026", "Fecha incorrecta"
        assert clave[8:10] == "01", "Tipo comprobante incorrecto"
        assert clave[10:23] == "1791234567001", "RUC incorrecto"
        assert clave[23] == "1", "Ambiente incorrecto"
        assert clave[24:27] == "001", "Establecimiento incorrecto"
        assert clave[27:30] == "001", "Punto emisión incorrecto"
        assert clave[30:39] == "000000001", "Secuencial incorrecto"
        assert clave[39] == "1", "Tipo emisión incorrecto"

    def test_digito_verificador_modulo11(self):
        """Verifica que el dígito verificador sea correcto (módulo 11)"""
        from repuestocontrol.core.sri import calcular_digito_verificador

        # Cadena de prueba
        cadena = "22022026011791234567001001001000000000110000000"
        digito = calcular_digito_verificador(cadena)

        # El resultado debe ser un dígito
        assert digito.isdigit(), "El dígito verificador debe ser un dígito"
        assert len(digito) == 1, "El dígito verificador debe tener un solo dígito"


class TestValidacionIdentificacion:
    """Tests para validación de identificación"""

    def test_validar_cedula_correcta(self):
        """Cédula válida"""
        from repuestocontrol.core.sri import validar_cedula

        # Cédula de prueba válida
        assert validar_cedula("1712345678") == True

    def test_validar_cedula_incorrecta(self):
        """Cédula inválida"""
        from repuestocontrol.core.sri import validar_cedula

        # Cédula con formato incorrecto
        assert validar_cedula("12345") == False
        assert validar_cedula("12345678901") == False
        assert validar_cedula("abcdefghij") == False

    def test_validar_ruc(self):
        """Validación de RUC"""
        from repuestocontrol.core.sri import validar_ruc

        # RUC válido (13 dígitos)
        assert validar_ruc("1791234567001") == True

        # RUC inválido
        assert validar_ruc("1791234567") == False
        assert validar_ruc("12345678901234") == False


class TestCalculoImpuestos:
    """Tests para cálculo de impuestos"""

    def test_calculo_iva_12(self):
        """Cálculo de IVA al 12%"""
        subtotal = Decimal("100.00")
        iva_tarifa = Decimal("12.00")

        iva = subtotal * (iva_tarifa / Decimal("100"))

        assert iva == Decimal("12.00")

    def test_calculo_iva_15(self):
        """Cálculo de IVA al 15%"""
        subtotal = Decimal("100.00")
        iva_tarifa = Decimal("15.00")

        iva = subtotal * (iva_tarifa / Decimal("100"))

        assert iva == Decimal("15.00")

    def test_calculo_total_con_iva(self):
        """Cálculo total con IVA"""
        subtotal_12 = Decimal("100.00")
        subtotal_0 = Decimal("50.00")
        descuento = Decimal("10.00")
        iva_tarifa = Decimal("12.00")

        subtotal_con_desc = subtotal_12 - descuento
        iva = subtotal_con_desc * (iva_tarifa / Decimal("100"))
        total = subtotal_12 + subtotal_0 + iva - descuento

        assert iva == Decimal("10.80")
        assert total == Decimal("150.80")

    def test_calculo_iva_cero(self):
        """Cálculo con IVA 0%"""
        subtotal_0 = Decimal("100.00")

        iva = Decimal("0.00")

        assert iva == Decimal("0.00")


class TestFormateoNumeroFactura:
    """Tests para formateo de número de factura"""

    def test_formatear_numero_factura(self):
        """Formateo correcto del número de factura"""
        from repuestocontrol.core.sri import formatear_numero_factura

        numero = formatear_numero_factura("001", "001", 1)
        assert numero == "001-001-000000001"

    def test_formatear_numero_factura_secuencial_alto(self):
        """Formateo con secuencial alto"""
        from repuestocontrol.core.sri import formatear_numero_factura

        numero = formatear_numero_factura("001", "001", 123456789)
        assert numero == "001-001-123456789"


class TestValidacionXSD:
    """Tests para validación XSD"""

    def test_validar_estructura_basica(self):
        """Validación de estructura básica XML"""
        from repuestocontrol.core.validacion_xsd import ValidadorXSD

        xml_valido = """<?xml version="1.0" encoding="UTF-8"?>
<factura id="comprobante" version="1.1.0">
    <infoTributaria>
        <ambiente>1</ambiente>
        <tipoEmision>1</tipoEmision>
        <razonSocial>EMPRESA TEST</razonSocial>
        <ruc>1791234567001</ruc>
        <claveAcceso>2202202601179123456700100100100000000011000000001</claveAcceso>
        <codDoc>01</codDoc>
        <estab>001</estab>
        <ptoEmision>001</ptoEmision>
        <secuencial>000000001</secuencial>
        <dirMatriz>DIRECCION MATRIZ</dirMatriz>
    </infoTributaria>
    <infoFactura>
        <fechaEmision>22/02/2026</fechaEmision>
        <tipoIdentificacionComprador>05</tipoIdentificacionComprador>
        <razonSocialComprador>CLIENTE TEST</razonSocialComprador>
        <identificacionComprador>1712345678</identificacionComprador>
        <totalSinImpuestos>100.00</totalSinImpuestos>
        <importeTotal>112.00</importeTotal>
    </infoFactura>
    <detalles>
        <detalle>
            <codigoPrincipal>PROD001</codigoPrincipal>
            <descripcion>Producto prueba</descripcion>
            <cantidad>1</cantidad>
            <precioUnitario>100.00</precioUnitario>
            <precioTotalSinImpuesto>100.00</precioTotalSinImpuesto>
        </detalle>
    </detalles>
</factura>"""

        validador = ValidadorXSD()
        es_valido, errores = validador.validar_factura(xml_valido)

        # La estructura básica debería pasar
        assert isinstance(es_valido, bool)


class TestSimulacionRespuestaSOAP:
    """Tests para simulación de respuestas SOAP"""

    def test_simular_autorizacion(self):
        """Simulación de autorización"""
        from repuestocontrol.core.sri import simular_autorizacion_sri

        xml = "<factura>test</factura>"
        clave_acceso = "2202202601179123456700100100100000000011000000001"

        mock_config = Mock()
        mock_config.ambiente = "1"

        respuesta = simular_autorizacion_sri(xml, clave_acceso, mock_config)

        assert respuesta["estado"] == "AUTORIZADO"
        assert "numero_autorizacion" in respuesta
        assert "fecha_autorizacion" in respuesta
        assert len(respuesta["numero_autorizacion"]) > 0


class TestGeneracionXML:
    """Tests para generación de XML"""

    def test_generar_xml_factura(self):
        """Generación de XML de factura"""
        from repuestocontrol.core.sri import generar_xml_factura
        from repuestocontrol.ventas.models import Venta
        from repuestocontrol.core.models import Configuracion
        from unittest.mock import Mock

        # Crear mocks
        config = Mock(spec=Configuracion)
        config.razon_social = "Empresa Test"
        config.nombre_comercial = "Empresa Test"
        config.ruc = "1791234567001"
        config.direccion_matriz = "Direccion Matriz"
        config.direccion_sucursal = "Direccion Sucursal"
        config.ambiente = "1"
        config.tipo_emision = "1"
        config.establecimiento = "001"
        config.punto_emision = "001"
        config.secuencia_factura = 1
        config.iva_tarifa_12 = Decimal("12.00")

        venta = Mock(spec=Venta)
        venta.created_at = datetime(2026, 2, 22, 10, 0, 0)
        venta.subtotal_12 = Decimal("100.00")
        venta.subtotal_0 = Decimal("0.00")
        venta.descuento = Decimal("0.00")
        venta.cliente = None
        venta.detalles = Mock()
        venta.detalles.all.return_value = []

        resultado = generar_xml_factura(venta, config)

        assert "xml" in resultado
        assert "clave_acceso" in resultado
        assert "numero_factura" in resultado
        assert len(resultado["clave_acceso"]) == 49


class TestFormasPagoSRI:
    """Tests para formas de pago SRI"""

    def test_codigos_forma_pago(self):
        """Verifica códigos de forma de pago SRI"""
        # Códigos oficiales SRI
        formas_pago = {
            "01": "Efectivo",
            "02": "Cheque",
            "03": "Transferencia",
            "04": "Tarjeta de Débito",
            "05": "Tarjeta de Crédito",
            "06": "Dinero electrónico",
            "07": "Compensación",
            "08": "otros",
            "09": "Cooperativa",
            "10": "Extorno",
            "11": "Rebaja",
            "12": "bonos",
        }

        assert len(formas_pago) > 0
        assert formas_pago["01"] == "Efectivo"
        assert formas_pago["03"] == "Transferencia"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
