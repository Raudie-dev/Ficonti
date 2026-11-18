"""Utilidades comunes: formularios Bootstrap y control de intentos de ingreso."""

from django import forms
from django.conf import settings
from django.core.cache import cache


class BootstrapFormMixin:
    """Agrega automáticamente las clases de Bootstrap 5 a los widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            w = field.widget
            if isinstance(w, (forms.CheckboxInput,)):
                css = 'form-check-input'
            elif isinstance(w, (forms.Select, forms.SelectMultiple)):
                css = 'form-select'
            elif isinstance(w, forms.RadioSelect):
                css = 'form-check-input'
            else:
                css = 'form-control'
            w.attrs['class'] = (w.attrs.get('class', '') + ' ' + css).strip()
            if field.required and not isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault('required', 'required')

    def full_clean(self):
        super().full_clean()
        # Marca visualmente los campos con error
        if self.is_bound:
            for name in self.errors:
                if name in self.fields:
                    w = self.fields[name].widget
                    if 'is-invalid' not in w.attrs.get('class', ''):
                        w.attrs['class'] = (w.attrs.get('class', '') + ' is-invalid').strip()


class ControlIntentos:
    """Bloquea temporalmente el ingreso tras varios intentos fallidos."""

    def __init__(self, request, ambito, usuario=''):
        ip = request.META.get('REMOTE_ADDR', '')
        self.clave = f'login:{ambito}:{ip}:{(usuario or "").lower()}'
        self.maximo = getattr(settings, 'LOGIN_MAX_INTENTOS', 5)
        self.segundos = getattr(settings, 'LOGIN_BLOQUEO_SEGUNDOS', 30)

    @property
    def bloqueado(self):
        return cache.get(self.clave + ':lock') is not None

    def fallo(self):
        n = cache.get(self.clave, 0) + 1
        if n >= self.maximo:
            cache.set(self.clave + ':lock', 1, self.segundos)
            cache.delete(self.clave)
        else:
            cache.set(self.clave, n, self.segundos * 10)

    def exito(self):
        cache.delete(self.clave)
        cache.delete(self.clave + ':lock')
