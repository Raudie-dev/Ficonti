from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from .middleware import _obtener_superadmin


def obtener_superadmin(request):
    return _obtener_superadmin(request)


class SuperAdminRequiredMixin:
    """Restringe la vista a super administradores con sesión iniciada."""

    def dispatch(self, request, *args, **kwargs):
        self.superadmin = obtener_superadmin(request)
        if self.superadmin is None:
            messages.warning(request, 'Inicie sesión como super administrador para continuar.')
            return redirect(f"{reverse('superadmin:login')}?next={request.get_full_path()}")
        return super().dispatch(request, *args, **kwargs)


def superadmin_required(view):
    @wraps(view)
    def _wrapped(request, *args, **kwargs):
        if obtener_superadmin(request) is None:
            messages.warning(request, 'Inicie sesión como super administrador para continuar.')
            return redirect(f"{reverse('superadmin:login')}?next={request.get_full_path()}")
        return view(request, *args, **kwargs)
    return _wrapped
