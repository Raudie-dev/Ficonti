import os
from django.conf import settings
from django.http import FileResponse, HttpResponse
from django.shortcuts import redirect, render

from apps.superadmin.mixins import obtener_superadmin
from apps.suscripciones.models import ConfiguracionPago, MODULOS_DISPONIBLES, PlanSuscripcion


def landing(request):
    """Landing page principal en la URL base con estética fintech oscuro, acentos verde lima y datos de TributoVE."""
    planes = PlanSuscripcion.objects.filter(activo=True, mostrar_en_landing=True).order_by('orden', 'precio_mensual')
    config_pago = ConfiguracionPago.obtener()
    return render(request, 'landing.html', {
        'planes': planes,
        'config_pago': config_pago,
        'modulos_disponibles': MODULOS_DISPONIBLES,
    })


def landing_redirect(request):
    """Redirige /landing/ permanentemente a la URL base / (código 301)."""
    return redirect('core:landing', permanent=True)


def inicio(request):
    """Redirección inteligente al iniciar sesión según el rol de usuario."""
    if request.user.is_authenticated:
        if request.user.empresas.exists() and request.user.suscripcion_activa:
            return redirect('empresas:resumen')
        return redirect('empresas:lista')
    if obtener_superadmin(request) is not None:
        return redirect('superadmin:panel')
    return redirect('core:landing')


def manifest_view(request):
    """Sirve el manifest de la PWA con la cabecera adecuada."""
    manifest_path = os.path.join(settings.BASE_DIR, 'static', 'manifest.json')
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='application/manifest+json')
    return HttpResponse('{}', content_type='application/manifest+json', status=404)


def service_worker_view(request):
    """Sirve el Service Worker desde la raíz con alcance total '/'."""
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'sw.js')
    if os.path.exists(sw_path):
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
        response = HttpResponse(content, content_type='application/javascript')
        response['Service-Worker-Allowed'] = '/'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    return HttpResponse('// SW no encontrado', content_type='application/javascript', status=404)


def offline_view(request):
    """Pantalla mostrada cuando el usuario está sin conexión."""
    return render(request, 'offline.html')
