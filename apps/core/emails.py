"""Servicio centralizado de envío de correos y notificaciones de FICONTI."""

import logging
import threading

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _debe_enviar_asincrono():
    backend = getattr(settings, 'EMAIL_BACKEND', '')
    return backend not in (
        'django.core.mail.backends.locmem.EmailBackend',
        'django.core.mail.backends.console.EmailBackend',
        'django.core.mail.backends.dummy.EmailBackend',
    )


def _sistema_meta():
    meta = getattr(settings, 'TRIBUTOVE', {}) or {}
    return (
        meta.get('NOMBRE', 'FICONTI'),
        meta.get('LEMA', 'Gestión fiscal · Venezuela'),
    )


def enviar_correo(
    destinatario,
    asunto,
    parrafos,
    *,
    titulo=None,
    nombre='',
    detalles=None,
    url_accion=None,
    texto_accion=None,
    nota_pie='',
    fail_silently=False,
    asincrono=False,
):
    """
    Envía un correo electrónico multipart (texto plano + HTML) usando la
    configuración SMTP definida en settings/.env.

    Si ``asincrono=True`` (y el backend no es locmem/console), despacha el envío
    en segundo plano para no bloquear la respuesta HTTP (login/registro/admin).
    """
    if isinstance(destinatario, str):
        destinatarios = [destinatario.strip()] if destinatario.strip() else []
    else:
        destinatarios = [d.strip() for d in (destinatario or []) if d and d.strip()]

    if not destinatarios:
        return False

    sistema_nombre, sistema_lema = _sistema_meta()
    titulo_final = titulo or asunto
    parrafos_lista = [parrafos] if isinstance(parrafos, str) else list(parrafos or [])
    detalles_lista = [(k, v) for k, v in (detalles or []) if v not in (None, '')]

    lineas_texto = []
    if nombre:
        lineas_texto.append(f'Hola {nombre},')
        lineas_texto.append('')
    for parrafo in parrafos_lista:
        lineas_texto.append(parrafo)
        lineas_texto.append('')
    if detalles_lista:
        for etiqueta, valor in detalles_lista:
            lineas_texto.append(f'- {etiqueta}: {valor}')
        lineas_texto.append('')
    if url_accion:
        etiqueta_url = texto_accion or 'Enlace'
        lineas_texto.append(f'{etiqueta_url}: {url_accion}')
        lineas_texto.append('')
    if nota_pie:
        lineas_texto.append(nota_pie)
        lineas_texto.append('')
    lineas_texto.append(f'-- {sistema_nombre} · {sistema_lema}')
    cuerpo_texto = '\n'.join(lineas_texto).strip()

    cuerpo_html = render_to_string(
        'emails/notificacion.html',
        {
            'sistema_nombre': sistema_nombre,
            'sistema_lema': sistema_lema,
            'titulo': titulo_final,
            'nombre': nombre,
            'parrafos': parrafos_lista,
            'detalles': detalles_lista,
            'url_accion': url_accion,
            'texto_accion': texto_accion,
            'nota_pie': nota_pie,
        },
    )

    mensaje = EmailMultiAlternatives(
        subject=asunto,
        body=cuerpo_texto,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=destinatarios,
    )
    mensaje.attach_alternative(cuerpo_html, 'text/html')

    def _despachar():
        try:
            enviados = mensaje.send(fail_silently=False)
            return enviados > 0
        except Exception:
            logger.exception('Error enviando correo "%s" a %s', asunto, destinatarios)
            if not fail_silently and not asincrono:
                raise
            return False

    if asincrono and _debe_enviar_asincrono():
        hilo = threading.Thread(target=_despachar, daemon=True)
        hilo.start()
        return True

    return _despachar()


def enviar_recuperacion_clave(usuario, enlace_recuperacion):
    """Envía el enlace de restablecimiento de clave al correo del usuario."""
    if not usuario or not usuario.email:
        return False
    horas = max(1, int(getattr(settings, 'PASSWORD_RESET_TIMEOUT', 86400)) // 3600)
    try:
        return enviar_correo(
            destinatario=usuario.email,
            asunto='Recuperación de clave · FICONTI',
            titulo='Restablece tu clave de acceso',
            nombre=usuario.nombre_mostrar,
            parrafos=[
                f'Recibimos una solicitud para restablecer la clave de acceso de tu cuenta en FICONTI.',
                'Haz clic en el siguiente botón para definir una nueva contraseña segura.',
            ],
            detalles=[
                ('Usuario', usuario.usuario),
                ('Vigencia del enlace', f'{horas} horas (un solo uso)'),
            ],
            url_accion=enlace_recuperacion,
            texto_accion='Restablecer mi clave',
            nota_pie='Si no solicitaste este cambio, puedes ignorar este mensaje; tu clave actual seguirá funcionando sin cambios.',
            fail_silently=False,
        )
    except Exception:
        return False


def enviar_notificacion_clave_actualizada(usuario, por_admin=False):
    """Notifica al usuario que la contraseña de su cuenta fue modificada."""
    if not usuario or not usuario.email:
        return False
    detalle = (
        'Un administrador del sistema ha restablecido la clave de acceso de tu cuenta.'
        if por_admin
        else 'Te confirmamos que la clave de acceso de tu cuenta en FICONTI fue actualizada correctamente.'
    )
    return enviar_correo(
        destinatario=usuario.email,
        asunto='Clave de acceso actualizada · FICONTI',
        titulo='Confirmación de cambio de clave',
        nombre=usuario.nombre_mostrar,
        parrafos=[detalle],
        detalles=[('Usuario', usuario.usuario)],
        nota_pie='Si no reconoces esta actividad, contacta de inmediato al equipo de soporte de FICONTI.',
        fail_silently=True,
        asincrono=True,
    )


def enviar_notificacion_bienvenida(usuario, url_login=None):
    """Envía correo de bienvenida cuando se registra un nuevo usuario."""
    if not usuario or not usuario.email:
        return False
    return enviar_correo(
        destinatario=usuario.email,
        asunto='Bienvenido a FICONTI · Cuenta creada',
        titulo='¡Bienvenido a FICONTI!',
        nombre=usuario.nombre_mostrar,
        parrafos=[
            'Tu cuenta ha sido creada exitosamente en FICONTI.',
            'Ya puedes ingresar al sistema para registrar tus empresas y gestionar tus obligaciones fiscales.',
        ],
        detalles=[
            ('Usuario', usuario.usuario),
            ('Correo registrado', usuario.email),
        ],
        url_accion=url_login,
        texto_accion='Iniciar sesión en FICONTI',
        nota_pie='Guarda este correo como referencia de tu usuario de acceso.',
        fail_silently=True,
        asincrono=True,
    )


def enviar_notificacion_suscripcion(usuario, suscripcion, evento, *, pago=None, motivo=''):
    """
    Notifica al usuario cambios relevantes en su suscripción o pagos.

    Eventos soportados: 'activada', 'suspendida', 'pago_aprobado', 'pago_rechazado'.
    """
    if not usuario or not usuario.email:
        return False

    vence_txt = f'{suscripcion.vence:%d/%m/%Y}' if suscripcion and suscripcion.vence else 'Sin fecha límite'

    if evento == 'pago_aprobado':
        detalles = [('Usuario', usuario.usuario)]
        if pago is not None:
            detalles.append(('Monto', f'{pago.moneda} {pago.monto}'))
            if pago.referencia:
                detalles.append(('Referencia', pago.referencia))
            detalles.append(('Días acreditados', f'{pago.dias} días'))
        detalles.append(('Vigente hasta', vence_txt))
        return enviar_correo(
            destinatario=usuario.email,
            asunto='Pago aprobado y suscripción activa · FICONTI',
            titulo='Tu pago ha sido aprobado',
            nombre=usuario.nombre_mostrar,
            parrafos=[
                'Confirmamos que tu pago fue aprobado y tu suscripción en FICONTI se encuentra activa.',
            ],
            detalles=detalles,
            fail_silently=True,
            asincrono=True,
        )

    if evento == 'pago_rechazado':
        detalles = [('Usuario', usuario.usuario)]
        if pago is not None:
            detalles.append(('Monto', f'{pago.moneda} {pago.monto}'))
            if pago.referencia:
                detalles.append(('Referencia', pago.referencia))
        if motivo:
            detalles.append(('Motivo', motivo))
        return enviar_correo(
            destinatario=usuario.email,
            asunto='Actualización sobre tu pago · FICONTI',
            titulo='Pago no aprobado',
            nombre=usuario.nombre_mostrar,
            parrafos=[
                'Tu registro de pago fue marcado como rechazado. Verifica los datos del comprobante o contacta con administración.',
            ],
            detalles=detalles,
            fail_silently=True,
            asincrono=True,
        )

    if evento == 'activada':
        return enviar_correo(
            destinatario=usuario.email,
            asunto='Suscripción activada · FICONTI',
            titulo='Tu suscripción está activa',
            nombre=usuario.nombre_mostrar,
            parrafos=[
                'Tu suscripción en FICONTI ha sido activada. Ya tienes acceso a los módulos fiscales habilitados para tu cuenta.',
            ],
            detalles=[
                ('Usuario', usuario.usuario),
                ('Vigente hasta', vence_txt),
            ],
            fail_silently=True,
            asincrono=True,
        )

    if evento == 'suspendida':
        return enviar_correo(
            destinatario=usuario.email,
            asunto='Suscripción suspendida · FICONTI',
            titulo='Tu suscripción ha sido suspendida',
            nombre=usuario.nombre_mostrar,
            parrafos=[
                'Tu suscripción en FICONTI se encuentra actualmente suspendida. Comunícate con administración para reactivar el acceso.',
            ],
            detalles=[('Usuario', usuario.usuario)],
            fail_silently=True,
            asincrono=True,
        )

    return False


def enviar_notificacion_general(
    destinatario,
    titulo,
    mensaje,
    *,
    asunto=None,
    nombre='',
    detalles=None,
    url_accion=None,
    texto_accion=None,
    nota_pie='',
    fail_silently=True,
):
    """Helper reutilizable para enviar notificaciones generales desde cualquier módulo."""
    return enviar_correo(
        destinatario=destinatario,
        asunto=asunto or f'{titulo} · FICONTI',
        titulo=titulo,
        nombre=nombre,
        parrafos=mensaje,
        detalles=detalles,
        url_accion=url_accion,
        texto_accion=texto_accion,
        nota_pie=nota_pie,
        fail_silently=fail_silently,
    )
