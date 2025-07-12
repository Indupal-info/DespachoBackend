from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import (
    Branch,
    SystemUser,
    Client,
    MachineEntry,
    RepairHistory,
    CallLog,
    MachineEntryMedia,
)
from django.utils.translation import gettext_lazy as _

# --- Restricciones de estados y roles ---
STAGES = [s[0] for s in MachineEntry.STAGES]

# Inline para SystemUser al crear un User
class SystemUserInline(admin.StackedInline):
    model = SystemUser
    can_delete = False
    verbose_name_plural = 'Usuario del sistema'
    fk_name = 'user'
    autocomplete_fields = ('branch',)


class UserAdmin(BaseUserAdmin):
    inlines = (SystemUserInline,)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("codigo_sucursal", "name", "phone")
    search_fields = ("codigo_sucursal", "name")


@admin.register(SystemUser)
class SystemUserAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "role", "branch", "is_active")
    list_filter = ("role", "branch", "is_active")
    search_fields = ("name", "email")
    autocomplete_fields = ("branch", "user")


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("client_name", "registro_cliente", "telefono", "celular", "departamento", "municipio")
    search_fields = ("client_name", "registro_cliente", "telefono", "celular")


@admin.register(MachineEntry)
class MachineEntryAdmin(admin.ModelAdmin):
    list_display = ("comprobante_ingreso", "serial_number", "client", "branch", "current_stage", "arrival_date")
    list_filter = ("branch", "current_stage", "arrival_date")
    search_fields = ("comprobante_ingreso", "serial_number", "client__client_name", "codigo_producto", "descripcion_producto")
    autocomplete_fields = ("client", "branch", "ingresado_por")
    readonly_fields = ("comprobante_ingreso",)  # El comprobante es generado automáticamente

    def save_model(self, request, obj, form, change):
        user = request.user
        # Aplica reglas solo si el usuario tiene SystemUser
        if hasattr(user, 'systemuser') and change:
            old_obj = MachineEntry.objects.get(pk=obj.pk)
            old_stage_idx = STAGES.index(old_obj.current_stage)
            new_stage_idx = STAGES.index(obj.current_stage)
            role = user.systemuser.role

            # Prohibir retroceso de estado para mecánico y recepcionista
            if new_stage_idx < old_stage_idx:
                raise ValidationError("No puedes retroceder el estado de la maquinaria.")

            # Mecánico NO puede pasar a 'ENTREGADA'
            if role == 'Mecánico' and obj.current_stage == 'ENTREGADA':
                raise ValidationError("El mecánico no puede poner la maquinaria en estado ENTREGADA.")

        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        # Mecánico y Recepcionista NO pueden eliminar maquinarias
        if hasattr(request.user, 'systemuser'):
            role = request.user.systemuser.role
            if role in ['Mecánico', 'Recepcionista']:
                return False
        return super().has_delete_permission(request, obj)


@admin.register(RepairHistory)
class RepairHistoryAdmin(admin.ModelAdmin):
    list_display = ("machine_entry", "stage", "start_date", "end_date", "budget_amount", "presupuesto_id")
    list_filter = ("stage",)
    search_fields = ("machine_entry__serial_number", "presupuesto_id")
    autocomplete_fields = ("machine_entry", "mechanic", "ingresado_por")


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display = ("machine_entry", "call_date", "attended_by", "notes")
    list_filter = ("call_date",)
    search_fields = ("machine_entry__serial_number", "notes")
    autocomplete_fields = ("machine_entry", "attended_by")


@admin.register(MachineEntryMedia)
class MachineEntryMediaAdmin(admin.ModelAdmin):
    list_display = ("machine_entry", "file", "uploaded_at")
    readonly_fields = ("uploaded_at",)
    autocomplete_fields = ("machine_entry",)

    def has_delete_permission(self, request, obj=None):
        # Mecánico y Recepcionista NO pueden eliminar detalles
        if hasattr(request.user, 'systemuser'):
            role = request.user.systemuser.role
            if role in ['Mecánico', 'Recepcionista']:
                return False
        return super().has_delete_permission(request, obj)