import re
from decimal import Decimal

from django import forms
from django.conf import settings

from apps.core.utils import BootstrapFormMixin

from .models import TIPOS_RIF, Empresa, formatear_rif


class EmpresaForm(BootstrapFormMixin, forms.ModelForm):
    """
    Registro de empresa:
    "El registro de empresas solo requiere nombre y rif y condición de contribuyente"
    Acepta tanto un campo único `rif` (Ej. J-12345678-9 o J123456789) como `tipo_rif` + `numero_rif`.
    """
    rif = forms.CharField(
        label='RIF',
        max_length=14,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'J-12345678-9',
            'autocomplete': 'off',
            'autocapitalize': 'characters',
            'spellcheck': 'false',
        }),
    )
    tipo_rif = forms.ChoiceField(label='Tipo', choices=[(t, t) for t in TIPOS_RIF], required=False)
    numero_rif = forms.CharField(
        label='RIF (9 dígitos)', max_length=9, min_length=9, required=False,
        widget=forms.TextInput(attrs={'inputmode': 'numeric', 'pattern': '[0-9]{9}', 'placeholder': '123456789',
                                      'autocomplete': 'off'}),
    )

    class Meta:
        model = Empresa
        fields = ['nombre', 'condicion', 'moneda', 'tasa']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Nombre o Razón Social', 'autocomplete': 'off',
                                             'autocapitalize': 'characters', 'spellcheck': 'false'}),
            'tasa': forms.NumberInput(attrs={'step': 'any', 'min': '0', 'placeholder': 'Bs por 1'}),
        }

    field_order = ['nombre', 'rif', 'condicion', 'tipo_rif', 'numero_rif', 'moneda', 'tasa']

    def __init__(self, *args, usuario=None, **kwargs):
        self.usuario = usuario
        super().__init__(*args, **kwargs)
        self.fields['moneda'].required = False
        self.fields['tasa'].required = False
        if self.instance and self.instance.pk and self.instance.rif:
            self.initial.setdefault('rif', self.instance.rif)
            r = self.instance.rif.replace('-', '')
            if r:
                self.initial.setdefault('tipo_rif', r[0])
                self.initial.setdefault('numero_rif', r[1:])

    def clean_nombre(self):
        n = (self.cleaned_data.get('nombre') or '').strip()
        if not n:
            raise forms.ValidationError('Indique el nombre de la empresa.')
        return n

    def clean(self):
        data = super().clean()
        raw_rif = (data.get('rif') or '').strip().upper()
        tipo = (data.get('tipo_rif') or '').strip().upper()
        num = re.sub(r'\D', '', data.get('numero_rif') or '')

        rif_formateado = ''
        if raw_rif:
            limpio = re.sub(r'[^A-Z0-9]', '', raw_rif)
            if len(limpio) == 9 and limpio.isdigit():
                rif_formateado = formatear_rif((tipo or 'J') + limpio)
            elif len(limpio) == 10 and limpio[0] in TIPOS_RIF and limpio[1:].isdigit():
                rif_formateado = formatear_rif(limpio)
            else:
                self.add_error('rif', 'Formato de RIF inválido. Use J-12345678-9 (letra J, G, V, E, P, C seguida de 9 dígitos).')
        elif tipo and num:
            if len(num) != 9:
                self.add_error('numero_rif', 'Escriba los 9 dígitos (8 del número y 1 final).')
            else:
                rif_formateado = formatear_rif(tipo + num)
        elif self.instance and self.instance.pk and self.instance.rif:
            rif_formateado = self.instance.rif
        else:
            self.add_error('rif', 'Indique el RIF de la empresa (Ej. J-12345678-9).')

        if rif_formateado:
            qs = Empresa.objects.filter(usuario=self.usuario, rif=rif_formateado)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('rif', 'Ese RIF ya está registrado.')
            self.instance.rif = rif_formateado
            data['rif'] = rif_formateado

        moneda = data.get('moneda') or (self.instance.moneda if self.instance and self.instance.pk else 'VES') or 'VES'
        tasa = data.get('tasa')
        if tasa is None:
            tasa = self.instance.tasa if (self.instance and self.instance.pk and self.instance.tasa) else Decimal('0')
        if moneda != 'VES' and not tasa > 0:
            tasa = Decimal('1')
        data['moneda'] = moneda
        data['tasa'] = tasa if moneda != 'VES' else Decimal('0')

        if not self.instance.pk and self.usuario is not None:
            maximo = settings.TRIBUTOVE.get('MAX_EMPRESAS', 200)
            if self.usuario.empresas.count() >= maximo:
                raise forms.ValidationError(f'Alcanzó el límite de {maximo} empresas.')
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.moneda = self.cleaned_data.get('moneda') or 'VES'
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
