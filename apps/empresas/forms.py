import re
from decimal import Decimal

from django import forms
from django.conf import settings

from apps.core.utils import BootstrapFormMixin

from .models import TIPOS_RIF, Empresa, formatear_rif


class EmpresaForm(BootstrapFormMixin, forms.ModelForm):
    tipo_rif = forms.ChoiceField(label='Tipo', choices=[(t, t) for t in TIPOS_RIF])
    numero_rif = forms.CharField(
        label='RIF (9 dígitos)', max_length=9, min_length=9,
        widget=forms.TextInput(attrs={'inputmode': 'numeric', 'pattern': '[0-9]{9}', 'placeholder': '123456789',
                                      'autocomplete': 'off'}),
    )

    class Meta:
        model = Empresa
        fields = ['nombre', 'condicion', 'moneda', 'tasa']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Razón social', 'autocomplete': 'off',
                                             'autocapitalize': 'characters', 'spellcheck': 'false'}),
            'tasa': forms.NumberInput(attrs={'step': 'any', 'min': '0', 'placeholder': 'Bs por 1'}),
        }

    field_order = ['nombre', 'tipo_rif', 'numero_rif', 'condicion', 'moneda', 'tasa']

    def __init__(self, *args, usuario=None, **kwargs):
        self.usuario = usuario
        super().__init__(*args, **kwargs)
        self.fields['tasa'].required = False
        if self.instance and self.instance.pk and self.instance.rif:
            r = self.instance.rif.replace('-', '')
            self.initial.setdefault('tipo_rif', r[0])
            self.initial.setdefault('numero_rif', r[1:])

    def clean_nombre(self):
        n = (self.cleaned_data.get('nombre') or '').strip()
        if not n:
            raise forms.ValidationError('Indique el nombre de la empresa.')
        return n

    def clean_numero_rif(self):
        d = re.sub(r'\D', '', self.cleaned_data.get('numero_rif') or '')
        if len(d) != 9:
            raise forms.ValidationError('Escriba los 9 dígitos (8 del número y 1 final).')
        return d

    def clean(self):
        data = super().clean()
        tipo, num = data.get('tipo_rif'), data.get('numero_rif')
        if tipo and num:
            rif = formatear_rif(tipo + num)
            qs = Empresa.objects.filter(usuario=self.usuario, rif=rif)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('numero_rif', 'Ese RIF ya está registrado.')
            self.instance.rif = rif
        moneda, tasa = data.get('moneda'), data.get('tasa') or Decimal('0')
        if moneda and moneda != 'VES' and not tasa > 0:
            self.add_error('tasa', f'Indique la tasa de cambio: cuántos bolívares vale 1 {moneda}.')
        data['tasa'] = tasa if moneda != 'VES' else Decimal('0')
        if not self.instance.pk and self.usuario is not None:
            maximo = settings.TRIBUTOVE.get('MAX_EMPRESAS', 200)
            if self.usuario.empresas.count() >= maximo:
                raise forms.ValidationError(f'Alcanzó el límite de {maximo} empresas.')
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.tasa = self.cleaned_data.get('tasa') or Decimal('0')
        if self.usuario is not None and not obj.pk:
            obj.usuario = self.usuario
        if commit:
            obj.save()
        return obj


class MonedaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['moneda', 'tasa']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tasa'].required = False

    def clean(self):
        data = super().clean()
        if data.get('moneda') == 'VES':
            data['tasa'] = Decimal('0')
        elif data.get('tasa') is None or data.get('tasa') < 0:
            data['tasa'] = Decimal('0')
        return data
