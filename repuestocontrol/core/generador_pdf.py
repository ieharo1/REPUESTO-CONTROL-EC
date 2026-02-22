"""
Módulo de Generación PDF RIDE (Representación Impresa del Documento Electrónico)

Este módulo genera el PDF del comprobante electrónico autorizado por el SRI,
cumpliendo con los requisitos establecidos en la Resolución del SRI.

El RIDE incluye:
- Datos del establecimiento/emisor
- Información del cliente
- Detalle de productos/servicios
- Desglose de impuestos
- Formas de pago
- Código de barras (Code128)
- Código QR
- Número de autorización
- Clave de acceso
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.barcode import code128

import qrcode
from PIL import Image as PILImage

logger = logging.getLogger(__name__)


class GeneradorRIDE:
    """
    Generador de PDF RIDE para comprobantes electrónicos SRI

    Attributes:
        titulo: Título del documento
        autor: Autor del documento
    """

    # Colores corporativos
    COLOR_PRIMARIO = colors.HexColor("#1a5276")
    COLOR_SECUNDARIO = colors.HexColor("#2980b9")
    COLOR_TEXTO = colors.HexColor("#2c3e50")
    COLOR_BORDE = colors.HexColor("#bdc3c7")
    COLOR_FONDO = colors.HexColor("#f8f9fa")

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._configurar_estilos()

    def _configurar_estilos(self):
        """Configura estilos personalizados para el PDF"""
        # Título principal
        self.styles.add(
            ParagraphStyle(
                name="TituloPrincipal",
                parent=self.styles["Heading1"],
                fontSize=16,
                textColor=self.COLOR_PRIMARIO,
                spaceAfter=10,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
            )
        )

        # Subtítulo
        self.styles.add(
            ParagraphStyle(
                name="Subtitulo",
                parent=self.styles["Heading2"],
                fontSize=12,
                textColor=self.COLOR_SECUNDARIO,
                spaceAfter=8,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
            )
        )

        # Normal
        self.styles.add(
            ParagraphStyle(
                name="Normal",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=self.COLOR_TEXTO,
                alignment=TA_LEFT,
                leading=12,
            )
        )

        # Normal negrita
        self.styles.add(
            ParagraphStyle(
                name="NormalBold",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=self.COLOR_TEXTO,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
                leading=12,
            )
        )

        # Datos tabla
        self.styles.add(
            ParagraphStyle(
                name="DatoTabla",
                parent=self.styles["Normal"],
                fontSize=8,
                alignment=TA_LEFT,
                leading=10,
            )
        )

        # Cabecera tabla
        self.styles.add(
            ParagraphStyle(
                name="CabeceraTabla",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.white,
                alignment=TA_CENTER,
                fontName="Helvetica-Bold",
                leading=10,
            )
        )

    def generar_pdf(
        self, datos_factura: Dict[str, Any], archivo_salida: Optional[str] = None
    ) -> bytes:
        """
        Genera el PDF del RIDE

        Args:
            datos_factura: Diccionario con todos los datos de la factura
            archivo_salida: Ruta donde guardar el PDF (opcional)

        Returns:
            Bytes del PDF generado
        """
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=15 * mm,
            leftMargin=15 * mm,
            topMargin=10 * mm,
            bottomMargin=15 * mm,
        )

        # Construir contenido
        story = []

        # Título
        titulo = Paragraph("FACTURA ELECTRÓNICA", self.styles["TituloPrincipal"])
        story.append(titulo)
        story.append(Spacer(1, 5))

        # Datos principales en tabla
        story.extend(self._crear_tabla_datos_principales(datos_factura))
        story.append(Spacer(1, 10))

        # Información del emisor
        story.extend(self._crear_info_emisor(datos_factura))
        story.append(Spacer(1, 10))

        # Información del cliente
        story.extend(self._crear_info_cliente(datos_factura))
        story.append(Spacer(1, 10))

        # Detalle de productos
        story.extend(self._crear_tabla_detalles(datos_factura))
        story.append(Spacer(1, 10))

        # Totales
        story.extend(self._crear_tabla_totales(datos_factura))
        story.append(Spacer(1, 10))

        # Formas de pago
        story.extend(self._crear_formas_pago(datos_factura))
        story.append(Spacer(1, 15))

        # Información de autorización
        story.extend(self._crear_info_autorizacion(datos_factura))

        # Generar PDF
        doc.build(story)

        pdf_bytes = buffer.getvalue()
        buffer.close()

        if archivo_salida:
            with open(archivo_salida, "wb") as f:
                f.write(pdf_bytes)
            logger.info(f"PDF guardado en: {archivo_salida}")

        return pdf_bytes

    def _crear_tabla_datos_principales(self, datos: Dict) -> List:
        """Crea tabla con datos principales de la factura"""
        story = []

        # Cabecera con número de factura
        empresa = datos.get("empresa", {})
        factura = datos.get("factura", {})

        # Tabla principal
        data = [
            [
                Paragraph(
                    f"<b>R.U.C.:</b> {empresa.get('ruc', '')}",
                    self.styles["NormalBold"],
                ),
                Paragraph(
                    f"<b>FACTURA N°:</b> {factura.get('numero', '')}",
                    self.styles["NormalBold"],
                ),
            ],
            [
                Paragraph(f"<b>Num. Autorización:</b>", self.styles["Normal"]),
                Paragraph(
                    factura.get("numero_autorizacion", ""), self.styles["Normal"]
                ),
            ],
            [
                Paragraph(f"<b>Fecha Autorización:</b>", self.styles["Normal"]),
                Paragraph(factura.get("fecha_autorizacion", ""), self.styles["Normal"]),
            ],
        ]

        tabla = Table(data, colWidths=[8 * cm, 10 * cm])
        tabla.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 1, self.COLOR_BORDE),
                    ("BACKGROUND", (0, 0), (-1, 0), self.COLOR_PRIMARIO),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )

        story.append(tabla)
        return story

    def _crear_info_emisor(self, datos: Dict) -> List:
        """Crea información del emisor"""
        story = []

        empresa = datos.get("empresa", {})
        factura = datos.get("factura", {})

        story.append(Paragraph("INFORMACIÓN DEL EMISOR", self.styles["Subtitulo"]))

        data = [
            [
                Paragraph("<b>Razón Social:</b>", self.styles["NormalBold"]),
                Paragraph(empresa.get("razon_social", ""), self.styles["Normal"]),
            ],
            [
                Paragraph("<b>Nombre Comercial:</b>", self.styles["NormalBold"]),
                Paragraph(empresa.get("nombre_comercial", ""), self.styles["Normal"]),
            ],
            [
                Paragraph("<b>Dirección:</b>", self.styles["NormalBold"]),
                Paragraph(empresa.get("direccion", ""), self.styles["Normal"]),
            ],
            [
                Paragraph("<b>Teléfono:</b>", self.styles["NormalBold"]),
                Paragraph(empresa.get("telefono", ""), self.styles["Normal"]),
            ],
            [
                Paragraph("<b>Fecha Emisión:</b>", self.styles["NormalBold"]),
                Paragraph(factura.get("fecha_emision", ""), self.styles["Normal"]),
            ],
            [
                Paragraph("<b>Clave de Acceso:</b>", self.styles["NormalBold"]),
                Paragraph(factura.get("clave_acceso", ""), self.styles["Normal"]),
            ],
        ]

        tabla = Table(data, colWidths=[4 * cm, 14 * cm])
        tabla.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, self.COLOR_BORDE),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        story.append(tabla)
        return story

    def _crear_info_cliente(self, datos: Dict) -> List:
        """Crea información del cliente"""
        story = []

        cliente = datos.get("cliente", {})

        story.append(Paragraph("INFORMACIÓN DEL COMPRADOR", self.styles["Subtitulo"]))

        data = [
            [
                Paragraph("<b>Razón Social:</b>", self.styles["NormalBold"]),
                Paragraph(cliente.get("nombre", ""), self.styles["Normal"]),
            ],
            [
                Paragraph("<b>Identificación:</b>", self.styles["NormalBold"]),
                Paragraph(cliente.get("identificacion", ""), self.styles["Normal"]),
            ],
            [
                Paragraph("<b>Dirección:</b>", self.styles["NormalBold"]),
                Paragraph(cliente.get("direccion", ""), self.styles["Normal"]),
            ],
            [
                Paragraph("<b>Teléfono:</b>", self.styles["NormalBold"]),
                Paragraph(cliente.get("telefono", ""), self.styles["Normal"]),
            ],
        ]

        tabla = Table(data, colWidths=[4 * cm, 14 * cm])
        tabla.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, self.COLOR_BORDE),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        story.append(tabla)
        return story

    def _crear_tabla_detalles(self, datos: Dict) -> List:
        """Crea tabla de detalles de productos"""
        story = []

        detalles = datos.get("detalles", [])
        totales = datos.get("totales", {})

        story.append(
            Paragraph("DETALLE DE PRODUCTOS/SERVICIOS", self.styles["Subtitulo"])
        )

        # Cabecera de tabla
        headers = ["Código", "Descripción", "Cant.", "P. Unit.", "Desc.", "Total"]

        # Anchos de columna
        col_widths = [2 * cm, 7 * cm, 1.5 * cm, 2 * cm, 1.5 * cm, 2 * cm]

        # Datos
        table_data = [headers]

        for item in detalles:
            table_data.append(
                [
                    Paragraph(str(item.get("codigo", "")), self.styles["DatoTabla"]),
                    Paragraph(
                        str(item.get("nombre", ""))[:50], self.styles["DatoTabla"]
                    ),
                    Paragraph(str(item.get("cantidad", "")), self.styles["DatoTabla"]),
                    Paragraph(
                        f"{float(item.get('precio', 0)):.2f}", self.styles["DatoTabla"]
                    ),
                    Paragraph(
                        f"{float(item.get('descuento', 0)):.2f}",
                        self.styles["DatoTabla"],
                    ),
                    Paragraph(
                        f"{float(item.get('subtotal', 0)):.2f}",
                        self.styles["DatoTabla"],
                    ),
                ]
            )

        tabla = Table(table_data, colWidths=col_widths)
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.COLOR_PRIMARIO),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("TOPPADDING", (0, 0), (-1, 0), 8),
                    ("BACKGROUND", (0, 1), (-1, -1), self.COLOR_FONDO),
                    ("GRID", (0, 0), (-1, -1), 0.5, self.COLOR_BORDE),
                    ("LEFTPADDING", (0, 0), (-1, -1), 2),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )

        story.append(tabla)
        return story

    def _crear_tabla_totales(self, datos: Dict) -> List:
        """Crea tabla de totales"""
        story = []

        totales = datos.get("totales", {})

        # Datos para totales
        data = [
            [
                Paragraph("<b>Subtotal 12%:</b>", self.styles["NormalBold"]),
                Paragraph(
                    f"{float(totales.get('subtotal_12', 0)):.2f}", self.styles["Normal"]
                ),
            ],
            [
                Paragraph("<b>Subtotal 0%:</b>", self.styles["NormalBold"]),
                Paragraph(
                    f"{float(totales.get('subtotal_0', 0)):.2f}", self.styles["Normal"]
                ),
            ],
            [
                Paragraph("<b>Descuento:</b>", self.styles["NormalBold"]),
                Paragraph(
                    f"{float(totales.get('descuento', 0)):.2f}", self.styles["Normal"]
                ),
            ],
            [
                Paragraph("<b>IVA:</b>", self.styles["NormalBold"]),
                Paragraph(f"{float(totales.get('iva', 0)):.2f}", self.styles["Normal"]),
            ],
            [
                Paragraph("<b>TOTAL:</b>", self.styles["NormalBold"]),
                Paragraph(
                    f"{float(totales.get('total', 0)):.2f}", self.styles["Normal"]
                ),
            ],
        ]

        tabla = Table(data, colWidths=[12 * cm, 6 * cm])
        tabla.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, self.COLOR_BORDE),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("VALIGN", (0, 0), (-1, -1), "RIGHT"),
                    ("BACKGROUND", (-1, -1), (-1, -1), self.COLOR_PRIMARIO),
                    ("TEXTCOLOR", (-1, -1), (-1, -1), colors.white),
                    ("FONTNAME", (-1, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )

        story.append(tabla)
        return story

    def _crear_formas_pago(self, datos: Dict) -> List:
        """Crea sección de formas de pago"""
        story = []

        formas_pago = datos.get("formas_pago", [])

        if formas_pago:
            story.append(Paragraph("FORMAS DE PAGO", self.styles["Subtitulo"]))

            data = []
            for fp in formas_pago:
                data.append(
                    [
                        Paragraph(fp.get("forma_pago", ""), self.styles["Normal"]),
                        Paragraph(
                            f"{float(fp.get('valor', 0)):.2f}", self.styles["Normal"]
                        ),
                    ]
                )

            tabla = Table(data, colWidths=[12 * cm, 6 * cm])
            tabla.setStyle(
                TableStyle(
                    [
                        ("BOX", (0, 0), (-1, -1), 0.5, self.COLOR_BORDE),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )

            story.append(tabla)

        return story

    def _crear_info_autorizacion(self, datos: Dict) -> List:
        """Crea información de autorización con códigos"""
        story = []

        factura = datos.get("factura", {})

        story.append(Paragraph("INFORMACIÓN DE AUTORIZACIÓN", self.styles["Subtitulo"]))

        # Clave de acceso
        clave_acceso = factura.get("clave_acceso", "")

        # Generar código de barras
        barcode = code128.Code128(clave_acceso, barWidth=0.8, barHeight=20)
        barcode_bytes = BytesIO()
        barcode.drawOn(canvas.Canvas(barcode_bytes), 0, 0)

        # Generar QR
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(clave_acceso)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        qr_bytes = BytesIO()
        qr_img.save(qr_bytes, format="PNG")
        qr_bytes.seek(0)

        # Crear tabla con códigos
        data = [
            [
                Paragraph("<b>Clave de Acceso</b>", self.styles["NormalBold"]),
                Paragraph("<b>Código QR</b>", self.styles["NormalBold"]),
            ],
            [
                Paragraph(
                    clave_acceso[:25] + "<br/>" + clave_acceso[25:],
                    self.styles["DatoTabla"],
                ),
                Image(qr_bytes, width=4 * cm, height=4 * cm),
            ],
        ]

        tabla = Table(data, colWidths=[10 * cm, 5 * cm])
        tabla.setStyle(
            TableStyle(
                [
                    ("BOX", (0, 0), (-1, -1), 0.5, self.COLOR_BORDE),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, -1), "CENTER"),
                ]
            )
        )

        story.append(tabla)

        # Nota de autorización
        story.append(Spacer(1, 10))
        nota = Paragraph(
            f"Documento autorizado por el SRI el {factura.get('fecha_autorizacion', '')}. "
            f"Número de autorización: {factura.get('numero_autorizacion', '')}",
            self.styles["Normal"],
        )
        story.append(nota)

        return story


def generar_pdf_rid(venta, config, archivo_salida: Optional[str] = None) -> bytes:
    """
    Función de conveniencia para generar PDF RIDE desde una venta

    Args:
        venta: Instancia del modelo Venta
        config: Instancia de Configuracion
        archivo_salida: Ruta donde guardar el PDF (opcional)

    Returns:
        Bytes del PDF
    """
    generador = GeneradorRIDE()

    # Preparar datos
    datos = {
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
            "numero_autorizacion": getattr(venta, "numero_autorizacion", ""),
            "fecha_autorizacion": getattr(venta, "fecha_autorizacion", ""),
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
            for d in venta.detalles.select_related("repuesto").all()
        ],
        "totales": {
            "subtotal_12": float(venta.subtotal_12),
            "subtotal_0": float(venta.subtotal_0),
            "descuento": float(venta.descuento),
            "iva": float(venta.iva),
            "total": float(venta.total),
        },
        "formas_pago": [
            {
                "forma_pago": dict(Venta.MetodoPago.choices).get(
                    venta.metodo_pago, "Efectivo"
                ),
                "valor": float(venta.total),
            }
        ],
    }

    return generador.generar_pdf(datos, archivo_salida)


# Importar choices de Venta
from repuestocontrol.ventas.models import Venta
