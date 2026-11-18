from decimal import Decimal

from django import forms
from django.contrib.auth import password_validation

from apps.core.utils import BootstrapFormMixin
from apps.core.validators import validar_telefono
from apps.suscripciones.models import MODULOS_DISPONIBLES, MONEDAS, ConfiguracionPago, PlanSuscripcion
from apps.usuarios.forms import ClavesMixin
from apps.usuarios.models import Usuario

from .models import SuperAdmin


class SuperAdminLoginForm(BootstrapFormMixin, forms.Form):
    usuario = forms.CharField(
        label='Usuario administrador', max_length=20,
        widget=forms.TextInput(attrs={'autocomplete': 'username', 'autofocus': True}),
    )
    clave = forms.CharField(
        label='Clave', strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )


# ---------------------------------------------------------------------------
# Gestión de usuarios normales (contadores)
# ---------------------------------------------------------------------------
class ContadorCrearForm(BootstrapFormMixin, ClavesMixin, forms.ModelForm):
    activar = forms.BooleanField(
        label='Activar suscripción ahora (sin fecha de vencimiento)', required=False,
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'telefono', 'email', 'usuario', 'is_active']
        widgets = {'telefono': forms.TextInput(attrs={'type': 'tel', 'placeholder': '0414-1234567'})}

    field_order = ['nombre', 'telefono', 'email', 'usuario', 'clave1', 'clave2', 'is_active', 'activar']

    def clean_telefono(self):
        t = self.cleaned_data.get('telefono')
        return validar_telefono(t) if t else ''

    def clean_usuario(self):
        u = self.cleaned_data['usuario'].strip().lower()
        if Usuario.objects.filter(usuario__iexact=u).exclude(pk=self.instance.pk).exists():
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


class ContadorEditarForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombre', 'telefono', 'email', 'usuario', 'is_active']

    def clean_telefono(self):
        t = self.cleaned_data.get('telefono')
        return validar_telefono(t) if t else ''

    def clean_usuario(self):
        u = self.cleaned_data['usuario'].strip().lower()
        if Usuario.objects.filter(usuario__iexact=u).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ese usuario ya está en uso.')
        return u


class RestablecerClaveForm(BootstrapFormMixin, ClavesMixin, forms.Form):
    def __init__(self, *args, usuario=None, **kwargs):
        self.usuario_obj = usuario
        super().__init__(*args, **kwargs)

    def clean(self):
        data = super().clean()
        self._validar_clave(self.usuario_obj)
        return data


class SuscripcionForm(BootstrapFormMixin, forms.Form):
    activo = forms.BooleanField(label='Suscripción activa', required=False)
    vence = forms.DateField(
        label='Vence', required=False, widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        help_text='Déjelo vacío para una suscripción sin vencimiento.',
    )
    nota = forms.CharField(label='Nota de seguimiento', required=False, max_length=200)


class PagoForm(BootstrapFormMixin, forms.Form):
    plan = forms.ModelChoiceField(
        label='Plan de suscripción',
        queryset=PlanSuscripcion.objects.filter(activo=True),
        required=False,
        empty_label='Seleccionar plan (opcional)...',
    )
    ciclo = forms.ChoiceField(
        label='Ciclo',
        choices=[('mensual', 'Mensual'), ('anual', 'Anual')],
        initial='mensual',
    )
    monto = forms.DecimalField(
        label='Monto cobrado', min_value=Decimal('0'), max_digits=14, decimal_places=2,
        widget=forms.NumberInput(attrs={'step': 'any', 'min': '0'}),
    )
    moneda = forms.ChoiceField(label='Moneda', choices=MONEDAS)
    dias = forms.IntegerField(label='Días a extender', min_value=1, max_value=3660, initial=30)
    metodo = forms.ChoiceField(label='Canal / Método', choices=[
        ('pago_movil', 'Pago Móvil'),
        ('transferencia', 'Transferencia Bancaria'),
        ('zelle', 'Zelle'),
        ('efectivo', 'Efectivo en divisas'),
        ('otro', 'Otro'),
    ], initial='pago_movil')
    referencia = forms.CharField(label='Referencia / Comprobante', required=False, max_length=60,
                                 widget=forms.TextInput(attrs={'placeholder': 'Ej. ORD-20261026-495DEB o Ref Zelle'}))
    nota = forms.CharField(label='Nota interna', required=False, max_length=200,
                           widget=forms.TextInput(attrs={'placeholder': 'Observaciones de la conciliación'}))


class ConciliarPagoGlobalForm(PagoForm):
    contador = forms.ModelChoiceField(
        label='Contador a conciliar',
        queryset=Usuario.objects.all().order_by('nombre'),
        empty_label='Seleccionar contador...',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    field_order = ['contador', 'plan', 'ciclo', 'monto', 'moneda', 'dias', 'metodo', 'referencia', 'nota']


class ConfiguracionPagoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ConfiguracionPago
        fields = [
            'monto', 'monto_anual', 'moneda', 'contacto',
            'pago_movil_banco', 'pago_movil_telefono', 'pago_movil_rif',
            'transferencia_banco', 'transferencia_beneficiario', 'transferencia_cuenta',
            'zelle_correo', 'zelle_titular',
            'instrucciones',
        ]
        widgets = {
            'monto': forms.NumberInput(attrs={'step': 'any', 'min': '0', 'placeholder': 'Ej. 10.00'}),
            'monto_anual': forms.NumberInput(attrs={'step': 'any', 'min': '0', 'placeholder': 'Ej. 100.00'}),
            'contacto': forms.TextInput(attrs={'placeholder': 'Ej. +58 414 1234567 o pagos@tributove.com'}),
            'pago_movil_banco': forms.TextInput(attrs={'placeholder': 'Ej. 0102 - Banco de Venezuela'}),
            'pago_movil_telefono': forms.TextInput(attrs={'placeholder': 'Ej. 0414-1234567'}),
            'pago_movil_rif': forms.TextInput(attrs={'placeholder': 'Ej. J-12345678-0 o V-12345678'}),
            'transferencia_banco': forms.TextInput(attrs={'placeholder': 'Ej. Banco Mercantil / Banesco'}),
            'transferencia_beneficiario': forms.TextInput(attrs={'placeholder': 'Ej. TributoVE Soluciones C.A.'}),
            'transferencia_cuenta': forms.TextInput(attrs={'placeholder': '0105-XXXX-XX-XXXXXXXXXX (20 dígitos)'}),
            'zelle_correo': forms.EmailInput(attrs={'placeholder': 'Ej. zelle@tributove.com'}),
            'zelle_titular': forms.TextInput(attrs={'placeholder': 'Ej. Juan Pérez'}),
            'instrucciones': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Notas adicionales mostradas a los usuarios (ej. Enviar capture con número de referencia)'}),
        }


class PlanSuscripcionForm(BootstrapFormMixin, forms.ModelForm):
    modulos = forms.MultipleChoiceField(
        label='Módulos incluidos',
        choices=MODULOS_DISPONIBLES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
    )

    class Meta:
        model = PlanSuscripcion
        fields = [
            'nombre', 'codigo', 'etiqueta_badge', 'precio_mensual', 'precio_anual',
            'limite_usuarios', 'limite_empresas', 'mostrar_en_landing', 'incluye_ia',
            'api_propia', 'modulos',
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Plan Starter Pyme'}),
            'codigo': forms.TextInput(attrs={'placeholder': 'EJ: STARTER_PYME'}),
            'etiqueta_badge': forms.TextInput(attrs={'placeholder': 'Ej: STARTER'}),
            'precio_mensual': forms.NumberInput(attrs={'step': 'any', 'min': '0', 'placeholder': '29.00'}),
            'precio_anual': forms.NumberInput(attrs={'step': 'any', 'min': '0', 'placeholder': '288.00'}),
            'limite_usuarios': forms.NumberInput(attrs={'min': '0', 'placeholder': '5'}),
            'limite_empresas': forms.NumberInput(attrs={'min': '0', 'placeholder': '1'}),
            'mostrar_en_landing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'incluye_ia': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'api_propia': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial['modulos'] = self.instance.modulos or []
        elif not self.is_bound:
            self.initial['modulos'] = [k for k, _ in MODULOS_DISPONIBLES]

    def clean_codigo(self):
        c = self.cleaned_data['codigo'].strip().upper().replace(' ', '_')
        qs = PlanSuscripcion.objects.filter(codigo=c)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Ya existe un plan con este código identificador.')
        return c

    def clean_modulos(self):
        return self.cleaned_data.get('modulos') or []


# ---------------------------------------------------------------------------
# Gestión de super administradores
# ---------------------------------------------------------------------------
class SuperAdminCrearForm(BootstrapFormMixin, ClavesMixin, forms.ModelForm):
    class Meta:
        model = SuperAdmin
        fields = ['nombre', 'email', 'usuario', 'is_active']

    def clean_usuario(self):
        u = self.cleaned_data['usuario'].strip().lower()
        if SuperAdmin.objects.filter(usuario__iexact=u).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ese usuario ya está en uso.')
        return u

    def _post_clean(self):
        super()._post_clean()
        self._validar_clave(self.instance)

    def save(self, commit=True):
        sa = super().save(commit=False)
        sa.set_password(self.cleaned_data['clave1'])
        if commit:
            sa.save()
        return sa


class SuperAdminEditarForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SuperAdmin
        fields = ['nombre', 'email', 'usuario', 'is_active']

    def clean_usuario(self):
        u = self.cleaned_data['usuario'].strip().lower()
        if SuperAdmin.objects.filter(usuario__iexact=u).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Ese usuario ya está en uso.')
        return u


class CambiarClaveSuperAdminForm(BootstrapFormMixin, ClavesMixin, forms.Form):
    actual = forms.CharField(label='Clave actual', strip=False,
                             widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))
    field_order = ['actual', 'clave1', 'clave2']

    def __init__(self, superadmin, *args, **kwargs):
        self.superadmin = superadmin
        super().__init__(*args, **kwargs)
        self.fields['clave1'].label = 'Clave nueva'
        self.fields['clave2'].label = 'Repetir clave nueva'

    def clean_actual(self):
        if not self.superadmin.check_password(self.cleaned_data['actual']):
            raise forms.ValidationError('La clave actual no es correcta.')
        return self.cleaned_data['actual']

    def clean(self):
        data = super().clean()
        clave = data.get('clave2')
        if clave:
            try:
                password_validation.validate_password(clave, self.superadmin)
            except forms.ValidationError as e:
                self.add_error('clave1', e)
        return data
