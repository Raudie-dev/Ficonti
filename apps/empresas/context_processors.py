from .models import MONEDAS

SESSION_EMPRESA = 'empresa_activa'


def obtener_empresa_activa(request):
    """Devuelve la empresa activa del contador (o la primera que tenga)."""
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return None
    if hasattr(request, '_empresa_activa'):
        return request._empresa_activa
    empresas = request.user.empresas.all()
    pk = request.session.get(SESSION_EMPRESA)
    empresa = empresas.filter(pk=pk).first() if pk else None
    if empresa is None:
        empresa = empresas.first()
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
        'empresas_usuario': user.empresas.all(),
        'MONEDAS_EMPRESA': MONEDAS,
    }
