import json

from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.core.mixins import render_bloqueado
from apps.core.modulos import MODULOS_POR_CODIGO
from django.contrib.auth.decorators import login_required

from .context_processors import fijar_empresa_activa, obtener_empresa_activa
from .forms import EmpresaForm, MonedaForm
from .models import DatoModulo, Empresa, EstadoModulo

MAX_VALOR_DATO = 8 * 1024 * 1024  # 8 MB por clave


def _volver(request, defecto='empresas:lista'):
    nxt = request.POST.get('next') or request.GET.get('next')
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return redirect(nxt)
    return redirect(defecto)


def suscripcion_requerida(view):
    """Decorador: contador autenticado y con mensualidad al día."""
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.suscripcion_activa:
            if request.headers.get('Content-Type', '').startswith('application/json'):
                return JsonResponse({'ok': False, 'error': 'Suscripción inactiva'}, status=403)
            return render_bloqueado(request)
        return view(request, *args, **kwargs)
    _wrapped.__name__ = view.__name__
    _wrapped.__doc__ = view.__doc__
    return _wrapped


# ---------------------------------------------------------------------------
# Mis empresas
# ---------------------------------------------------------------------------
@suscripcion_requerida
def lista(request):
    form = EmpresaForm(request.POST or None, usuario=request.user)
    if request.method == 'POST':
        if form.is_valid():
            empresa = form.save()
            fijar_empresa_activa(request, empresa)
            messages.success(request, f'Empresa «{empresa.nombre}» registrada y activada.')
            return redirect('empresas:lista')
        messages.error(request, 'No se pudo registrar la empresa. Revise los datos.')
    empresas = request.user.empresas.all()
    return render(request, 'empresas/lista.html', {
        'form': form,
        'empresas': empresas,
        'activa': obtener_empresa_activa(request),
    })


@suscripcion_requerida
def editar(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk, usuario=request.user)
    form = EmpresaForm(request.POST or None, instance=empresa, usuario=request.user)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            messages.success(request, 'Empresa actualizada.')
            return redirect('empresas:lista')
        messages.error(request, 'Revise los datos de la empresa.')
    return render(request, 'empresas/editar.html', {'form': form, 'empresa': empresa})


@require_POST
@suscripcion_requerida
def eliminar(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk, usuario=request.user)
    nombre = empresa.nombre
    empresa.delete()
    if request.session.get('empresa_activa') == pk:
        request.session.pop('empresa_activa', None)
    messages.success(request, f'Empresa «{nombre}» eliminada.')
    return redirect('empresas:lista')


@require_POST
@login_required
def activar(request, pk=None):
    pk = pk or request.POST.get('empresa')
    empresa = get_object_or_404(Empresa, pk=pk, usuario=request.user)
    fijar_empresa_activa(request, empresa)
    messages.info(request, f'Empresa activa: {empresa.nombre}.')
    return _volver(request)


@require_POST
@login_required
def moneda(request, pk):
    empresa = get_object_or_404(Empresa, pk=pk, usuario=request.user)
    form = MonedaForm(request.POST, instance=empresa)
    if form.is_valid():
        empresa = form.save()
        if empresa.falta_tasa:
            messages.warning(request, f'Indique la tasa: cuántos bolívares vale 1 {empresa.moneda}.')
        else:
            messages.success(request, f'Moneda de {empresa.nombre}: {empresa.get_moneda_display()}.')
    else:
        messages.error(request, 'Moneda o tasa inválida.')
    return _volver(request)


# ---------------------------------------------------------------------------
# Resumen de estatus
# ---------------------------------------------------------------------------
def construir_resumen(empresas, q='', filtro='todas', orden='nombre'):
    filas = []
    for e in empresas:
        st = e.resumen_estatus()
        if q and q.lower() not in f'{e.nombre} {e.rif}'.lower():
            continue
        if filtro == 'pend' and not st['realizados'] < st['aplican']:
            continue
        if filtro == 'comp' and not (st['aplican'] > 0 and st['realizados'] == st['aplican']):
            continue
        if filtro == 'sin' and st['realizados'] != 0:
            continue
        filas.append({'empresa': e, **st})
    filas.sort(key=lambda f: f['empresa'].nombre.lower())
    if orden == 'menor':
        filas.sort(key=lambda f: f['pct'])
    elif orden == 'mayor':
        filas.sort(key=lambda f: -f['pct'])
    return filas


def totales_resumen(empresas):
    from apps.core.modulos import MODULOS_RESUMEN
    tot = {m.codigo: {'ok': 0, 'ap': 0} for m in MODULOS_RESUMEN}
    aplican = realizados = pendientes = 0
    for e in empresas:
        st = e.resumen_estatus()
        aplican += st['aplican']
        realizados += st['realizados']
        if st['realizados'] < st['aplican']:
            pendientes += 1
        for c in st['celdas']:
            if c['estado'] != 'na':
                tot[c['modulo'].codigo]['ap'] += 1
                if c['estado'] == 'ok':
                    tot[c['modulo'].codigo]['ok'] += 1
    return {
        'por_modulo': [tot[m.codigo] for m in MODULOS_RESUMEN],
        'aplican': aplican, 'realizados': realizados, 'pendientes': pendientes,
        'pct': round(realizados / aplican * 100) if aplican else 0,
    }


@suscripcion_requerida
def resumen(request):
    todas = list(request.user.empresas.prefetch_related('estados'))
    q = request.GET.get('q', '').strip()
    filtro = request.GET.get('f', 'todas')
    orden = request.GET.get('o', 'nombre')
    compacta = request.GET.get('c', '1' if len(todas) > 30 else '0') == '1'
    filas = construir_resumen(todas, q, filtro, orden)
    return render(request, 'empresas/resumen.html', {
        'filas': filas, 'total_empresas': len(todas), 'totales': totales_resumen(todas),
        'q': q, 'f': filtro, 'o': orden, 'compacta': compacta,
    })


# ---------------------------------------------------------------------------
# API usada por los módulos (JSON)
# ---------------------------------------------------------------------------
def _json(request):
    try:
        return json.loads(request.body or b'{}')
    except (ValueError, UnicodeDecodeError):
        return None


@require_POST
@suscripcion_requerida
def estado_modulo(request, pk):
    """Guarda el avance que reporta un módulo para la empresa."""
    empresa = get_object_or_404(Empresa, pk=pk, usuario=request.user)
    data = _json(request)
    if not isinstance(data, dict):
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)
    modulo, estado = data.get('modulo'), data.get('estado')
    if modulo not in MODULOS_POR_CODIGO or estado not in dict(EstadoModulo.ESTADOS):
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)
    EstadoModulo.objects.update_or_create(
        empresa=empresa, modulo=modulo,
        defaults={'estado': estado, 'detalle': str(data.get('detalle') or '')[:60]},
    )
    return JsonResponse({'ok': True})


@require_POST
@suscripcion_requerida
def datos_modulo(request, pk):
    """Sincroniza el almacenamiento de trabajo de los módulos (antes localStorage)."""
    empresa = get_object_or_404(Empresa, pk=pk, usuario=request.user)
    data = _json(request)
    if not isinstance(data, dict):
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)
    cambios = data.get('cambios') if 'cambios' in data else data
    if not isinstance(cambios, dict):
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)
    with transaction.atomic():
        for clave, valor in cambios.items():
            clave = str(clave)[:100]
            if valor is None:
                DatoModulo.objects.filter(empresa=empresa, clave=clave).delete()
                continue
            valor = str(valor)
            if len(valor) > MAX_VALOR_DATO:
                return JsonResponse({'ok': False, 'error': f'El dato «{clave}» es demasiado grande'}, status=413)
            DatoModulo.objects.update_or_create(empresa=empresa, clave=clave, defaults={'valor': valor})
    return JsonResponse({'ok': True, 'guardados': len(cambios)})
