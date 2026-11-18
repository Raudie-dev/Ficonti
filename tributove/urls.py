"""
Rutas principales de TributoVE.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    # Entrada principal / redirección inteligente
    path('', include('apps.core.urls')),

    # Autenticación y perfil de contadores (usuarios normales)
    path('', include('apps.usuarios.urls')),

    # Panel independiente de SuperAdministrador
    path('superadmin/', include('apps.superadmin.urls')),

    # Gestión de empresas y APIs de sincronización
    path('empresas/', include('apps.empresas.urls')),

    # Módulos fiscales (un módulo = una app)
    path('modulo/planificacion/', include('apps.planificacion.urls')),
    path('modulo/calculo-ari/', include('apps.calculo_ari.urls')),
    path('modulo/estimada-islr/', include('apps.estimada_islr.urls')),
    path('modulo/retenciones-islr/', include('apps.retenciones_islr.urls')),
    path('modulo/retenciones-iva/', include('apps.retenciones_iva.urls')),
    path('modulo/calendario/', include('apps.calendario.urls')),
    path('modulo/sanciones-cot/', include('apps.sanciones_cot.urls')),
    path('modulo/impuesto-diferido/', include('apps.impuesto_diferido.urls')),
    path('modulo/grandes-patrimonios/', include('apps.grandes_patrimonios.urls')),
    path('modulo/conciliacion/', include('apps.conciliacion.urls')),
    path('modulo/auditoria-ingresos/', include('apps.auditoria_ingresos.urls')),
    path('modulo/control-bancario/', include('apps.control_bancario.urls')),
    path('modulo/ajuste-inicial/', include('apps.ajuste_inicial.urls')),
    path('modulo/cedula-fiscal/', include('apps.cedula_fiscal.urls')),
    path('modulo/conciliacion-islr/', include('apps.conciliacion_islr.urls')),
    path('modulo/precios-transferencia/', include('apps.precios_transferencia.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
