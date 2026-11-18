from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

from apps.suscripciones.models import ConfiguracionPago


class ContadorRequiredMixin(LoginRequiredMixin):
    """Vista exclusiva de usuarios normales (contadores) con sesión iniciada."""


class SuscripcionRequeridaMixin:
    """Muestra la pantalla de cuenta bloqueada si la mensualidad no está al día."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not request.user.suscripcion_activa:
            return render_bloqueado(request)
        return super().dispatch(request, *args, **kwargs)


def render_bloqueado(request, template='modulos/bloqueado.html'):
    return render(request, template, {
        'config_pago': ConfiguracionPago.obtener(),
        'suscripcion': getattr(request.user, 'suscripcion', None),
    })
