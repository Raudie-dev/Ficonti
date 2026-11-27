from .models import MONEDAS

SESSION_EMPRESA = 'empresa_activa'


def _empresas_usuario(request):
    """Cachea la lista de empresas del usuario dentro del request actual."""
    if not hasattr(request, '_empresas_usuario_cache'):
        request._empresas_usuario_cache = list(request.user.empresas.all())
    return request._empresas_usuario_cache


def obtener_empresa_activa(request):
    """Devuelve la empresa activa del contador (o la primera que tenga)."""
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return None
    if hasattr(request, '_empresa_activa'):
        return request._empresa_activa
    empresas = _empresas_usuario(request)
    pk = request.session.get(SESSION_EMPRESA)
    empresa = next((e for e in empresas if e.pk == pk), None) if pk else None
    if empresa is None:
        empresa = empresas[0] if empresas else None
        if empresa:
            request.session[SESSION_EMPRESA] = empresa.pk
        else:
            request.session.pop(SESSION_EMPRESA, None)
    request._empresa_activa = empresa
    return empresa


def fijar_empresa_activa(request, empresa):
    request.session[SESSION_EMPRESA] = empresa.pk if empresa else None
    request._empresa_activa = empresa


def empresa_activa(request):
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    return {
        'empresa_activa': obtener_empresa_activa(request),
        'empresas_usuario': _empresas_usuario(request),
        'MONEDAS_EMPRESA': MONEDAS,
    }
