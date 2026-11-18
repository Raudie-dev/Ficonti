from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import url_has_allowed_host_and_scheme, urlsafe_base64_decode, urlsafe_base64_encode
from django.views.decorators.http import require_POST

from apps.core.utils import ControlIntentos
from apps.suscripciones.models import ConfiguracionPago

from .forms import (
    CambiarClaveForm,
    LoginForm,
    PerfilForm,
    RecuperarClaveMailForm,
    RegistroForm,
    RestablecerClaveForm,
)
from .models import Usuario


def _siguiente(request, defecto='core:inicio'):
    nxt = request.POST.get('next') or request.GET.get('next')
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return nxt
    return defecto


def login_view(request):
    """Ingreso de usuarios (contadores, administradores, economistas)."""
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
    """Registro de usuario con Usuario, Clave y Correo electrónico para recuperación."""
    if request.user.is_authenticated:
        return redirect('core:inicio')
    form = RegistroForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Cuenta creada correctamente. Registre su primera empresa para activar los módulos.')
            return redirect('core:inicio')
        messages.error(request, 'Revise los datos del formulario.')
    return render(request, 'usuarios/registro.html', {'form': form})


def recuperar_view(request):
    """Recuperación de clave por correo electrónico."""
    form = RecuperarClaveMailForm(request.POST or None)
    enlace_recuperacion = None
    enviado = False
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email'].strip().lower()
        usuario_txt = (form.cleaned_data.get('usuario') or '').strip().lower()
        qs = Usuario.objects.filter(email__iexact=email, is_active=True)
        if usuario_txt:
            qs = qs.filter(usuario__iexact=usuario_txt)
        user = qs.first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            path_reset = reverse('usuarios:restablecer_clave', kwargs={'uidb64': uid, 'token': token})
            enlace_recuperacion = request.build_absolute_uri(path_reset)
            try:
                send_mail(
                    subject='Recuperación de clave · Gestión Fiscal Venezuela',
                    message=(
                        f'Hola {user.nombre_mostrar},\n\n'
                        f'Recibimos una solicitud para restablecer la clave de su usuario «{user.usuario}».\n'
                        f'Abra el siguiente enlace para crear una nueva clave:\n\n{enlace_recuperacion}\n'
                    ),
                    from_email='no-reply@tributove.local',
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception:
                pass
            enviado = True
            messages.success(request, f'Se generaron las instrucciones de recuperación para {email}.')
        else:
            messages.error(request, 'No encontramos una cuenta activa asociada a ese correo electrónico.')
    return render(request, 'usuarios/recuperar.html', {
        'form': form,
        'enviado': enviado,
        'enlace_recuperacion': enlace_recuperacion,
        'config_pago': ConfiguracionPago.obtener(),
    })


def restablecer_clave_view(request, uidb64, token):
    """Permite definir una nueva clave mediante el enlace enviado al correo."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid, is_active=True)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None

    token_valido = user is not None and default_token_generator.check_token(user, token)
    form = RestablecerClaveForm(request.POST or None)

    if token_valido and request.method == 'POST' and form.is_valid():
        form._validar_clave(user)
        if not form.errors:
            user.set_password(form.cleaned_data['clave1'])
            user.save()
            messages.success(request, 'Su clave ha sido actualizada. Ya puede iniciar sesión.')
            return redirect('usuarios:login')

    return render(request, 'usuarios/restablecer.html', {
        'form': form,
        'token_valido': token_valido,
        'usuario_obj': user,
    })


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
