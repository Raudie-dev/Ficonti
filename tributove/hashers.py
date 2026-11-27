"""Hashers de contraseña configurados para buen balance seguridad/rendimiento."""

from django.contrib.auth.hashers import PBKDF2PasswordHasher


class FicontiPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    """
    PBKDF2-SHA256 con 260.000 iteraciones (~4x más rápido que el valor por
    defecto de Django 5.2 en servidores compartidos como cPanel, manteniendo
    compatibilidad automática con hashes previos).
    """

    iterations = 260_000
