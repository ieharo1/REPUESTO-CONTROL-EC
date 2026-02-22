"""
Utilidades para facturación electrónica SRI Ecuador
"""

import re
import hashlib
import os
from datetime import datetime
from decimal import Decimal
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


def validar_ruc(ruc):
    """Valida que el RUC tenga 13 dígitos y sea válido"""
    if not ruc or len(ruc) != 13:
        return False
    if not ruc.isdigit():
        return False
    return True


def validar_cedula(cedula):
    """Valida cédula ecuatoriana con algoritmo módulo 10"""
    if not cedula or len(cedula) != 10:
        return False
    if not cedula.isdigit():
        return False

    provincia = int(cedula[:2])
    if provincia < 1 or provincia > 24:
        return False

    tercer_digito = int(cedula[2])
    if tercer_digito > 6:
        return False

    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = 0

    for i in range(9):
        producto = int(cedula[i]) * coeficientes[i]
        if producto > 9:
            producto -= 9
        suma += producto

    digito_verificador = (10 - (suma % 10)) % 10

    return digito_verificador == int(cedula[9])


def calcular_digito_verificador(cadena):
    """Calcula el dígito verificador módulo 11"""
    multiplicadores = [2, 3, 4, 5, 6, 7, 8, 9]
    suma = 0

    for i, char in enumerate(reversed(cadena)):
        producto = int(char) * multiplicadores[i % 8]
        suma += producto

    digito = 11 - (suma % 11)
    if digito == 11:
        digito = 0
    elif digito == 10:
        digito = 1

    return str(digito)


def generar_clave_acceso(
    fecha_emision,
    tipo_comprobante,
    ruc,
    ambiente,
    establecimiento,
    punto_emision,
    secuencial,
    tipo_emision="1",
):
    """
    Genera la clave de acceso según fórmula oficial SRI

    Formato: 49 dígitos
    - Fecha (8): DDMMYYYY
    - Tipo comprobante (2)
    - RUC (13)
    - Ambiente (1)
    - Establecimiento (3)
    - Punto emisión (3)
    - Secuencial (9)
    - Tipo emisión (1)
    - Código numérico (8)
    - Dígito verificador (1)
    """
    fecha = datetime.strptime(fecha_emision, "%d/%m/%Y").strftime("%d%m%Y")

    codigo_numerico = str(datetime.now().timestamp()).split(".")[-1][:8].zfill(8)

    parte1 = (
        fecha
        + tipo_comprobante
        + ruc
        + ambiente
        + establecimiento
        + punto_emision
        + secuencial.zfill(9)
        + tipo_emision
        + codigo_numerico
    )

    digito = calcular_digito_verificador(parte1)

    return parte1 + digito


def formatear_numero_factura(establecimiento, punto_emision, secuencial):
    """Formatea el número de factura: 001-001-000000001"""
    return f"{establecimiento}-{punto_emision}-{str(secuencial).zfill(9)}"


def generar_xml_factura(venta, config):
    """Genera el XML de factura según esquema SRI"""

    # Fecha emision
    fecha_emision = venta.created_at.strftime("%d/%m/%Y")

    # Generar clave de acceso
    secuencial = config.secuencia_factura
    clave_acceso = generar_clave_acceso(
        fecha_emision=fecha_emision,
        tipo_comprobante="01",  # Factura
        ruc=config.ruc,
        ambiente=config.ambiente,
        establecimiento=config.establecimiento,
        punto_emision=config.punto_emision,
        secuencial=str(secuencial),
        tipo_emision=config.tipo_emision,
    )

    numero_factura = formatear_numero_factura(
        config.establecimiento, config.punto_emision, secuencial
    )

    # Calcular IVA
    iva_tarifa = float(config.iva_tarifa_12)
    subtotal_12 = float(venta.subtotal_12)
    descuento = float(venta.descuento)
    subtotal_con_desc = subtotal_12 - descuento
    iva = round(subtotal_con_desc * (iva_tarifa / 100), 2)
    total = subtotal_12 + float(venta.subtotal_0) + iva - descuento

    # Datos del cliente
    if venta.cliente:
        cliente_tipo_id = {
            "ruc": "04",
            "cedula": "05",
            "pasaporte": "06",
            "consumidor_final": "07",
        }.get(venta.cliente.tipo_identificacion, "07")

        cliente_identificacion = venta.cliente.cedula or "9999999999"
        cliente_nombre = venta.cliente.nombre
        cliente_direccion = venta.cliente.direccion or "N/A"
        cliente_telefono = venta.cliente.telefono or ""
        cliente_email = venta.cliente.email or ""
    else:
        cliente_tipo_id = "07"
        cliente_identificacion = "9999999999"
        cliente_nombre = "CONSUMIDOR FINAL"
        cliente_direccion = "N/A"
        cliente_telefono = ""
        cliente_email = ""

    # Crear XML
    root = Element("factura")
    root.set("id", "comprobante")
    root.set("version", "1.1.0")

    # InfoTributaria
    info_tributaria = SubElement(root, "infoTributaria")

    ambiente_elem = SubElement(info_tributaria, "ambiente")
    ambiente_elem.text = config.ambiente

    tipo_emision_elem = SubElement(info_tributaria, "tipoEmision")
    tipo_emision_elem.text = config.tipo_emision

    razon_social_elem = SubElement(info_tributaria, "razonSocial")
    razon_social_elem.text = config.razon_social

    nombre_comercial_elem = SubElement(info_tributaria, "nombreComercial")
    nombre_comercial_elem.text = config.nombre_comercial or config.razon_social

    ruc_elem = SubElement(info_tributaria, "ruc")
    ruc_elem.text = config.ruc

    clave_acc_elem = SubElement(info_tributaria, "claveAcceso")
    clave_acc_elem.text = clave_acceso

    cod_doc_elem = SubElement(info_tributaria, "codDoc")
    cod_doc_elem.text = "01"  # Factura

    estab_elem = SubElement(info_tributaria, "estab")
    estab_elem.text = config.establecimiento

    pt_emision_elem = SubElement(info_tributaria, "ptoEmision")
    pt_emision_elem.text = config.punto_emision

    secuencial_elem = SubElement(info_tributaria, "secuencial")
    secuencial_elem.text = str(secuencial).zfill(9)

    dir_matriz_elem = SubElement(info_tributaria, "dirMatriz")
    dir_matriz_elem.text = config.direccion_matriz

    # InfoFactura
    info_factura = SubElement(root, "infoFactura")

    fecha_em_elem = SubElement(info_factura, "fechaEmision")
    fecha_em_elem.text = fecha_emision

    dir_establecimiento = SubElement(info_factura, "dirEstablecimiento")
    dir_establecimiento.text = config.direccion_sucursal or config.direccion_matriz

    tipo_id_cli_elem = SubElement(info_factura, "tipoIdentificacionComprador")
    tipo_id_cli_elem.text = cliente_tipo_id

    razon_social_cli = SubElement(info_factura, "razonSocialComprador")
    razon_social_cli.text = cliente_nombre

    identificacion_cli = SubElement(info_factura, "identificacionComprador")
    identificacion_cli.text = cliente_identificacion

    direccion_cli = SubElement(info_factura, "direccionComprador")
    direccion_cli.text = cliente_direccion

    telefono_cli = SubElement(info_factura, "telefonoComprador")
    telefono_cli.text = cliente_telefono

    email_cli = SubElement(info_factura, "emailComprador")
    email_cli.text = cliente_email

    obligado_contab = SubElement(info_factura, "obligadoContabilidad")
    obligado_contab.text = "SI" if config.obligado_contabilidad else "NO"

    if config.contribuyente_especial:
        cont_esp = SubElement(info_factura, "contribuyenteEspecial")
        cont_esp.text = config.resolucion_contribuyente or "N/A"

    tipo_cli = SubElement(info_factura, "tipoProveedor")
    tipo_cli.text = "01" if config.tipo_contribuyente == "sociedad" else "02"

    # Totales
    total_sin_impuestos = SubElement(info_factura, "totalSinImpuestos")
    total_sin_impuestos.text = f"{subtotal_12 + float(venta.subtotal_0):.2f}"

    total_desc = SubElement(info_factura, "totalDescuento")
    total_desc.text = f"{descuento:.2f}"

    # Impuestos
    if subtotal_12 > 0:
        impuestos = SubElement(info_factura, "totalImpuesto")

        codigo = SubElement(impuestos, "codigo")
        codigo.text = "2"  # IVA

        codigo_porcentaje = SubElement(impuestos, "codigoPorcentaje")
        codigo_porcentaje.text = (
            "2" if iva_tarifa == 12 else ("0" if iva_tarifa == 0 else "3")
        )

        base_imponible = SubElement(impuestos, "baseImponible")
        base_imponible.text = f"{subtotal_con_desc:.2f}"

        valor = SubElement(impuestos, "valor")
        valor.text = f"{iva:.2f}"

    # Propina
    importe_total = SubElement(info_factura, "importeTotal")
    importe_total.text = f"{total:.2f}"

    moneda = SubElement(info_factura, "moneda")
    moneda.text = "DOLAR"

    # Forma de pago
    pagos = SubElement(info_factura, "pagos")
    pago = SubElement(pagos, "pago")

    forma_pago = SubElement(pago, "formaPago")
    forma_pago.text = venta.forma_pago_sri or "01"

    valor_pago = SubElement(pago, "valor")
    valor_pago.text = f"{total:.2f}"

    # Detalles
    detalles = SubElement(root, "detalles")

    for detalle in venta.detalles.all():
        detalle_elem = SubElement(detalles, "detalle")

        codigo_principal = SubElement(detalle_elem, "codigoPrincipal")
        codigo_principal.text = detalle.repuesto.codigo

        descripcion = SubElement(detalle_elem, "descripcion")
        descripcion.text = detalle.repuesto.nombre

        cantidad = SubElement(detalle_elem, "cantidad")
        cantidad.text = str(detalle.cantidad)

        precio_unitario = SubElement(detalle_elem, "precioUnitario")
        precio_unitario.text = f"{float(detalle.precio_unitario):.2f}"

        descuento_linea = SubElement(detalle_elem, "descuento")
        descuento_linea.text = f"{float(detalle.descuento_item):.2f}"

        precio_total = SubElement(detalle_elem, "precioTotalSinImpuesto")
        precio_total.text = f"{float(detalle.subtotal):.2f}"

        impuestos_det = SubElement(detalle_elem, "impuestos")
        impuesto_det = SubElement(impuestos_det, "impuesto")

        codigo_imp = SubElement(impuesto_det, "codigo")
        codigo_imp.text = "2"

        codigo_porc_det = SubElement(impuesto_det, "codigoPorcentaje")
        codigo_porc_det.text = "2" if iva_tarifa == 12 else "0"

        tarifa = SubElement(impuesto_det, "tarifa")
        tarifa.text = f"{iva_tarifa:.0f}"

        base_imp_det = SubElement(impuesto_det, "baseImponible")
        base_imp_det.text = f"{float(detalle.subtotal):.2f}"

        valor_det = SubElement(impuesto_det, "valor")
        valor_det.text = f"{float(detalle.subtotal) * (iva_tarifa / 100):.2f}"

    # Convertir a string XML
    xml_str = tostring(root, encoding="unicode")

    # Formatear XML
    xml_formateado = minidom.parseString(xml_str).toprettyxml(indent="  ")

    # Limpiar espacios extras
    xml_limpio = "\n".join(
        [linea for linea in xml_formateado.split("\n") if linea.strip()]
    )

    return {
        "xml": xml_limpio,
        "clave_acceso": clave_acceso,
        "numero_factura": numero_factura,
        "secuencial": secuencial,
    }


def simular_autorizacion_sri(xml, clave_acceso, config):
    """
    Simula la autorización del SRI (para ambiente de pruebas)
    En producción, esto se conectaría al web service del SRI
    """
    import uuid
    from datetime import datetime

    numero_autorizacion = str(uuid.uuid4()).upper()[:49]
    fecha_autorizacion = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Simular respuesta autorizada
    respuesta = {
        "estado": "AUTORIZADO",
        "numero_autorizacion": numero_autorizacion,
        "fecha_autorizacion": fecha_autorizacion,
        "mensajes": [],
        "xmlAutorizado": xml,
    }

    return respuesta


def generar_rid_pdf(venta, config):
    """
    Genera los datos para el RIDE (Representación Impresa)
    """
    return {
        "empresa": {
            "razon_social": config.razon_social,
            "nombre_comercial": config.nombre_comercial or config.razon_social,
            "ruc": config.ruc,
            "direccion": config.direccion_sucursal or config.direccion_matriz,
            "telefono": config.telefono,
            "email": config.email,
        },
        "factura": {
            "numero": venta.numero_factura,
            "fecha_emision": venta.created_at.strftime("%d/%m/%Y"),
            "clave_acceso": venta.clave_acceso,
        },
        "cliente": {
            "nombre": venta.cliente_nombre,
            "identificacion": venta.cliente_identificacion,
            "direccion": venta.cliente_direccion,
            "telefono": venta.cliente_telefono,
            "email": venta.cliente_email,
        },
        "detalles": [
            {
                "codigo": d.repuesto.codigo,
                "nombre": d.repuesto.nombre,
                "cantidad": d.cantidad,
                "precio": float(d.precio_unitario),
                "descuento": float(d.descuento_item),
                "subtotal": float(d.subtotal),
            }
            for d in venta.detalles.all()
        ],
        "totales": {
            "subtotal_12": float(venta.subtotal_12),
            "subtotal_0": float(venta.subtotal_0),
            "descuento": float(venta.descuento),
            "iva": float(venta.iva),
            "total": float(venta.total),
        },
    }
