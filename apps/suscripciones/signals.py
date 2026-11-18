from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Suscripcion


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def crear_suscripcion(sender, instance, created, **kwargs):
    """Todo contador nuevo arranca con una suscripción pendiente de activación."""
    if created:
        Suscripcion.objects.get_or_create(usuario=instance)
