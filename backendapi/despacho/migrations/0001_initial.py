# Generated by Django 5.0.14 on 2025-06-30 22:02

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Branch',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('codigo_sucursal', models.CharField(blank=True, max_length=10, null=True, unique=True)),
                ('address', models.TextField(blank=True, null=True)),
                ('phone', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'branches',
            },
        ),
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('client_name', models.CharField(max_length=255)),
                ('contacto', models.CharField(blank=True, max_length=255, null=True)),
                ('telefono', models.CharField(blank=True, max_length=50, null=True)),
                ('celular', models.CharField(blank=True, max_length=50, null=True)),
                ('departamento', models.CharField(blank=True, max_length=100, null=True)),
                ('municipio', models.CharField(blank=True, max_length=100, null=True)),
                ('direccion', models.TextField(blank=True, null=True)),
                ('registro_cliente', models.CharField(max_length=50, unique=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('nit', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'clients',
                'indexes': [models.Index(fields=['registro_cliente'], name='clients_registr_08f18d_idx')],
            },
        ),
        migrations.CreateModel(
            name='MachineEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('arrival_date', models.DateField()),
                ('arrival_time', models.TimeField()),
                ('comprobante_ingreso', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ('machine_type', models.CharField(max_length=100)),
                ('machine_model', models.CharField(blank=True, max_length=100, null=True)),
                ('serial_number', models.CharField(blank=True, max_length=100, null=True)),
                ('codigo_producto', models.CharField(blank=True, max_length=50, null=True)),
                ('marca_producto', models.CharField(blank=True, max_length=50, null=True)),
                ('descripcion_producto', models.TextField(blank=True, null=True)),
                ('accessories', models.TextField(blank=True, null=True)),
                ('reported_fault', models.TextField()),
                ('observations', models.TextField(blank=True, null=True)),
                ('current_stage', models.CharField(choices=[('INGRESADO', 'INGRESADO'), ('INICIAR_REVISION', 'INICIAR_REVISION'), ('PRESUPUESTADO', 'PRESUPUESTADO'), ('AUTORIZADO', 'AUTORIZADO'), ('NO_AUTORIZADO', 'NO_AUTORIZADO'), ('MSPR_ACTIVO', 'MSPR_ACTIVO'), ('INICIO_REPARACION', 'INICIO_REPARACION'), ('FIN_REPARACION', 'FIN_REPARACION'), ('ENTREGADA', 'ENTREGADA')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('branch', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='despacho.branch')),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='despacho.client')),
            ],
            options={
                'db_table': 'machineentries',
            },
        ),
        migrations.CreateModel(
            name='MachineEntryMedia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='media_maquinas/%Y/%m/%d/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('machine_entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media', to='despacho.machineentry')),
            ],
            options={
                'db_table': 'machineentrymedia',
            },
        ),
        migrations.CreateModel(
            name='SystemUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('role', models.CharField(choices=[('Recepcionista', 'Recepcionista'), ('Mecánico', 'Mecánico'), ('Técnico Líder', 'Técnico Líder'), ('Gerente', 'Gerente'), ('Administrador', 'Administrador')], max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('branch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='despacho.branch')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='systemuser', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'systemusers',
            },
        ),
        migrations.CreateModel(
            name='RepairHistory',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('stage', models.CharField(choices=[('INGRESADO', 'INGRESADO'), ('INICIAR_REVISION', 'INICIAR_REVISION'), ('PRESUPUESTADO', 'PRESUPUESTADO'), ('AUTORIZADO', 'AUTORIZADO'), ('NO_AUTORIZADO', 'NO_AUTORIZADO'), ('MSPR_ACTIVO', 'MSPR_ACTIVO'), ('INICIO_REPARACION', 'INICIO_REPARACION'), ('FIN_REPARACION', 'FIN_REPARACION'), ('ENTREGADA', 'ENTREGADA')], max_length=20)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('budget_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('presupuesto_id', models.CharField(blank=True, max_length=50, null=True)),
                ('comentario_presupuesto', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('machine_entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='despacho.machineentry')),
                ('ingresado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repair_creator', to='despacho.systemuser')),
                ('mechanic', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repair_mechanic', to='despacho.systemuser')),
            ],
            options={
                'db_table': 'repairhistory',
            },
        ),
        migrations.AddField(
            model_name='machineentry',
            name='ingresado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='despacho.systemuser'),
        ),
        migrations.CreateModel(
            name='CallLog',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('call_date', models.DateTimeField()),
                ('notes', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('machine_entry', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='despacho.machineentry')),
                ('attended_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='despacho.systemuser')),
            ],
            options={
                'db_table': 'calllogs',
            },
        ),
        migrations.AddIndex(
            model_name='machineentry',
            index=models.Index(fields=['serial_number'], name='machineentr_serial__1a0d1a_idx'),
        ),
    ]
