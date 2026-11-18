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
    path('modulo/retenciones-islr/', include('apps.retenciones_islr.urls')),
    path('modulo/retenciones-iva/', include('apps.retenciones_iva.urls')),
    path('modulo/calendario/', include('apps.calendario.urls')),
    path('modulo/impuesto-diferido/', include('apps.impuesto_diferido.urls')),
    path('modulo/grandes-patrimonios/', include('apps.grandes_patrimonios.urls')),
    path('modulo/conciliacion/', include('apps.conciliacion.urls')),
    path('modulo/ajuste-inicial/', include('apps.ajuste_inicial.urls')),
    path('modulo/cedula-fiscal/', include('apps.cedula_fiscal.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
