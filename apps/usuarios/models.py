from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from apps.core.validators import USUARIO_MENSAJE, USUARIO_REGEX


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def get_by_natural_key(self, username):
        return self.get(**{f'{self.model.USERNAME_FIELD}__iexact': username})

    def create_user(self, usuario, password=None, **extra):
        if not usuario:
            raise ValueError('El usuario es obligatorio.')
        user = self.model(usuario=usuario.strip().lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user


class Usuario(AbstractBaseUser):
    """
    Usuario normal del sistema (contador).

    Es la tabla propia de usuarios (``AUTH_USER_MODEL``). Los super
    administradores se guardan en otra tabla: ``apps.superadmin.SuperAdmin``.
    """

    usuario = models.CharField(
        'usuario', max_length=20, unique=True,
        validators=[RegexValidator(USUARIO_REGEX, USUARIO_MENSAJE)],
        help_text='De 4 a 20 letras, números, punto, guion o guion bajo.',
    )
    nombre = models.CharField('nombre completo', max_length=150)
    telefono = models.CharField('teléfono', max_length=20, blank=True)
    email = models.EmailField('correo electrónico', blank=True)
    is_active = models.BooleanField(
        'cuenta habilitada', default=True,
        help_text='Si se desmarca, el usuario no podrá iniciar sesión.',
    )
    uso = models.JSONField('uso de módulos', default=dict, blank=True)
    creado = models.DateTimeField('fecha de registro', default=timezone.now)
    creado_por = models.ForeignKey(
        'superadmin.SuperAdmin', verbose_name='creado por', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='usuarios_creados',
    )

    objects = UsuarioManager()

    USERNAME_FIELD = 'usuario'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'
        ordering = ['nombre']

    def __str__(self):
        return f'{self.nombre} ({self.usuario})'

    def save(self, *args, **kwargs):
        if self.usuario:
            self.usuario = self.usuario.strip().lower()
        super().save(*args, **kwargs)

    def get_full_name(self):
        return self.nombre

    def get_short_name(self):
        return self.nombre.split(' ')[0] if self.nombre else self.usuario

    # --- suscripción --------------------------------------------------------
    @property
    def suscripcion_activa(self):
        sus = getattr(self, 'suscripcion', None)
        return bool(sus and sus.vigente)

    def registrar_uso(self, codigo):
        uso = dict(self.uso or {})
        uso[codigo] = int(uso.get(codigo, 0)) + 1
        self.uso = uso
        Usuario.objects.filter(pk=self.pk).update(uso=uso)

    @property
    def uso_ordenado(self):
        return sorted((self.uso or {}).items(), key=lambda kv: -int(kv[1]))
