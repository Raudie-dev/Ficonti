"""
Sesión independiente para los super administradores.

Los super administradores no usan ``request.user`` (reservado para los
contadores, tabla ``usuarios``). Este middleware expone ``request.superadmin``
a partir de la sesión.
"""

from django.utils.crypto import constant_time_compare
from django.utils.functional import SimpleLazyObject

SESSION_ID = '_superadmin_id'
SESSION_HASH = '_superadmin_hash'


def _obtener_superadmin(request):
    if not hasattr(request, '_superadmin_cache'):
        from .models import SuperAdmin

        sa = None
        pk = request.session.get(SESSION_ID)
        if pk is not None:
            try:
                candidato = SuperAdmin.objects.get(pk=pk, is_active=True)
            except SuperAdmin.DoesNotExist:
                candidato = None
            # Invalida la sesión si la clave cambió
            if candidato and constant_time_compare(
                request.session.get(SESSION_HASH, ''), candidato.get_session_auth_hash()
            ):
                sa = candidato
            else:
                request.session.pop(SESSION_ID, None)
                request.session.pop(SESSION_HASH, None)
        request._superadmin_cache = sa
    return request._superadmin_cache


def iniciar_sesion_superadmin(request, superadmin):
    request.session.cycle_key()
    request.session[SESSION_ID] = superadmin.pk
    request.session[SESSION_HASH] = superadmin.get_session_auth_hash()
    request._superadmin_cache = superadmin
    from django.utils import timezone
    superadmin.last_login = timezone.now()
    superadmin.save(update_fields=['last_login'])


def actualizar_hash_superadmin(request, superadmin):
    request.session[SESSION_HASH] = superadmin.get_session_auth_hash()


def cerrar_sesion_superadmin(request):
    request.session.pop(SESSION_ID, None)
    request.session.pop(SESSION_HASH, None)
    request.session.cycle_key()
    request._superadmin_cache = None


class SuperAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.superadmin = SimpleLazyObject(lambda: _obtener_superadmin(request))
        return self.get_response(request)
