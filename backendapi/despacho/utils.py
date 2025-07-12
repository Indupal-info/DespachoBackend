# despacho/utils.py

from twilio.rest import Client
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO
from django.conf import settings
import os
from .models import MachineEntry

def enviar_pdf_whatsapp(numero_destino, pdf_url, mensaje="Aquí está tu documento PDF"):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    mensaje = client.messages.create(
        from_='whatsapp:+14155238886',  # Tu número de Twilio (sandbox o real)
        to=f'whatsapp:{numero_destino}',
        body=mensaje,
        media_url=[pdf_url]
    )

    return mensaje.sid


def generar_comprobante_pdf_a_archivo(comprobante_id: str) -> str:
    comprobante = MachineEntry.objects.select_related("client", "branch").get(comprobante_ingreso=comprobante_id)

    cliente = comprobante.client
    sucursal = comprobante.branch
    modelo = comprobante.machine_model or "N/A"
    serie = comprobante.serial_number or "N/A"
    accesorios = comprobante.accessories or "Ninguno"
    falla = comprobante.reported_fault or "No especificada"
    fecha = comprobante.arrival_date
    hora = comprobante.arrival_time

    fecha_hora = "N/D"
    if fecha and hora:
        try:
            fecha_hora = f"{fecha.strftime('%d/%m/%Y')} {hora.strftime('%H:%M:%S')}"
        except Exception:
            pass

    nombre_cliente = cliente.client_name if cliente else "N/A"
    direccion_cliente = ", ".join(p for p in [cliente.direccion, cliente.municipio, cliente.departamento] if p) if cliente else "N/A"
    nombre_sucursal = sucursal.name if sucursal else "N/A"

    filename = f"comprobante_{comprobante_id}.pdf"
    filepath = os.path.join(settings.MEDIA_ROOT, filename)
    p = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4
    y = height - 80

    def draw_label_value(label, value):
        nonlocal y
        p.setFont("Helvetica-Bold", 10)
        p.drawString(40, y, label)
        p.setFont("Helvetica", 10)
        p.drawString(160, y, value)
        y -= 20

    base_path = os.path.dirname(__file__)
    indupal_logo = os.path.join(base_path, 'static', 'indupal_logo.png')
    karcher_logo = os.path.join(base_path, 'static', 'karcher_logo.png')

    try:
        p.drawImage(karcher_logo, 40, height - 60, width=120, height=40, preserveAspectRatio=True)
        p.drawImage(indupal_logo, width - 160, height - 60, width=120, height=40, preserveAspectRatio=True)
    except:
        pass

    p.setFillColor(colors.HexColor('#FFD500'))
    p.rect(40, y + 10, width - 80, 25, fill=True, stroke=False)
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2, y + 17, "FICHA DE REGISTRO DE EQUIPO")
    y -= 40

    draw_label_value("Comprobante Nro:", comprobante.comprobante_ingreso)
    draw_label_value("Fecha Ingreso:", fecha_hora)
    draw_label_value("Sucursal:", nombre_sucursal)
    y -= 10
    p.line(40, y, width - 40, y)
    y -= 25
    draw_label_value("Cliente:", nombre_cliente)
    draw_label_value("Ubicación:", direccion_cliente)
    y -= 10
    p.line(40, y, width - 40, y)
    y -= 25
    draw_label_value("Modelo:", modelo)
    draw_label_value("Serie:", serie)
    y -= 10
    p.line(40, y, width - 40, y)
    y -= 25
    p.setFont("Helvetica-Bold", 10)
    p.drawString(40, y, "Accesorios Incluidos:")
    p.setFont("Helvetica", 10)
    p.drawString(180, y, accesorios)
    y -= 20
    p.setFont("Helvetica-Bold", 10)
    p.drawString(40, y, "Falla Reportada por el Cliente:")
    p.setFont("Helvetica", 10)
    p.drawString(220, y, falla)
    y -= 40
    p.setFont("Helvetica", 10)
    p.drawString(40, y, "Gracias por confiar en Karcher - Indupal El Salvador.")
    p.showPage()
    p.save()

    return f"{settings.MEDIA_URL}{filename}"  # URL relativa para Django