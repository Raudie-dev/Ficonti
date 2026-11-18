from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.core.utils import ControlIntentos
from apps.suscripciones.models import ConfiguracionPago

from .forms import CambiarClaveForm, LoginForm, PerfilForm, RegistroForm


def _siguiente(request, defecto='core:inicio'):
    nxt = request.POST.get('next') or request.GET.get('next')
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return nxt
    return defecto


def login_view(request):
    """Ingreso de usuarios normales (contadores)."""
    if request.user.is_authenticated:
        return redirect('core:inicio')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.cleaned_data['usuario'].strip().lower()
        control = ControlIntentos(request, 'usuario', usuario)
        if control.bloqueado:
            messages.error(request, 'Demasiados intentos. Espere unos segundos e intente de nuevo.')
        else:
            user = authenticate(request, username=usuario, password=form.cleaned_data['clave'])
            if user is not None:
                control.exito()
                login(request, user)
                messages.success(request, f'Bienvenido, {user.get_short_name()}.')
                if not user.suscripcion_activa:
                    messages.warning(request, 'Su suscripción no está activa. Revise las instrucciones de pago.')
                return redirect(_siguiente(request))
            control.fallo()
            messages.error(request, 'Usuario o clave incorrectos.')
    return render(request, 'usuarios/login.html', {'form': form, 'next': request.GET.get('next', '')})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('usuarios:login')


def registro_view(request):
    """Registro de un contador nuevo. Queda pendiente hasta que un super admin lo active."""
    if request.user.is_authenticated:
        return redirect('core:inicio')
    form = RegistroForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Cuenta creada. Un administrador la activará cuando se registre su mensualidad.')
            return redirect('core:inicio')
        messages.error(request, 'Revise los datos del formulario.')
    return render(request, 'usuarios/registro.html', {'form': form})


def recuperar_view(request):
    """Las claves de los contadores las restablece el super administrador."""
    return render(request, 'usuarios/recuperar.html', {'config_pago': ConfiguracionPago.obtener()})


@login_required
def mi_cuenta_view(request):
    perfil_form = PerfilForm(instance=request.user, prefix='perfil')
    clave_form = CambiarClaveForm(request.user, prefix='clave')
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'perfil':
            perfil_form = PerfilForm(request.POST, instance=request.user, prefix='perfil')
            if perfil_form.is_valid():
                perfil_form.save()
                messages.success(request, 'Datos actualizados.')
                return redirect('usuarios:mi_cuenta')
            messages.error(request, 'Revise los datos del perfil.')
        elif accion == 'clave':
            clave_form = CambiarClaveForm(request.user, request.POST, prefix='clave')
            if clave_form.is_valid():
                user = clave_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Clave actualizada.')
                return redirect('usuarios:mi_cuenta')
            messages.error(request, 'No se pudo cambiar la clave. Revise los campos.')
    return render(request, 'usuarios/mi_cuenta.html', {
        'perfil_form': perfil_form,
        'clave_form': clave_form,
        'suscripcion': getattr(request.user, 'suscripcion', None),
        'config_pago': ConfiguracionPago.obtener(),
    })
