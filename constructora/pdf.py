"""Generacion de PDF de una cotizacion para enviar/imprimir al cliente.
reportlab es puro Python (sin librerias nativas que instalar aparte), a
diferencia de WeasyPrint — por eso se eligio para no complicar el setup local
en Windows."""
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def generar_pdf_cotizacion(cotizacion):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    estilos = getSampleStyleSheet()
    elementos = []

    levantamiento = cotizacion.levantamiento
    elementos.append(Paragraph("Cotización de obra", estilos["Title"]))
    elementos.append(Paragraph(f"{cotizacion.titulo} (versión {cotizacion.version})", estilos["Heading2"]))
    elementos.append(Spacer(1, 0.3 * cm))
    elementos.append(Paragraph(f"<b>Cliente:</b> {levantamiento.cliente.nombre}", estilos["Normal"]))
    if levantamiento.direccion:
        elementos.append(Paragraph(f"<b>Dirección de la obra:</b> {levantamiento.direccion}", estilos["Normal"]))
    elementos.append(Paragraph(f"<b>Proyecto:</b> {levantamiento.titulo}", estilos["Normal"]))
    elementos.append(Spacer(1, 0.6 * cm))

    datos = [["Concepto", "Unidad", "Cantidad", "Precio unitario", "Subtotal"]]
    for item in cotizacion.items:
        datos.append([
            item.concepto, item.unidad, f"{item.cantidad:,.2f}",
            f"${item.precio_unitario:,.2f}", f"${item.subtotal:,.2f}",
        ])
    datos.append(["", "", "", "Total", f"${cotizacion.total:,.2f}"])

    tabla = Table(datos, colWidths=[7 * cm, 2 * cm, 2.2 * cm, 3 * cm, 3 * cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#212529")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.grey),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elementos.append(tabla)

    if cotizacion.notas:
        elementos.append(Spacer(1, 0.6 * cm))
        elementos.append(Paragraph("<b>Notas</b>", estilos["Heading4"]))
        elementos.append(Paragraph(cotizacion.notas.replace("\n", "<br/>"), estilos["Normal"]))

    doc.build(elementos)
    buffer.seek(0)
    return buffer
