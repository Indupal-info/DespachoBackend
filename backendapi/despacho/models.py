from datetime import timezone
from django.db import models
from django.contrib.auth.models import User
import uuid

class Branch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    codigo_sucursal = models.CharField(max_length=10, unique=True, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'branches'

    def __str__(self):
        return self.name


class SystemUser(models.Model):
    ROLES = [
        ('Recepcionista', 'Recepcionista'),
        ('Mecánico', 'Mecánico'),
        ('Técnico Líder', 'Técnico Líder'),
        ('Gerente', 'Gerente'),
        ('Administrador', 'Administrador'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='systemuser')
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=ROLES)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'systemusers'


class Client(models.Model):
    id = models.AutoField(primary_key=True)
    client_name = models.CharField(max_length=255)
    contacto = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(max_length=50, blank=True, null=True)
    celular = models.CharField(max_length=50, blank=True, null=True)
    departamento = models.CharField(max_length=100, blank=True, null=True)
    municipio = models.CharField(max_length=100, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    registro_cliente = models.CharField(max_length=50, unique=True)
    email = models.EmailField(blank=True, null=True)
    nit = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clients'
        indexes = [models.Index(fields=['registro_cliente'])]


class MachineEntry(models.Model):
    STAGES = [
        ('EN_ESPERA', 'EN ESPERA'),
        ('REVISION_TALLER', 'REVISION TALLER'),
        ('PRESUPUESTADA', 'PRESUPUESTADA'),
        ('AUTORIZADA', 'AUTORIZADA'),
        ('EN_REPARACION', 'EN REPARACION'),
        ('ENTREGADA_BODEGA', 'ENTREGADA BODEGA'),
        ('REPARADA', 'REPARADA'),
        ('ENTREGADA_CLIENTE', 'ENTREGADA CLIENTE'),
        ('NO_ACEPTADA_CLIENTE', 'NO ACEPTADA CLIENTE'),
        ('NO_AUTORIZADA', 'NO AUTORIZADA'),
        ('CLIENTE_INACTIVO', 'CLIENTE INACTIVO'),
        ('NO_HAY_REPUESTOS', 'NO HAY REPUESTOS'),
        ('REPUESTOS_SOLICITADO', 'REPUESTOS SOLICITADO'),
        ('REPUESTOS_RECIBIDOS', 'REPUESTOS RECIBIDOS'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(Branch, on_delete=models.RESTRICT)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    arrival_date = models.DateField()
    arrival_time = models.TimeField()
    comprobante_ingreso = models.CharField(max_length=20, unique=True, blank=True, null=True)
    ingresado_por = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True)
    machine_type = models.CharField(max_length=100)
    machine_model = models.CharField(max_length=100, blank=True, null=True)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    codigo_producto = models.CharField(max_length=50, blank=True, null=True)
    marca_producto = models.CharField(max_length=50, blank=True, null=True)
    descripcion_producto = models.TextField(blank=True, null=True)
    accessories = models.TextField(blank=True, null=True)
    reported_fault = models.TextField()
    observations = models.TextField(blank=True, null=True)
    current_stage = models.CharField(max_length=30, choices=STAGES)

    # Campos nuevos
    tipo_servicio = models.TextField(blank=True, null=True)
    mediciones_tecnicas = models.TextField(blank=True, null=True)
    recibido_por_nombre = models.CharField(max_length=255, blank=True, null=True)
    tipo_consumidor = models.CharField(max_length=50, blank=True, null=True)
    acepta_normativa = models.BooleanField(default=False)
    firma_cliente = models.ImageField(upload_to='firmas_clientes/', null=True, blank=True)

    # Campos de fecha por estado
    fecha_en_espera = models.DateTimeField(null=True, blank=True)
    fecha_revision_taller = models.DateTimeField(null=True, blank=True)
    fecha_presupuestada = models.DateTimeField(null=True, blank=True)
    fecha_autorizada = models.DateTimeField(null=True, blank=True)
    fecha_en_reparacion = models.DateTimeField(null=True, blank=True)
    fecha_entregada_bodega = models.DateTimeField(null=True, blank=True)
    fecha_reparada = models.DateTimeField(null=True, blank=True)
    fecha_entregada_cliente = models.DateTimeField(null=True, blank=True)
    fecha_no_aceptada_cliente = models.DateTimeField(null=True, blank=True)
    fecha_no_autorizada = models.DateTimeField(null=True, blank=True)
    fecha_cliente_inactivo = models.DateTimeField(null=True, blank=True)
    fecha_no_hay_repuestos = models.DateTimeField(null=True, blank=True)
    fecha_repuestos_solicitado = models.DateTimeField(null=True, blank=True)
    fecha_repuestos_recibidos = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.comprobante_ingreso and self.branch:
            prefix = self.branch.codigo_sucursal or "UNDEF"
            last_entry = MachineEntry.objects.filter(
                branch=self.branch,
                comprobante_ingreso__startswith=f"{prefix}-"
            ).order_by('-created_at').first()

            last_number = 0
            if last_entry and last_entry.comprobante_ingreso:
                try:
                    last_number = int(last_entry.comprobante_ingreso.replace(f"{prefix}-", ""))
                except ValueError:
                    pass

            self.comprobante_ingreso = f"{prefix}-{str(last_number + 1).zfill(5)}"

        if self.pk:
            old = MachineEntry.objects.get(pk=self.pk)
            if old.current_stage != self.current_stage:
                now = timezone.now()
                stage_field_map = {
                    'EN_ESPERA': 'fecha_en_espera',
                    'REVISION_TALLER': 'fecha_revision_taller',
                    'PRESUPUESTADA': 'fecha_presupuestada',
                    'AUTORIZADA': 'fecha_autorizada',
                    'EN_REPARACION': 'fecha_en_reparacion',
                    'ENTREGADA_BODEGA': 'fecha_entregada_bodega',
                    'REPARADA': 'fecha_reparada',
                    'ENTREGADA_CLIENTE': 'fecha_entregada_cliente',
                    'NO_ACEPTADA_CLIENTE': 'fecha_no_aceptada_cliente',
                    'NO_AUTORIZADA': 'fecha_no_autorizada',
                    'CLIENTE_INACTIVO': 'fecha_cliente_inactivo',
                    'NO_HAY_REPUESTOS': 'fecha_no_hay_repuestos',
                    'REPUESTOS_SOLICITADO': 'fecha_repuestos_solicitado',
                    'REPUESTOS_RECIBIDOS': 'fecha_repuestos_recibidos',
                }
                field_name = stage_field_map.get(self.current_stage)
                if field_name:
                    setattr(self, field_name, now)

        super().save(*args, **kwargs)

    class Meta:
        db_table = 'machineentries'
        indexes = [models.Index(fields=['serial_number'])]



class RepairHistory(models.Model):
    STAGES = MachineEntry.STAGES
    id = models.AutoField(primary_key=True)
    machine_entry = models.ForeignKey(MachineEntry, on_delete=models.CASCADE)
    stage = models.CharField(max_length=20, choices=STAGES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    mechanic = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='repair_mechanic')
    budget_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    presupuesto_id = models.CharField(max_length=50, null=True, blank=True)
    comentario_presupuesto = models.TextField(blank=True, null=True)
    ingresado_por = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='repair_creator')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'repairhistory'


class CallLog(models.Model):
    id = models.AutoField(primary_key=True)
    machine_entry = models.ForeignKey(MachineEntry, on_delete=models.CASCADE)
    call_date = models.DateTimeField()
    notes = models.TextField()
    attended_by = models.ForeignKey(SystemUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'calllogs'


class MachineEntryMedia(models.Model):
    machine_entry = models.ForeignKey(MachineEntry, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='media_maquinas/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def is_image(self):
        return self.file.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))

    def is_video(self):
        return self.file.name.lower().endswith(('.mp4', '.avi', '.mov'))

    class Meta:
        db_table = 'machineentrymedia'
