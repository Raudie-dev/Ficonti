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
    """
    Registro de usuario:
    "El Usuario se registra con sus datos: Usuario y clave para recuperar clave usar mail"
    """

    class Meta:
        model = Usuario
        fields = ['usuario', 'email', 'nombre', 'telefono']
        widgets = {
            'usuario': forms.TextInput(attrs={'autocomplete': 'username', 'placeholder': 'Usuario (4 a 20 letras o números)'}),
            'email': forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'Correo electrónico (para recuperar clave)'}),
            'nombre': forms.TextInput(attrs={'autocomplete': 'name', 'placeholder': 'Nombre completo (opcional)'}),
            'telefono': forms.TextInput(attrs={'type': 'tel', 'placeholder': '0414-1234567 (opcional)', 'autocomplete': 'tel'}),
        }

    field_order = ['usuario', 'email', 'clave1', 'clave2', 'nombre', 'telefono']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['email'].widget.attrs['required'] = 'required'
        self.fields['nombre'].required = False
        self.fields['telefono'].required = False

    def clean_usuario(self):
        u = self.cleaned_data['usuario'].strip().lower()
        if Usuario.objects.filter(usuario__iexact=u).exists():
            raise forms.ValidationError('Ese usuario ya está en uso.')
        return u

    def clean_email(self):
        e = (self.cleaned_data.get('email') or '').strip().lower()
        if not e:
            raise forms.ValidationError('Indique un correo electrónico para poder recuperar su clave.')
        return e

    def clean_nombre(self):
        n = (self.cleaned_data.get('nombre') or '').strip()
        return n

    def clean_telefono(self):
        t = (self.cleaned_data.get('telefono') or '').strip()
        return validar_telefono(t) if t else ''

    def _post_clean(self):
        if not self.instance.nombre:
            self.instance.nombre = self.cleaned_data.get('usuario') or 'Usuario'
        super()._post_clean()
        self._validar_clave(self.instance)

    def save(self, commit=True):
        user = super().save(commit=False)
        if not user.nombre:
            user.nombre = user.usuario
        user.set_password(self.cleaned_data['clave1'])
        if commit:
            user.save()
        return user


class RecuperarClaveMailForm(BootstrapFormMixin, forms.Form):
    """Formulario para recuperar clave usando correo electrónico."""
    email = forms.EmailField(
        label='Correo electrónico registrado',
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'correo@ejemplo.com', 'autofocus': True}),
    )
    usuario = forms.CharField(
        label='Usuario (opcional)',
        required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'username', 'placeholder': 'Su nombre de usuario'}),
    )


class RestablecerClaveForm(BootstrapFormMixin, ClavesMixin):
    """Establece una nueva clave tras validar el enlace de correo."""
    pass


class PerfilForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'telefono', 'email']

    def clean_telefono(self):
        t = self.cleaned_data.get('telefono')
        return validar_telefono(t) if t else ''


class CambiarClaveForm(BootstrapFormMixin, PasswordChangeForm):
    pass
