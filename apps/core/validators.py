import re

from django.core.exceptions import ValidationError


class LetrasYNumerosValidator:
    """La clave debe contener al menos una letra y un número."""

    def validate(self, password, user=None):
        if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            raise ValidationError(
                'La clave debe contener letras y números.',
                code='password_sin_letras_numeros',
            )

    def get_help_text(self):
        return 'La clave debe contener letras y números.'


USUARIO_REGEX = r'^[A-Za-z0-9._-]{4,20}$'
USUARIO_MENSAJE = 'El usuario debe tener de 4 a 20 letras, números, punto, guion o guion bajo.'


def validar_telefono(valor):
    limpio = re.sub(r'[^\d+]', '', valor or '')
    if not re.fullmatch(r'\+?\d{10,15}', limpio):
        raise ValidationError('Escriba un número de teléfono válido, con código de área.')
    return limpio
