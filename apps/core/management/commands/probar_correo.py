from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.core.emails import enviar_notificacion_general


class Command(BaseCommand):
    help = 'Envía un correo de prueba para verificar la conexión SMTP configurada en .env.'

    def add_arguments(self, parser):
        parser.add_argument(
            'destinatario',
            help='Correo electrónico de destino para el mensaje de prueba.',
        )

    def handle(self, *args, **options):
        destinatario = options['destinatario'].strip()
        self.stdout.write(
            f'Enviando prueba desde {settings.DEFAULT_FROM_EMAIL} '
            f'vía {settings.EMAIL_HOST}:{settings.EMAIL_PORT} '
            f'(SSL={settings.EMAIL_USE_SSL}, TLS={settings.EMAIL_USE_TLS})...'
        )
        try:
            ok = enviar_notificacion_general(
                destinatario=destinatario,
                titulo='Prueba de correo SMTP',
                asunto='Prueba de notificaciones · FICONTI',
                mensaje=[
                    'Este es un correo de prueba enviado desde FICONTI.',
                    'Si recibiste este mensaje, la conexión SMTP para notificaciones y recuperación de clave funciona correctamente.',
                ],
                detalles=[
                    ('Remitente', settings.DEFAULT_FROM_EMAIL),
                    ('Servidor SMTP', f'{settings.EMAIL_HOST}:{settings.EMAIL_PORT}'),
                ],
                fail_silently=False,
            )
        except Exception as exc:
            raise CommandError(f'Error al enviar correo de prueba: {exc}') from exc

        if not ok:
            raise CommandError('El backend de correo no confirmó el envío del mensaje.')

        self.stdout.write(self.style.SUCCESS(f'Correo de prueba enviado correctamente a {destinatario}.'))
