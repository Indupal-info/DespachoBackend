from django.contrib.auth.models import User
from rest_framework import serializers
from .models import (
    Branch,
    Client,
    SystemUser,
    MachineEntry,
    RepairHistory,
    CallLog,
    MachineEntryMedia
)


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'


class SystemUserSerializer(serializers.ModelSerializer):
    branch_id = serializers.UUIDField(source='branch.id', read_only=True)

    class Meta:
        model = SystemUser
        fields = ['id', 'name', 'email', 'role', 'is_active', 'branch_id']


class SystemUserCreateSerializer(serializers.Serializer):
    # Campos para el modelo User
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    # Campos para SystemUser
    name = serializers.CharField()
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=SystemUser.ROLES)
    branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), allow_null=True, required=False)
    is_active = serializers.BooleanField(default=True)

    def create(self, validated_data):
        username = validated_data['username']
        password = validated_data['password']
        name = validated_data['name']
        email = validated_data['email']
        role = validated_data['role']
        branch = validated_data.get('branch', None)
        is_active = validated_data.get('is_active', True)

        # Crear el usuario base de Django
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            is_active=is_active
        )
        # Crear el perfil SystemUser
        system_user = SystemUser.objects.create(
            user=user,
            name=name,
            email=email,
            role=role,
            branch=branch,
            is_active=is_active
        )
        return system_user

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'username': instance.user.username,
            'name': instance.name,
            'email': instance.email,
            'role': instance.role,
            'branch': str(instance.branch.id) if instance.branch else None,
            'is_active': instance.is_active,
        }


class MachineEntryMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MachineEntryMedia
        fields = ['id', 'file', 'uploaded_at']


class MachineEntrySerializer(serializers.ModelSerializer):
    media = MachineEntryMediaSerializer(many=True, read_only=True)
    comprobante_ingreso = serializers.CharField(read_only=True)

    class Meta:
        model = MachineEntry
        fields = '__all__'
        depth = 1


class RepairHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RepairHistory
        fields = '__all__'


class CallLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallLog
        fields = '__all__'


class MachineEntryDashboardSerializer(serializers.ModelSerializer):
    cliente = serializers.CharField(source='client.client_name')
    estado = serializers.CharField(source='current_stage')
    fecha_ingreso = serializers.DateField(source='arrival_date', format="%Y-%m-%d")
    serie = serializers.CharField(source='serial_number')
    sucursal = serializers.SerializerMethodField()
    branchId = serializers.SerializerMethodField()
    tipo_maquina = serializers.SerializerMethodField()
    fecha_ultimo_estado = serializers.SerializerMethodField()

    def get_sucursal(self, obj):
        return obj.branch.name if obj.branch else "N/A"

    def get_branchId(self, obj):
        return str(obj.branch.id) if obj.branch else None

    def get_tipo_maquina(self, obj):
        return f"{obj.machine_type} {obj.machine_model or ''}".strip()

    def get_fecha_ultimo_estado(self, obj):
        latest_history = obj.repairhistory_set.order_by('-start_date').first()
        return latest_history.start_date.date() if latest_history else None

    class Meta:
        model = MachineEntry
        fields = [
            'id', 'cliente', 'estado', 'fecha_ingreso',
            'serie', 'sucursal', 'branchId', 'tipo_maquina', 'fecha_ultimo_estado'
        ]


class ClientDetailsSerializer(serializers.ModelSerializer):
    clientName = serializers.CharField(source='client_name')
    registroCliente = serializers.CharField(source='registro_cliente')

    class Meta:
        model = Client
        fields = [
            'clientName',
            'contacto',
            'telefono',
            'celular',
            'departamento',
            'municipio',
            'direccion',
            'registroCliente',
            'email',
            'nit',
        ]


class MachineEntryDashboardFullSerializer(serializers.ModelSerializer):
    cliente = ClientDetailsSerializer(source='client', read_only=True)
    sucursal = serializers.CharField(source='branch.name', read_only=True)
    branchId = serializers.CharField(source='branch.id', read_only=True)
    ingresado_por = serializers.CharField(source='ingresado_por.name', default="Sistema", read_only=True)
    comprobante = serializers.CharField(source='comprobante_ingreso', read_only=True)
    tipo_maquina = serializers.SerializerMethodField()
    fecha_ultimo_estado = serializers.SerializerMethodField()
    media = MachineEntryMediaSerializer(many=True, read_only=True)
    fecha_ingreso = serializers.DateField(source='arrival_date', format="%Y-%m-%d", read_only=True)

    class Meta:
        model = MachineEntry
        fields = [
            'id',
            'comprobante',
            'cliente',
            'sucursal',
            'branchId',
            'fecha_ingreso',
            'arrival_time',
            'ingresado_por',
            'tipo_maquina',
            'machine_type',
            'machine_model',
            'serial_number',
            'codigo_producto',
            'marca_producto',
            'descripcion_producto',
            'accessories',
            'reported_fault',
            'observations',
            'current_stage',
            'fecha_ultimo_estado',
            'media'
        ]

    def get_tipo_maquina(self, obj):
        return f"{obj.machine_type} {obj.machine_model or ''}".strip()

    def get_fecha_ultimo_estado(self, obj):
        latest_history = obj.repairhistory_set.order_by('-start_date').first()
        return latest_history.start_date.date() if latest_history else None

