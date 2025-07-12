from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import AccessToken
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import uuid
import re

from .sqlserver_connector import get_sqlserver_connection
from .models import (
    Branch, Client, MachineEntry,
    RepairHistory, CallLog, SystemUser, MachineEntryMedia
)
from .serializers import (
    BranchSerializer, ClientSerializer, MachineEntrySerializer,
    RepairHistorySerializer, CallLogSerializer,
    SystemUserSerializer, MachineEntryDashboardFullSerializer, MachineEntryMediaSerializer,
    SystemUserCreateSerializer
)
from .permissions import IsAdminUser, IsAdminOrCanEdit
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from django.utils.encoding import smart_str
from io import BytesIO
from django.http import JsonResponse
from .utils import enviar_pdf_whatsapp
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from .utils import generar_comprobante_pdf_a_archivo, enviar_pdf_whatsapp
from reportlab.lib import colors
import os
from reportlab.lib.utils import ImageReader
def enviar_pdf_view(request):
    """
    Vista de prueba para enviar un PDF por WhatsApp usando Twilio.

    Asegúrate de que el número esté registrado en el sandbox de Twilio,
    y que el archivo PDF esté en una URL accesible públicamente.
    """
    numero_destino = "+50379883951"  # Número de WhatsApp destino (debe estar unido al sandbox)
    pdf_url = "https://file-examples.com/wp-content/uploads/2017/10/file-example_PDF_1MB.pdf"
 # URL pública del PDF
    mensaje = "Aquí está tu documento PDF desde el sistema de despacho."

    try:
        mensaje_id = enviar_pdf_whatsapp(numero_destino, pdf_url, mensaje)
        return JsonResponse({
            "success": True,
            "mensaje_id": mensaje_id,
            "info": "Mensaje enviado correctamente por WhatsApp"
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e),
            "info": "Hubo un error al enviar el mensaje"
        }, status=500)

# ✅ NUEVO: Generador de PDF de comprobante
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def generar_comprobante_pdf(request, comprobante_id):
    comprobante = get_object_or_404(MachineEntry, comprobante_ingreso=comprobante_id)

    cliente = comprobante.client
    sucursal = comprobante.branch
    modelo = comprobante.machine_model or "N/A"
    serie = comprobante.serial_number or "N/A"
    accesorios = comprobante.accessories or "Ninguno"
    falla = comprobante.reported_fault or "No especificada"
    fecha = comprobante.arrival_date
    hora = comprobante.arrival_time
    tipo_servicio = comprobante.tipo_servicio or "N/A"
    mediciones = comprobante.mediciones_tecnicas or "N/A"
    recibido_por = comprobante.recibido_por_nombre or "N/A"
    tipo_consumidor = comprobante.tipo_consumidor or "N/A"

    fecha_hora = "N/D"
    if fecha and hora:
        try:
            fecha_hora = f"{fecha.strftime('%d/%m/%Y')} {hora.strftime('%H:%M:%S')}"
        except Exception:
            pass

    nombre_cliente = cliente.client_name if cliente else "N/A"
    direccion_cliente = ", ".join(p for p in [cliente.direccion, cliente.municipio, cliente.departamento] if p) if cliente else "N/A"
    nombre_sucursal = sucursal.name if sucursal else "N/A"

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 80

    def draw_label_value(label, value):
        nonlocal y
        p.setFont("Helvetica-Bold", 10)
        p.drawString(40, y, label)
        p.setFont("Helvetica", 10)
        p.drawString(160, y, value)
        y -= 20

    def draw_label_multiline_value(label, value, max_width=400):
        nonlocal y
        from reportlab.pdfbase.pdfmetrics import stringWidth
        p.setFont("Helvetica-Bold", 10)
        p.drawString(40, y, label)
        p.setFont("Helvetica", 10)

        palabras = value.split()
        linea_actual = ""
        lineas = []

        for palabra in palabras:
            if stringWidth(linea_actual + " " + palabra, "Helvetica", 10) < max_width:
                linea_actual += " " + palabra
            else:
                lineas.append(linea_actual.strip())
                linea_actual = palabra
        if linea_actual:
            lineas.append(linea_actual.strip())

        for idx, linea in enumerate(lineas):
            p.drawString(160, y, linea)
            y -= 15 if idx < len(lineas) - 1 else 20

    base_path = os.path.dirname(os.path.abspath(__file__))
    indupal_logo = os.path.join(base_path, 'static', 'images', 'indupal.png')
    karcher_logo = os.path.join(base_path, 'static', 'images', 'karcher.png')

    try:
        if os.path.exists(karcher_logo):
            p.drawImage(ImageReader(karcher_logo), 40, height - 60, width=120, height=40, preserveAspectRatio=True)
        if os.path.exists(indupal_logo):
            p.drawImage(ImageReader(indupal_logo), width - 160, height - 60, width=120, height=40, preserveAspectRatio=True)
    except Exception:
        pass

    p.setFillColor(colors.HexColor('#FFD500'))
    p.rect(40, y + 10, width - 80, 25, fill=True, stroke=False)
    p.setFillColor(colors.black)
    p.setFont("Helvetica-Bold", 14)
    p.drawCentredString(width / 2, y + 17, "FICHA DE REGISTRO DE EQUIPO")
    y -= 20

    draw_label_value("Comprobante Nro:", comprobante.comprobante_ingreso)
    draw_label_value("Fecha Ingreso:", fecha_hora)
    draw_label_value("Sucursal:", nombre_sucursal)
    draw_label_value("Tipo de consumidor:", tipo_consumidor)

    y -= 10
    p.line(40, y, width - 40, y)
    y -= 25

    draw_label_value("Cliente:", nombre_cliente)
    draw_label_multiline_value("Ubicación:", direccion_cliente)

    y -= 10
    p.line(40, y, width - 40, y)
    y -= 25

    draw_label_value("Modelo:", modelo)
    draw_label_value("Serie:", serie)

    y -= 5
    p.line(40, y, width - 40, y)
    y -= 25

    draw_label_value("Accesorios:", accesorios)
    draw_label_value("Falla reportada:", falla)

    draw_label_value("Tipo de servicio:", tipo_servicio)
    draw_label_value("Mediciones técnicas:", mediciones)
    draw_label_value("Recibido por:", recibido_por)

    y -= 5
    p.setFont("Helvetica-Bold", 10)
    p.drawString(40, y, "Normativa:")
    y -= 10
    normativa = (
        "* Toda Revision, diagnostico o repracion hecha por nuestro departarmento de servicio Tecnico.\n"
        "   tendran un costo, incluso cuando el cliente decida no reparar la maquina.\n"
        "* El costo de revision o mantenimiento variara segun modelo de maquina.\n"
        "* En caso de que el clienta decida no reparar el equipo se cobrara $17.50 en concepto de revision.\n"
        "* El costo de revision o diagnostico no siempre es igual al costo de mano de obra, el cual se ofertara\n"
        "   posteriomente; pues la realizacion de una reparacion , frecuentemente demanda una mayor inversion de recursos\n"
        "* El Tiempo promedio necesario para realizar un diagnostico es de 72 horas habiles, transcurrido este \n"
        "  periodo se podra solicitar informacion sobre el estatus de la maquina. No aplica en equipos Industriales.\n"
        "* Todo Presupuesto estara sujeto a cambios.\n"
        "* Posterior al envio de presupuesto, se daran 3 dias de plazo para aprobarlo, esto para garantizar el stock de respuestos.\n"
        "* Posterior a la aprobacion de la reparacion, se daran 30 dias para que el propietario retire el equipo; en caso contrario \n"
        "  se enviara la maquina a bodega, cobrandose $1.00 diario en concepto de bodegaje.\n"
        "* Cuando la maquina tenga mas de 6 meses en bodegaje y no haya sido reclamada por el cliente, esta pasara a ser destruida.\n"
        "* La garantia en repuestos sustituidos es por un periodo de 30 dias siempre y cuando se haya autorizado \n"
        "  el 100% del presupuesto de reparacion.\n"
        "* La garantia no aplica a piezas de la maquina que estan sometidas a degaste normal como accesorios, carcasa, etc.\n"
    )
    for linea in normativa.split("\n"):
        p.setFont("Helvetica", 9)
        p.drawString(50, y, linea)
        y -= 12

    y -= 5
    p.setFont("Helvetica-Bold", 8)
    p.drawString(40, y, "Información de sucursales:")
    y -= 12
    sucursales = [
        "KÄRCHER CENTER - 25 Avenida Sur #752, San Salvador - Tel: 7619-4489 / 2510-3600",
        "KÄRCHER STORE SANTA ANA - Calle a Aldea San Antonio y 25 Calle Pte. - Tel: 7039-2766 / 2440-5396",
        "KÄRCHER STORE SAN MIGUEL - Col. Ciudad Jardín, Calle Los Naranjos #704 - Tel: 7986-2835 / 2660-0243",
    ]
    for s in sucursales:
        p.setFont("Helvetica", 9)
        p.drawString(50, y, s)
        y -= 12

    y -= 5
    p.setFont("Helvetica-Bold", 10)
    p.drawString(40, y, "Firma del Cliente:")

    if comprobante.firma_cliente and comprobante.firma_cliente.path:
        try:
            p.drawImage(comprobante.firma_cliente.path, 160, y - 40, width=100, height=40, preserveAspectRatio=True)
        except Exception:
            p.setFont("Helvetica", 9)
            p.drawString(160, y - 20, "[Firma no disponible]")
    else:
        p.setFont("Helvetica", 9)
        p.drawString(160, y - 20, "[No se proporcionó firma digital]")

    y -= 60
    p.setFont("Helvetica", 10)
    p.drawString(40, y, "Gracias por confiar en Kärcher - Indupal El Salvador.")

    p.showPage()
    p.save()
    buffer.seek(0)

    filename = f"comprobante_{comprobante.comprobante_ingreso}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response






def assign_permissions_by_role(user, role):
    if role == "Administrador":
        user.is_staff = True
        user.is_superuser = True
        user.save()
    else:
        group, _ = Group.objects.get_or_create(name=role)
        user.groups.add(group)
        user.is_staff = False
        user.is_superuser = False
        user.save()

@api_view(['POST'])
@permission_classes([IsAdminUser])
def crear_usuario_con_rol(request):
    serializer = SystemUserCreateSerializer(data=request.data)
    if serializer.is_valid():
        system_user = serializer.save()
        assign_permissions_by_role(system_user.user, system_user.role)
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([AllowAny])
def test_token_cookie(request):
    raw_token = request.COOKIES.get("access")
    if not raw_token:
        return Response({"tokenValido": False, "error": "No hay cookie 'access'"}, status=401)
    try:
        token = AccessToken(raw_token)
        return Response({"tokenValido": True, "user_id": token['user_id']})
    except Exception as e:
        return Response({"tokenValido": False, "error": str(e)}, status=401)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    user = request.user
    try:
        if hasattr(user, "systemuser") and user.systemuser is not None:
            role = user.systemuser.role
            branch_id = user.systemuser.branch.id if user.systemuser.branch else None
            branch_name = user.systemuser.branch.name if user.systemuser.branch else None
        elif user.is_superuser:
            role = "admin"
            branch_id = None
            branch_name = None
        else:
            return Response({"error": "El usuario no tiene perfil asignado."}, status=400)

        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': role,
            'branch_id': branch_id,
            'branch_name': branch_name,
        })
    except Exception as e:
        return Response({"error": f"Error interno: {str(e)}"}, status=500)

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAdminUser]

class SystemUserViewSet(viewsets.ModelViewSet):
    queryset = SystemUser.objects.all()
    serializer_class = SystemUserSerializer
    permission_classes = [IsAdminUser]

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [IsAdminOrCanEdit]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Client.objects.all()
        return Client.objects.filter(
            machineentry__branch_id=user.systemuser.branch_id
        ).distinct()

class MachineEntryViewSet(viewsets.ModelViewSet):
    queryset = MachineEntry.objects.all()
    serializer_class = MachineEntrySerializer
    permission_classes = [IsAdminOrCanEdit]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return MachineEntry.objects.all()
        return MachineEntry.objects.filter(branch_id=user.systemuser.branch_id)

class RepairHistoryViewSet(viewsets.ModelViewSet):
    queryset = RepairHistory.objects.all()
    serializer_class = RepairHistorySerializer
    permission_classes = [IsAdminOrCanEdit]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return RepairHistory.objects.all()
        return RepairHistory.objects.filter(machine_entry__branch_id=user.systemuser.branch_id)

class CallLogViewSet(viewsets.ModelViewSet):
    queryset = CallLog.objects.all()
    serializer_class = CallLogSerializer
    permission_classes = [IsAdminOrCanEdit]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return CallLog.objects.all()
        return CallLog.objects.filter(machine_entry__branch_id=user.systemuser.branch_id)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_maquina(request):
    codigo = request.GET.get('codigo', '').replace("'", "''")
    serie = request.GET.get('serie', '').replace("'", "''")
    if not codigo and not serie:
        return Response({"error": "Debe enviar al menos 'codigo' o 'serie'"}, status=400)

    try:
        conn = get_sqlserver_connection()
        cursor = conn.cursor()

        # 1. Buscar primero en INVENTARIO (Indupal)
        estado_actual = None
        comprobante = None
        mensaje = None
        fecha_entregada = None
        garantia_vigente = None
        fecha_vencimiento = None

        estados_map = {
            0: "EN ESPERA", 1: "REVISION TALLER", 2: "PRESUPUESTADA",
            3: "AUTORIZADA", 4: "EN REPARACION", 5: "ENTREGADA BODEGA",
            6: "REPARADA", 7: "ENTREGADA CLIENTE", 8: "NO ACEPTADA CLIENTE",
            9: "NO AUTORIZADA", 10: "CLIENTE INACTIVO", 11: "NO HAY REPUESTOS",
            12: "REPUESTOS SOLICITADO", 13: "REPUESTOS RECIBIDOS"
        }

        consulta_inventario = f'''SELECT TOP 1 Estado, Comprobante, Entregada
FROM [Indupal].[dbo].[Inventario]
WHERE Serie = '{serie}'
  AND Modelo LIKE '%{codigo}%'
ORDER BY Fecha DESC'''

        cursor.execute(consulta_inventario)
        resultado = cursor.fetchone()

        if resultado:
            estado_num, comprobante, fecha_entregada = resultado
            estado_actual = estados_map.get(estado_num, f"DESCONOCIDO ({estado_num})")
            if estado_num == 7 and fecha_entregada:
                if isinstance(fecha_entregada, datetime):
                    fecha_entregada = fecha_entregada.date()
                fecha_vencimiento = fecha_entregada + relativedelta(months=3)
                garantia_vigente = fecha_vencimiento >= date.today()
                mensaje = f"⚠️ Máquina entregada al cliente el {fecha_entregada} (Comprobante: {comprobante})"
            else:
                mensaje = f"⚠️ Máquina aún en reparación en despacho antiguo. Estado actual: {estado_actual} (Comprobante: {comprobante})"
        else:
            mensaje = "ℹ️ No se encontró en Inventario antiguo."

        # 2. Buscar SIEMPRE en linked server CLOUD para datos de cliente
        filtros = []
        if codigo:
            filtros.append(f'fd.codProductoFactura LIKE "%{codigo}%"')
        if serie:
            filtros.append(f'fd.nombreProductoFactura LIKE "%{serie}%"')
        where_clause = " AND ".join(filtros)

        query = f'''SELECT TOP 1 *
FROM OPENQUERY(CLOUD, '
    SELECT
        fd.codProductoFactura,
        fd.nombreProductoFactura,
        SUBSTRING(fd.nombreProductoFactura, LOCATE("(", fd.nombreProductoFactura) + 1, LOCATE(")", fd.nombreProductoFactura) - LOCATE("(", fd.nombreProductoFactura) - 1) AS numeroSerie,
        f.fechaEmision,
        cli.nombreCliente,
        u.direccionClienteUbicacion AS direccionCliente,
        c.contactoCliente AS telefonoCliente,
        c.descripcionContactoCliente AS notaContacto,
        p.nombreProducto AS descripcionCatalogo,
        (
            SELECT correo
            FROM bit_fel_correos b
            WHERE b.facturaId = f.facturaId
            ORDER BY fhAdd DESC
            LIMIT 1
        ) AS correoCliente
    FROM fel_factura f
    JOIN fel_factura_detalle fd ON f.facturaId = fd.facturaId
    LEFT JOIN inv_productos p ON fd.codProductoFactura = p.codInterno
    LEFT JOIN fel_clientes_ubicaciones u ON f.clienteUbicacionId = u.clienteUbicacionId
    LEFT JOIN fel_clientes cli ON u.clienteId = cli.clienteId
    LEFT JOIN fel_clientes_contactos c ON u.clienteUbicacionId = c.clienteUbicacionId
    WHERE {where_clause}
')'''

        cursor.execute(query)
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()
        if not row:
            return Response({
                "error": "No se encontraron datos de cliente.",
                "estadoAnterior": estado_actual,
                "comprobanteAnterior": comprobante,
                "mensaje": mensaje
            }, status=404)

        data = dict(zip(columns, row))
        nombre_producto = data.get("nombreProductoFactura", "")
        match = re.search(r"\(([^)]+)\)", nombre_producto)
        serial_number = match.group(1).strip() if match else None
        fecha_emision = data.get("fechaEmision")

        return Response({
            "codigo": data.get("codProductoFactura"),
            "descripcion": nombre_producto,
            "serialNumber": serial_number,
            "cliente": data.get("nombreCliente"),
            "direccion": data.get("direccionCliente"),
            "telefono": data.get("telefonoCliente"),
            "notaContacto": data.get("notaContacto"),
            "catalogo": data.get("descripcionCatalogo"),
            "correo": data.get("correoCliente"),
            "fechaFacturacion": fecha_emision.strftime("%Y-%m-%d") if fecha_emision else None,
            "fechaVencimientoGarantia": fecha_vencimiento.strftime("%Y-%m-%d") if fecha_vencimiento else None,
            "garantiaVigente": garantia_vigente,
            "estadoAnterior": estado_actual,
            "comprobanteAnterior": comprobante,
            "mensaje": mensaje
        })

    except Exception as e:
        return Response({"error": str(e)}, status=500)
    finally:
        if 'conn' in locals():
            conn.close()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def registrar_maquina(request):
    try:
        data = request.data
        cliente_nombre = data.get("clienteNombre")
        equipo = data.get("equipoDescripcion")
        serie = data.get("serie")
        observaciones = data.get("observaciones", "")
        accesorios = data.get("accessories", "")
        tipo = data.get("machineType", "")
        modelo = data.get("machineModel", "")
        codigo = data.get("codigoProducto", "")
        marca = data.get("marcaProducto", "")
        descripcion = data.get("descripcionProducto", "")
        registro_cliente = data.get("registroCliente", "").strip() or f"TEMP-{uuid.uuid4().hex[:8]}"
        email = data.get("email")
        contacto = data.get("contacto")
        telefono = data.get("telefono")
        celular = data.get("celular")
        departamento = data.get("departamento")
        municipio = data.get("municipio")
        direccion = data.get("direccion")
        nit = data.get("nit")

        tipo_servicio = data.get("tipoServicio", "")
        mediciones_tecnicas = data.get("medicionesTecnicas", "")
        recibido_por_nombre = data.get("recibidoPor", "")

        tipo_consumidor = data.get("tipoConsumidor")
        acepta_normativa = data.get("aceptaNormativa") == 'true'
        firma_cliente = request.FILES.get("firmaCliente")

        if not cliente_nombre or not equipo or not serie:
            return Response({"error": "Faltan campos obligatorios"}, status=400)

        if not acepta_normativa:
            return Response({"error": "Debe aceptar los términos y condiciones."}, status=400)

        cliente, creado = Client.objects.get_or_create(
            client_name=cliente_nombre,
            registro_cliente=registro_cliente,
            defaults={
                "contacto": contacto,
                "telefono": telefono,
                "celular": celular,
                "departamento": departamento,
                "municipio": municipio,
                "direccion": direccion,
                "email": email,
                "nit": nit,
            }
        )

        if not hasattr(request.user, "systemuser") or request.user.systemuser is None:
            return Response({"error": "El usuario no tiene un perfil de sistema asociado."}, status=400)

        if not request.user.systemuser.branch:
            return Response({"error": "El usuario no tiene una sucursal asignada."}, status=400)

        branch = request.user.systemuser.branch
        ingresado_por = request.user.systemuser

        nuevo = MachineEntry(
            client=cliente,
            branch=branch,
            arrival_date=timezone.now().date(),
            arrival_time=timezone.now().time(),
            ingresado_por=ingresado_por,
            machine_type=tipo,
            machine_model=modelo,
            serial_number=serie,
            codigo_producto=codigo,
            marca_producto=marca,
            descripcion_producto=descripcion,
            reported_fault=observaciones,
            accessories=accesorios,
            current_stage="INGRESADO",
            tipo_servicio=tipo_servicio,
            mediciones_tecnicas=mediciones_tecnicas,
            recibido_por_nombre=recibido_por_nombre,
            tipo_consumidor=tipo_consumidor,
            acepta_normativa=acepta_normativa,
            firma_cliente=firma_cliente
        )
        nuevo.save()

        for archivo in request.FILES.getlist("photos"):
            MachineEntryMedia.objects.create(machine_entry=nuevo, file=archivo)

        return Response({
            "success": True,
            "id": str(nuevo.id),
            "comprobante": nuevo.comprobante_ingreso,
            "clientDetails": {
                "clientName": cliente.client_name,
                "contacto": cliente.contacto,
                "telefono": cliente.telefono,
                "celular": cliente.celular,
                "departamento": cliente.departamento,
                "municipio": cliente.municipio,
                "direccion": cliente.direccion,
                "registroCliente": cliente.registro_cliente,
                "email": cliente.email,
                "nit": cliente.nit,
            },
            "branchId": str(branch.id)
        }, status=201)

    except Exception as e:
        import traceback
        print("*************************************")
        print("ERROR EN registrar_maquina:")
        traceback.print_exc()
        print("*************************************")
        return Response({"error": "Error al guardar en backend: " + str(e)}, status=500)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_maquinas_activas(request):
    user = request.user
    print("🧪 USUARIO:", user)
    print("🧪 Tiene systemuser:", hasattr(user, "systemuser"))
    print("🧪 Es superusuario:", user.is_superuser)

    if not hasattr(user, "systemuser") or user.systemuser is None:
        if user.is_superuser:
            maquinas = MachineEntry.objects.all().order_by('-arrival_date')
        else:
            print("❌ El usuario no tiene perfil asignado")
            return Response({"error": "El usuario no tiene perfil asignado."}, status=400)
    else:
        branch = user.systemuser.branch
        if not branch:
            print("❌ El usuario no tiene una sucursal asignada")
            return Response({"error": "El usuario no tiene una sucursal asignada."}, status=400)
        maquinas = MachineEntry.objects.filter(branch=branch).order_by('-arrival_date')

    serializer = MachineEntryDashboardFullSerializer(maquinas, many=True)
    return Response(serializer.data)



@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def editar_maquina(request, machine_id):
    try:
        machine = MachineEntry.objects.get(id=machine_id)
    except MachineEntry.DoesNotExist:
        return Response({'error': 'Máquina no encontrada'}, status=404)

    serializer = MachineEntrySerializer(machine, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detalle_maquina_completo(request, machine_id):
    machine = get_object_or_404(MachineEntry, id=machine_id)
    machine_serializer = MachineEntrySerializer(machine)

    repair_history = RepairHistory.objects.filter(machine_entry=machine).order_by('-start_date')
    repair_serializer = RepairHistorySerializer(repair_history, many=True)

    call_logs = CallLog.objects.filter(machine_entry=machine).order_by('-call_date')
    call_serializer = CallLogSerializer(call_logs, many=True)

    fotos = MachineEntryMedia.objects.filter(machine_entry=machine)
    foto_urls = [request.build_absolute_uri(foto.file.url) for foto in fotos]

    return Response({
        'maquina': machine_serializer.data,
        'historial_reparaciones': repair_serializer.data,
        'llamadas': call_serializer.data,
        'fotos': foto_urls,
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def custom_logout_view(request):
    response = Response({"message": "Sesión cerrada correctamente."})
    response.delete_cookie("access", path="/", samesite="Lax")
    response.delete_cookie("refresh_token", path="/", samesite="Lax")
    return response

class CustomLoginView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        refresh_token = response.data.get("refresh")
        access_token = response.data.get("access")

        if refresh_token:
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=False,
                samesite="Lax",
                path="/",
                max_age=86400,
            )
        if access_token:
            response.set_cookie(
                key="access",
                value=access_token,
                httponly=True,
                secure=False,
                samesite="Lax",
                path="/",
                max_age=600,
            )

        #response.data.pop('access', None)
        #response.data.pop('refresh', None)
        return response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cambiar_estado_maquina(request):
    try:
        machine_id = request.data.get("machine_id")
        nuevo_estado = request.data.get("nuevo_estado")
        notas = request.data.get("notas", "")
        mecanico_nombre = request.data.get("mecanico", "")
        presupuesto = request.data.get("presupuesto")

        if not machine_id or not nuevo_estado:
            return Response({"error": "Faltan datos obligatorios"}, status=400)

        machine = get_object_or_404(MachineEntry, id=machine_id)

        # Cerrar historial actual
        historial_abierto = RepairHistory.objects.filter(
            machine_entry=machine,
            end_date__isnull=True
        ).order_by('-start_date').first()

        if historial_abierto:
            historial_abierto.end_date = timezone.now()
            historial_abierto.save()

        # Identificar mecánico si aplica
        mecanico = None
        if mecanico_nombre:
            mecanico = SystemUser.objects.filter(name=mecanico_nombre).first()

        # Crear nuevo registro de reparación
        nuevo_log = RepairHistory.objects.create(
            machine_entry=machine,
            stage=nuevo_estado,
            start_date=timezone.now(),
            notes=notas,
            mechanic=mecanico,
            budget_amount=presupuesto if presupuesto else None,
            ingresado_por=request.user.systemuser if hasattr(request.user, "systemuser") else None
        )

        # Actualizar estado de máquina
        machine.current_stage = nuevo_estado
        machine.save()

        return Response({"success": True, "nuevo_estado": nuevo_estado}, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def registrar_llamada(request):
    try:
        machine_id = request.data.get("machine_id")
        notas = request.data.get("notas")
        atendido_por = request.data.get("atendido_por")

        if not machine_id or not notas or not atendido_por:
            return Response({"error": "Faltan datos obligatorios"}, status=400)

        machine = get_object_or_404(MachineEntry, id=machine_id)
        atendido = SystemUser.objects.filter(name=atendido_por).first()

        CallLog.objects.create(
            machine_entry=machine,
            call_date=timezone.now(),
            notes=notas,
            attended_by=atendido
        )

        return Response({"success": True}, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_mecanicos_sucursal(request):
    try:
        user = request.user
        if not hasattr(user, "systemuser") or user.systemuser is None:
            return Response({"error": "El usuario no tiene perfil asignado."}, status=400)

        sucursal = user.systemuser.branch
        if not sucursal:
            return Response({"error": "El usuario no tiene una sucursal asignada."}, status=400)

        # ✅ CAMBIO: Se usa SystemUserSerializer en lugar de SystemUserCreateSerializer para evitar error 500
        mecanicos = SystemUser.objects.filter(
            role="MECANICO",
            branch=sucursal,
            is_active=True
        )
        serializer = SystemUserSerializer(mecanicos, many=True)

        return Response(serializer.data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generar_y_enviar_comprobante(request):
    comprobante_id = request.data.get("comprobante_id")
    numero_destino = request.data.get("telefono")

    if not comprobante_id or not numero_destino:
        return JsonResponse({"success": False, "error": "Faltan datos"}, status=400)

    try:
        # Generar PDF y obtener URL relativa
        relative_url = generar_comprobante_pdf_a_archivo(comprobante_id)
        full_url = request.build_absolute_uri(relative_url)

        mensaje = "Aquí está tu comprobante de ingreso desde Indupal."
        mensaje_id = enviar_pdf_whatsapp(numero_destino, full_url, mensaje)

        return JsonResponse({
            "success": True,
            "mensaje_id": mensaje_id,
            "pdf_url": full_url,
            "info": "PDF generado y enviado correctamente por WhatsApp"
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e),
            "info": "Error al generar o enviar comprobante"
        }, status=500)   