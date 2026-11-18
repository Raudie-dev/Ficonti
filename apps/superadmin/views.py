from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.core.utils import ControlIntentos
from apps.empresas.models import Empresa
from apps.empresas.views import construir_resumen, totales_resumen
from apps.suscripciones.models import ConfiguracionPago, MODULOS_DISPONIBLES, Pago, PlanSuscripcion, Suscripcion
from apps.usuarios.models import Usuario

from .forms import (
    CambiarClaveSuperAdminForm, ConciliarPagoGlobalForm, ConfiguracionPagoForm, ContadorCrearForm,
    ContadorEditarForm, PagoForm, PlanSuscripcionForm, RestablecerClaveForm, SuperAdminCrearForm, SuperAdminEditarForm,
    SuperAdminLoginForm, SuscripcionForm,
)
from .middleware import actualizar_hash_superadmin, cerrar_sesion_superadmin, iniciar_sesion_superadmin
from .mixins import obtener_superadmin, superadmin_required
from .models import SuperAdmin


# ---------------------------------------------------------------------------
# Sesión
# ---------------------------------------------------------------------------
def login_admin(request):
    """Ingreso de super administradores (tabla independiente)."""
    if obtener_superadmin(request) is not None:
        return redirect('superadmin:panel')
    form = SuperAdminLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.cleaned_data['usuario'].strip().lower()
        control = ControlIntentos(request, 'superadmin', usuario)
        if control.bloqueado:
            messages.error(request, 'Demasiados intentos. Espere unos segundos e intente de nuevo.')
        else:
            sa = SuperAdmin.objects.filter(usuario__iexact=usuario, is_active=True).first()
            if sa and sa.check_password(form.cleaned_data['clave']):
                control.exito()
                iniciar_sesion_superadmin(request, sa)
                messages.success(request, f'Bienvenido, {sa.nombre}.')
                nxt = request.POST.get('next') or ''
                if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
                    return redirect(nxt)
                return redirect('superadmin:panel')
            control.fallo()
            messages.error(request, 'Usuario o clave incorrectos.')
    return render(request, 'superadmin/login.html', {'form': form, 'next': request.GET.get('next', '')})


@require_POST
def logout_admin(request):
    cerrar_sesion_superadmin(request)
    messages.info(request, 'Sesión de administrador cerrada.')
    return redirect('superadmin:login')


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------
def _kpis():
    hoy = timezone.localdate()
    contadores = Usuario.objects.count()
    activos = Suscripcion.objects.filter(activo=True).filter(Q(vence__isnull=True) | Q(vence__gte=hoy)).count()
    cobrado = (Pago.objects.filter(fecha__year=hoy.year, fecha__month=hoy.month)
               .values('moneda').annotate(total=Sum('monto')).order_by('moneda'))
    return {
        'contadores': contadores,
        'activos': activos,
        'inactivos': contadores - activos,
        'empresas': Empresa.objects.count(),
        'cobrado_mes': list(cobrado),
    }


@superadmin_required
def panel(request):
    hoy = timezone.localdate()
    por_vencer = (Suscripcion.objects.select_related('usuario')
                  .filter(activo=True, vence__isnull=False, vence__gte=hoy, vence__lte=hoy + timezone.timedelta(days=7))
                  .order_by('vence'))
    pendientes = (Usuario.objects.select_related('suscripcion')
                  .filter(Q(suscripcion__activo=False) | Q(suscripcion__vence__lt=hoy))
                  .order_by('-creado')[:8])
    return render(request, 'superadmin/panel.html', {
        'kpis': _kpis(),
        'por_vencer': por_vencer,
        'pendientes': pendientes,
        'ultimos_pagos': Pago.objects.select_related('suscripcion__usuario', 'registrado_por')[:8],
        'config_pago': ConfiguracionPago.obtener(),
    })


# ---------------------------------------------------------------------------
# Contadores (usuarios normales)
# ---------------------------------------------------------------------------
@superadmin_required
def contadores(request):
    hoy = timezone.localdate()
    q = request.GET.get('q', '').strip()
    estado = request.GET.get('estado', '')
    qs = Usuario.objects.select_related('suscripcion').annotate(n_empresas=Count('empresas'))
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(usuario__icontains=q) | Q(telefono__icontains=q) | Q(email__icontains=q))
    vigente = Q(suscripcion__activo=True) & (Q(suscripcion__vence__isnull=True) | Q(suscripcion__vence__gte=hoy))
    if estado == 'activo':
        qs = qs.filter(vigente)
    elif estado == 'vencido':
        qs = qs.filter(suscripcion__vence__lt=hoy)
    elif estado == 'pendiente':
        qs = qs.exclude(vigente).filter(suscripcion__vence__isnull=True)
    elif estado == 'deshabilitado':
        qs = qs.filter(is_active=False)
    config = ConfiguracionPago.obtener()
    return render(request, 'superadmin/contadores/lista.html', {
        'contadores': qs, 'q': q, 'estado': estado, 'kpis': _kpis(),
        'pago_form': PagoForm(initial={'monto': config.monto or 0, 'moneda': config.moneda, 'dias': 30}),
    })


@superadmin_required
def contador_crear(request):
    form = ContadorCrearForm(request.POST or None, initial={'is_active': True})
    if request.method == 'POST':
        if form.is_valid():
            user = form.save(commit=False)
            user.creado_por = obtener_superadmin(request)
            user.save()
            if form.cleaned_data.get('activar'):
                Suscripcion.objects.filter(usuario=user).update(activo=True, vence=None)
            messages.success(request, f'Contador «{user.nombre}» creado.')
            return redirect('superadmin:contador_detalle', pk=user.pk)
        messages.error(request, 'Revise los datos del contador.')
    return render(request, 'superadmin/contadores/form.html', {'form': form, 'titulo': 'Nuevo contador'})


@superadmin_required
def contador_detalle(request, pk):
    contador = get_object_or_404(Usuario.objects.select_related('suscripcion'), pk=pk)
    suscripcion, _ = Suscripcion.objects.get_or_create(usuario=contador)
    config = ConfiguracionPago.obtener()
    return render(request, 'superadmin/contadores/detalle.html', {
        'contador': contador,
        'suscripcion': suscripcion,
        'empresas': contador.empresas.order_by('-creado'),
        'pagos': suscripcion.pagos.select_related('registrado_por'),
        'sus_form': SuscripcionForm(initial={'activo': suscripcion.activo, 'vence': suscripcion.vence,
                                             'nota': suscripcion.nota}),
        'pago_form': PagoForm(initial={'monto': config.monto or 10, 'moneda': config.moneda, 'dias': 30, 'metodo': 'pago_movil'}),
        'clave_form': RestablecerClaveForm(usuario=contador),
    })


@superadmin_required
def contador_editar(request, pk):
    contador = get_object_or_404(Usuario, pk=pk)
    form = ContadorEditarForm(request.POST or None, instance=contador)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Datos del contador actualizados.')
            return redirect('superadmin:contador_detalle', pk=contador.pk)
        messages.error(request, 'Revise los datos del contador.')
    return render(request, 'superadmin/contadores/form.html', {
        'form': form, 'titulo': f'Editar a {contador.nombre}', 'contador': contador,
    })


@require_POST
@superadmin_required
def contador_clave(request, pk):
    contador = get_object_or_404(Usuario, pk=pk)
    form = RestablecerClaveForm(request.POST, usuario=contador)
    if form.is_valid():
        contador.set_password(form.cleaned_data['clave1'])
        contador.save(update_fields=['password'])
        messages.success(request, f'Clave de {contador.nombre} restablecida.')
    else:
        errores = '; '.join(e for errs in form.errors.values() for e in errs)
        messages.error(request, f'No se pudo restablecer la clave: {errores}')
    return redirect('superadmin:contador_detalle', pk=contador.pk)


@require_POST
@superadmin_required
def contador_eliminar(request, pk):
    contador = get_object_or_404(Usuario, pk=pk)
    nombre = contador.nombre
    contador.delete()
    messages.success(request, f'Contador «{nombre}» eliminado junto con sus empresas.')
    return redirect('superadmin:contadores')


@require_POST
@superadmin_required
def contador_suscripcion(request, pk):
    contador = get_object_or_404(Usuario, pk=pk)
    sus, _ = Suscripcion.objects.get_or_create(usuario=contador)
    form = SuscripcionForm(request.POST)
    if form.is_valid():
        sus.activo = form.cleaned_data['activo']
        sus.vence = form.cleaned_data['vence']
        sus.nota = form.cleaned_data['nota']
        sus.save()
        messages.success(request, f'Suscripción de {contador.nombre}: {sus.estado}.')
    else:
        messages.error(request, 'Datos de suscripción inválidos.')
    return _volver(request, 'superadmin:contador_detalle', pk=contador.pk)


@require_POST
@superadmin_required
def contador_alternar(request, pk):
    """Activa o suspende la suscripción (botón rápido)."""
    contador = get_object_or_404(Usuario, pk=pk)
    sus, _ = Suscripcion.objects.get_or_create(usuario=contador)
    if sus.vigente:
        sus.activo = False
        messages.warning(request, f'Suscripción de {contador.nombre} suspendida.')
    else:
        sus.activo = True
        if sus.vence and sus.vence < timezone.localdate():
            sus.vence = None
        messages.success(request, f'Suscripción de {contador.nombre} activada.')
    sus.save()
    return _volver(request, 'superadmin:contadores')


@require_POST
@superadmin_required
def contador_pago(request, pk):
    contador = get_object_or_404(Usuario, pk=pk)
    sus, _ = Suscripcion.objects.get_or_create(usuario=contador)
    form = PagoForm(request.POST)
    if form.is_valid():
        d = form.cleaned_data
        sus.registrar_pago(
            d['monto'], d['moneda'], d['dias'], obtener_superadmin(request),
            nota=d.get('nota', ''), referencia=d.get('referencia', ''), metodo=d.get('metodo', 'pago_movil'),
        )
        messages.success(request, f'Pago registrado. La suscripción de {contador.nombre} vence el {sus.vence:%d/%m/%Y}.')
    else:
        messages.error(request, 'Datos del pago inválidos.')
    return _volver(request, 'superadmin:contador_detalle', pk=contador.pk)


def _volver(request, defecto, **kwargs):
    nxt = request.POST.get('next')
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return redirect(nxt)
    return redirect(defecto, **kwargs)


# ---------------------------------------------------------------------------
# Empresas y estatus de todos los contadores
# ---------------------------------------------------------------------------
@superadmin_required
def empresas(request):
    usuario = request.GET.get('usuario', '')
    q = request.GET.get('q', '').strip()
    qs = Empresa.objects.select_related('usuario').order_by('usuario__nombre', 'nombre')
    if usuario:
        qs = qs.filter(usuario_id=usuario)
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(rif__icontains=q))
    return render(request, 'superadmin/empresas.html', {
        'empresas': qs, 'contadores': Usuario.objects.order_by('nombre'), 'usuario_sel': usuario, 'q': q,
    })


@superadmin_required
def estatus(request):
    usuario = request.GET.get('usuario', '')
    q = request.GET.get('q', '').strip()
    filtro = request.GET.get('f', 'todas')
    orden = request.GET.get('o', 'nombre')
    qs = Empresa.objects.select_related('usuario').prefetch_related('estados')
    if usuario:
        qs = qs.filter(usuario_id=usuario)
    todas = list(qs)
    compacta = request.GET.get('c', '1' if len(todas) > 30 else '0') == '1'
    return render(request, 'superadmin/estatus.html', {
        'filas': construir_resumen(todas, q, filtro, orden), 'total_empresas': len(todas),
        'totales': totales_resumen(todas), 'contadores': Usuario.objects.order_by('nombre'),
        'usuario_sel': usuario, 'q': q, 'f': filtro, 'o': orden, 'compacta': compacta,
    })


# ---------------------------------------------------------------------------
# Pagos, Conciliación y Configuración de Planes
# ---------------------------------------------------------------------------
@superadmin_required
def pagos(request):
    config = ConfiguracionPago.obtener()
    pago_form = ConciliarPagoGlobalForm(request.POST or None, initial={
        'monto': config.monto or 10,
        'moneda': config.moneda,
        'dias': 30,
        'metodo': 'pago_movil',
    })
    if request.method == 'POST' and 'conciliar_pago' in request.POST:
        if pago_form.is_valid():
            d = pago_form.cleaned_data
            contador = d['contador']
            sus, _ = Suscripcion.objects.get_or_create(usuario=contador)
            sus.registrar_pago(
                d['monto'], d['moneda'], d['dias'], obtener_superadmin(request),
                nota=d.get('nota', ''), referencia=d.get('referencia', ''), metodo=d.get('metodo', 'pago_movil'),
                plan=d.get('plan'), ciclo=d.get('ciclo', 'mensual'), estado='aprobado',
            )
            messages.success(request, f'Pago aprobado y registrado para {contador.nombre}. Suscripción vigente hasta {sus.vence:%d/%m/%Y}.')
            return redirect('superadmin:pagos')
        messages.error(request, 'Revise los datos del formulario de registro de pago.')

    base_qs = Pago.objects.select_related('suscripcion__usuario', 'plan', 'registrado_por')

    # Estadísticas para las 4 KPI cards superiores exactas a la imagen
    kpis_pagos = {
        'pendientes': base_qs.filter(estado='pendiente').count(),
        'aprobados': base_qs.filter(estado='aprobado').count(),
        'rechazados': base_qs.filter(estado='rechazado').count(),
        'total_recaudado': base_qs.filter(estado='aprobado').aggregate(t=Sum('monto'))['t'] or Decimal('0.00'),
    }

    # Filtros por estado (Todos, Pendientes, Aprobados, Rechazados) y búsqueda
    estado_filtro = request.GET.get('estado', '').strip()
    q = request.GET.get('q', '').strip()

    lista = base_qs
    if estado_filtro in ('pendiente', 'aprobado', 'rechazado'):
        lista = lista.filter(estado=estado_filtro)

    if q:
        lista = lista.filter(
            Q(referencia__icontains=q) |
            Q(nota__icontains=q) |
            Q(suscripcion__usuario__nombre__icontains=q) |
            Q(suscripcion__usuario__usuario__icontains=q) |
            Q(suscripcion__usuario__email__icontains=q) |
            Q(plan__nombre__icontains=q)
        )

    return render(request, 'superadmin/pagos.html', {
        'pago_form': pago_form,
        'pagos': lista[:300],
        'kpis_pagos': kpis_pagos,
        'estado_filtro': estado_filtro,
        'q': q,
        'config': config,
    })


@require_POST
@superadmin_required
def pago_aprobar(request, pk):
    pago = get_object_or_404(Pago, pk=pk)
    pago.aprobar(admin=obtener_superadmin(request))
    messages.success(request, f'Pago de {pago.suscripcion.usuario.nombre} aprobado. Suscripción extendida por {pago.dias} días.')
    return _volver(request, 'superadmin:pagos')


@require_POST
@superadmin_required
def pago_rechazar(request, pk):
    pago = get_object_or_404(Pago, pk=pk)
    motivo = request.POST.get('motivo', '').strip()
    pago.rechazar(admin=obtener_superadmin(request), motivo=motivo)
    messages.warning(request, f'Pago de {pago.suscripcion.usuario.nombre} marcado como rechazado.')
    return _volver(request, 'superadmin:pagos')


def _inicializar_planes_por_defecto():
    if PlanSuscripcion.objects.exists():
        return
    todos_modulos = [k for k, _ in MODULOS_DISPONIBLES]
    pack_inicial = ['planificacion', 'retenciones_islr', 'retenciones_iva', 'calendario', 'conciliacion', 'cedula_fiscal']

    PlanSuscripcion.objects.create(
        nombre='Plan Inicial',
        codigo='STARTER',
        etiqueta_badge='STARTER',
        precio_mensual=Decimal('10.00'),
        precio_anual=Decimal('80.00'),
        limite_usuarios=3,
        limite_empresas=1,
        mostrar_en_landing=True,
        api_propia=True,
        modulos=pack_inicial,
        orden=1,
    )
    PlanSuscripcion.objects.create(
        nombre='Plan Profesional',
        codigo='PRO',
        etiqueta_badge='PRO',
        precio_mensual=Decimal('20.00'),
        precio_anual=Decimal('220.00'),
        limite_usuarios=10,
        limite_empresas=2,
        mostrar_en_landing=True,
        api_propia=True,
        modulos=todos_modulos,
        orden=2,
    )
    PlanSuscripcion.objects.create(
        nombre='Plan Corporativo',
        codigo='ENTERPRISE',
        etiqueta_badge='ENTERPRISE',
        precio_mensual=Decimal('30.00'),
        precio_anual=Decimal('560.00'),
        limite_usuarios=0,
        limite_empresas=0,
        mostrar_en_landing=True,
        incluye_ia=True,
        api_propia=True,
        modulos=todos_modulos,
        orden=3,
    )
    PlanSuscripcion.objects.create(
        nombre='testing',
        codigo='TEST',
        etiqueta_badge='TEST',
        precio_mensual=Decimal('0.20'),
        precio_anual=Decimal('0.00'),
        limite_usuarios=200,
        limite_empresas=100,
        mostrar_en_landing=False,
        incluye_ia=True,
        api_propia=False,
        modulos=todos_modulos,
        orden=4,
    )


@superadmin_required
def planes_configuracion(request):
    _inicializar_planes_por_defecto()
    planes = PlanSuscripcion.objects.filter(activo=True).order_by('orden', 'precio_mensual')
    config = ConfiguracionPago.obtener()
    config_form = ConfiguracionPagoForm(instance=config)
    plan_form = PlanSuscripcionForm()

    return render(request, 'superadmin/planes.html', {
        'planes': planes,
        'config': config,
        'config_form': config_form,
        'plan_form': plan_form,
        'modulos_disponibles': MODULOS_DISPONIBLES,
    })


@require_POST
@superadmin_required
def plan_crear(request):
    form = PlanSuscripcionForm(request.POST)
    if form.is_valid():
        plan = form.save()
        messages.success(request, f'Plan «{plan.nombre}» creado exitosamente.')
    else:
        errores = '; '.join(f'{f}: {e[0]}' for f, e in form.errors.items())
        messages.error(request, f'No se pudo crear el plan: {errores}')
    return redirect('superadmin:planes')


@require_POST
@superadmin_required
def plan_editar(request, pk):
    plan = get_object_or_404(PlanSuscripcion, pk=pk)
    form = PlanSuscripcionForm(request.POST, instance=plan)
    if form.is_valid():
        form.save()
        messages.success(request, f'Plan «{plan.nombre}» actualizado correctamente.')
    else:
        errores = '; '.join(f'{f}: {e[0]}' for f, e in form.errors.items())
        messages.error(request, f'No se pudo actualizar el plan: {errores}')
    return redirect('superadmin:planes')


@require_POST
@superadmin_required
def plan_eliminar(request, pk):
    plan = get_object_or_404(PlanSuscripcion, pk=pk)
    nombre = plan.nombre
    plan.delete()
    messages.warning(request, f'Plan «{nombre}» eliminado del sistema.')
    return redirect('superadmin:planes')


@require_POST
@superadmin_required
def planes_cobro(request):
    config = ConfiguracionPago.obtener()
    form = ConfiguracionPagoForm(request.POST, instance=config)
    if form.is_valid():
        form.save()
        messages.success(request, 'Datos de cobro bancario actualizados exitosamente.')
    else:
        messages.error(request, 'Revise los campos de la configuración de cobro.')
    return redirect('superadmin:planes')


@require_POST
@superadmin_required
def pago_eliminar(request, pk):
    pago = get_object_or_404(Pago, pk=pk)
    pago.delete()
    messages.warning(request, 'Pago eliminado del historial (la fecha de vencimiento no se modificó).')
    return _volver(request, 'superadmin:pagos')


# ---------------------------------------------------------------------------
# Super administradores
# ---------------------------------------------------------------------------
@superadmin_required
def administradores(request):
    return render(request, 'superadmin/administradores/lista.html', {
        'administradores': SuperAdmin.objects.all(),
    })


@superadmin_required
def administrador_crear(request):
    form = SuperAdminCrearForm(request.POST or None, initial={'is_active': True})
    if request.method == 'POST':
        if form.is_valid():
            sa = form.save()
            messages.success(request, f'Administrador «{sa.nombre}» creado.')
            return redirect('superadmin:administradores')
        messages.error(request, 'Revise los datos del administrador.')
    return render(request, 'superadmin/administradores/form.html', {'form': form, 'titulo': 'Nuevo administrador'})


@superadmin_required
def administrador_editar(request, pk):
    sa = get_object_or_404(SuperAdmin, pk=pk)
    actual = obtener_superadmin(request)
    form = SuperAdminEditarForm(request.POST or None, instance=sa)
    if request.method == 'POST':
        if form.is_valid():
            if sa.pk == actual.pk and not form.cleaned_data['is_active']:
                messages.error(request, 'No puede desactivar su propia cuenta.')
            else:
                form.save()
                messages.success(request, 'Administrador actualizado.')
                return redirect('superadmin:administradores')
        else:
            messages.error(request, 'Revise los datos del administrador.')
    return render(request, 'superadmin/administradores/form.html', {
        'form': form, 'titulo': f'Editar a {sa.nombre}', 'administrador': sa,
    })


@require_POST
@superadmin_required
def administrador_eliminar(request, pk):
    sa = get_object_or_404(SuperAdmin, pk=pk)
    if sa.pk == obtener_superadmin(request).pk:
        messages.error(request, 'No puede eliminar su propia cuenta.')
    elif SuperAdmin.objects.filter(is_active=True).exclude(pk=sa.pk).count() == 0:
        messages.error(request, 'Debe quedar al menos un administrador activo.')
    else:
        sa.delete()
        messages.success(request, 'Administrador eliminado.')
    return redirect('superadmin:administradores')


@superadmin_required
def mi_cuenta(request):
    sa = obtener_superadmin(request)
    form = CambiarClaveSuperAdminForm(sa, request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            sa.set_password(form.cleaned_data['clave1'])
            sa.save(update_fields=['password'])
            actualizar_hash_superadmin(request, sa)
            messages.success(request, 'Clave actualizada.')
            return redirect('superadmin:mi_cuenta')
        messages.error(request, 'No se pudo cambiar la clave.')
    return render(request, 'superadmin/mi_cuenta.html', {'form': form, 'sa': sa})


__all__ = ['Decimal']
