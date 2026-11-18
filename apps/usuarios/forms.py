from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import PasswordChangeForm

from apps.core.utils import BootstrapFormMixin
from apps.core.validators import validar_telefono

from .models import Usuario


class LoginForm(BootstrapFormMixin, forms.Form):
    usuario = forms.CharField(
        label='Usuario', max_length=20,
        widget=forms.TextInput(attrs={'autocomplete': 'username', 'autofocus': True, 'placeholder': 'Su usuario'}),
    )
    clave = forms.CharField(
        label='Clave', strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'placeholder': '••••••••'}),
    )


class ClavesMixin(forms.Form):
    """Clave + confirmación con los validadores de Django."""

    clave1 = forms.CharField(
        label='Clave', strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Mínimo 8, con letras y números'}),
    )
    clave2 = forms.CharField(
        label='Repetir clave', strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    def clean_clave2(self):
        c1, c2 = self.cleaned_data.get('clave1'), self.cleaned_data.get('clave2')
        if c1 and c2 and c1 != c2:
            raise forms.ValidationError('Las claves no coinciden.')
        return c2

    def _validar_clave(self, usuario_obj):
        clave = self.cleaned_data.get('clave2')
        if clave:
            try:
                password_validation.validate_password(clave, usuario_obj)
            except forms.ValidationError as e:
                self.add_error('clave1', e)


class RegistroForm(BootstrapFormMixin, ClavesMixin, forms.ModelForm):
    """Registro público de contadores (quedan pendientes de activación)."""

    class Meta:
        model = Usuario
        fields = ['nombre', 'telefono', 'email', 'usuario']
        widgets = {
            'nombre': forms.TextInput(attrs={'autocomplete': 'name'}),
            'telefono': forms.TextInput(attrs={'type': 'tel', 'placeholder': '0414-1234567', 'autocomplete': 'tel'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'opcional'}),
            'usuario': forms.TextInput(attrs={'autocomplete': 'username', 'placeholder': '4 a 20 letras o números'}),
        }

    field_order = ['nombre', 'telefono', 'email', 'usuario', 'clave1', 'clave2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['telefono'].required = True
        self.fields['telefono'].widget.attrs['required'] = 'required'

    def clean_nombre(self):
        n = self.cleaned_data['nombre'].strip()
        if len(n) < 3:
            raise forms.ValidationError('Escriba su nombre completo.')
        return n

    def clean_telefono(self):
        return validar_telefono(self.cleaned_data.get('telefono'))

    def clean_usuario(self):
        u = self.cleaned_data['usuario'].strip().lower()
        if Usuario.objects.filter(usuario__iexact=u).exists():
            raise forms.ValidationError('Ese usuario ya está en uso.')
        return u

    def _post_clean(self):
        super()._post_clean()
        self._validar_clave(self.instance)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['clave1'])
        if commit:
            user.save()
        return user


class PerfilForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'telefono', 'email']

    def clean_telefono(self):
        t = self.cleaned_data.get('telefono')
        return validar_telefono(t) if t else ''


class CambiarClaveForm(BootstrapFormMixin, PasswordChangeForm):
    pass
