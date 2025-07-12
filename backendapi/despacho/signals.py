from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import SystemUser, Branch
import uuid

@receiver(post_save, sender=User)
def create_user_profiles(sender, instance, created, **kwargs):
    if created:
        # Crear una sucursal predeterminada si no existe ninguna
        branch = Branch.objects.first()
        if not branch:
            branch = Branch.objects.create(
                id=str(uuid.uuid4()),
                name="Sucursal Principal",
                codigo_sucursal="PRINC",
                phone="",
                address=""
            )

        # Crear SystemUser solo si no existe ya
        if not hasattr(instance, 'systemuser'):
            SystemUser.objects.create(
                user=instance,
                name=instance.get_full_name() or instance.username,
                email=instance.email,
                role="Administrador",  # Puedes cambiar esto dinámicamente si lo deseas
                branch=branch,
                is_active=True,
            )
