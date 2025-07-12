from rest_framework import permissions

def get_systemuser_role(user):
    if hasattr(user, "systemuser") and user.systemuser:
        return user.systemuser.role
    return None

class IsAdminUser(permissions.BasePermission):
    """
    Permite acceso solo a usuarios administradores (superuser o rol Administrador).
    """
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return request.user.is_superuser or get_systemuser_role(request.user) == "Administrador"
        return False


class IsRecepcionista(permissions.BasePermission):
    """
    Permite a recepcionistas crear registros y verlos, pero no editarlos totalmente.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = get_systemuser_role(request.user)
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == "POST":
            return role == "Recepcionista"
        if request.method in ["PUT", "PATCH"]:
            return role == "Recepcionista"
        return request.user.is_superuser


class IsMecanico(permissions.BasePermission):
    """
    Permite a mecánicos modificar estados y comentarios técnicos.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        role = get_systemuser_role(request.user)
        return role == "Mecánico" or request.user.is_superuser


class IsAdminOrCanEdit(permissions.BasePermission):
    """
    Permite editar si es admin o está en grupo 'puede_editar'.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name='puede_editar').exists()
