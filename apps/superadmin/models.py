from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from apps.core.validators import USUARIO_MENSAJE, USUARIO_REGEX


class SuperAdminManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, username):
        return self.get(usuario__iexact=username)

    def create_superadmin(self, usuario, password, nombre='Administrador', **extra):
        sa = self.model(usuario=usuario.strip().lower(), nombre=nombre, **extra)
        sa.set_password(password)
        sa.save(using=self._db)
        return sa


class SuperAdmin(AbstractBaseUser):
    """
    Super administrador del sistema.

    Tabla independiente de la de usuarios normales. Administra a los
    contadores (usuarios normales), sus suscripciones y la configuración.
    Su sesión es independiente de la de ``django.contrib.auth``.
    """

    usuario = models.CharField(
        'usuario', max_length=20, unique=True,
        validators=[RegexValidator(USUARIO_REGEX, USUARIO_MENSAJE)],
    )
    nombre = models.CharField('nombre', max_length=150)
    email = models.EmailField('correo electrónico', blank=True)
    is_active = models.BooleanField('activo', default=True)
    creado = models.DateTimeField('creado', default=timezone.now)

    objects = SuperAdminManager()

    USERNAME_FIELD = 'usuario'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        db_table = 'superadmins'
        verbose_name = 'super administrador'
        verbose_name_plural = 'super administradores'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.usuario})'

    def save(self, *args, **kwargs):
        if self.usuario:
            self.usuario = self.usuario.strip().lower()
        super().save(*args, **kwargs)
