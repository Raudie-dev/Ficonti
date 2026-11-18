from django.conf import settings

from .modulos import MODULOS, MODULOS_RESUMEN, menu_agrupado


def sistema(request):
    """Variables globales disponibles en todas las plantillas."""
    cfg = getattr(settings, 'TRIBUTOVE', {})
    match = getattr(request, 'resolver_match', None)
    return {
        'SISTEMA_NOMBRE': cfg.get('NOMBRE', 'TributoVE'),
        'SISTEMA_LEMA': cfg.get('LEMA', ''),
        'MENU_MODULOS': menu_agrupado(),
        'MODULOS': MODULOS,
        'MODULOS_RESUMEN': MODULOS_RESUMEN,
        'url_actual': match.view_name if match else '',
        'namespace_actual': match.namespace if match else '',
    }
