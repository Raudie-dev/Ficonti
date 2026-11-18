import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.modulos import MODULOS_RESUMEN, obtener_modulo

SPE = 'Sujeto pasivo especial'
CONDICIONES = [
    (SPE, SPE),
    ('Contribuyente ordinario', 'Contribuyente ordinario'),
    ('Contribuyente formal', 'Contribuyente formal'),
]

MONEDAS = [
    ('VES', 'Bs · Bolívares'),
    ('USD', 'USD · Dólares americanos'),
    ('EUR', 'EUR · Euros'),
    ('COP', 'COP · Pesos colombianos'),
    ('CNY', 'CNY · Yuan chino'),
]

TIPOS_RIF = ['J', 'G', 'V', 'E', 'P', 'C']
RIF_REGEX = re.compile(r'^[JGVEPC]-?\d{8}-?\d$', re.I)


def formatear_rif(rif):
    r = (rif or '').strip().upper().replace('-', '')
    return f'{r[0]}-{r[1:9]}-{r[9:]}'


def validar_rif(rif):
    if not RIF_REGEX.match((rif or '').strip()):
        raise ValidationError('RIF inválido: elija la letra y escriba los 9 dígitos (8 del número y 1 final).')


class Empresa(models.Model):
    """Empresa (contribuyente) atendida por un contador."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='empresas',
    )
    nombre = models.CharField('razón social', max_length=200)
    rif = models.CharField('RIF', max_length=12, validators=[validar_rif])
    condicion = models.CharField('condición', max_length=40, choices=CONDICIONES, default=SPE)
    moneda = models.CharField('moneda', max_length=3, choices=MONEDAS, default='VES')
    tasa = models.DecimalField('tasa (Bs por 1)', max_digits=18, decimal_places=4, default=0)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'empresas'
        ordering = ['nombre']
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'rif'], name='empresa_rif_unico_por_usuario'),
        ]

    def __str__(self):
        return f'{self.nombre} · {self.rif}'

    def save(self, *args, **kwargs):
        if self.rif and RIF_REGEX.match(self.rif.strip()):
            self.rif = formatear_rif(self.rif)
        if self.moneda == 'VES':
            self.tasa = 0
        super().save(*args, **kwargs)

    @property
    def es_spe(self):
        return self.condicion == SPE

    @property
    def es_sujeto_pasivo_especial(self):
        return self.es_spe

    @property
    def condicion_corta(self):
        if self.es_spe:
            return 'SPE'
        if 'ordinario' in (self.condicion or '').lower():
            return 'Ordinario'
        return 'Formal'

    @property
    def es_bolivares(self):
        return (self.moneda or 'VES') == 'VES'

    @property
    def moneda_simbolo(self):
        return {
            'VES': 'Bs',
            'USD': 'USD',
            'EUR': 'EUR',
            'COP': 'COP',
            'CNY': 'CNY',
        }.get(self.moneda or 'VES', self.moneda or 'Bs')

    @property
    def actualizada(self):
        est = self.estados.order_by('-fecha').first()
        if est and est.fecha:
            return est.fecha
        return self.creado

    @property
    def falta_tasa(self):
        return self.moneda != 'VES' and not (self.tasa and self.tasa > 0)

    # --- datos que recibe cada módulo (window.EMPRESA) -----------------------
    def datos_modulo(self, modulo):
        return {
            'id': self.pk,
            'nombre': self.nombre,
            'rif': self.rif,
            'condicion': self.condicion,
            'soloSPE': bool(modulo.solo_spe),
            'soloBs': bool(modulo.solo_bs),
            'moneda': {'cod': self.moneda or 'VES', 'tasa': float(self.tasa or 0)},
        }

    # --- estatus por módulo ---------------------------------------------------
    def estatus_modulo(self, codigo, estados=None):
        """Devuelve (estado, detalle) para un módulo: ok | proc | sin | na."""
        modulo = obtener_modulo(codigo)
        if modulo and modulo.consulta:
            return 'na', 'Módulo de consulta'
        if estados is None:
            estados = {e.modulo: e for e in self.estados.all()}
        e = estados.get(codigo)
        if e:
            return e.estado, e.detalle
        if codigo == 'iva' and not self.es_spe:
            return 'na', 'No es agente de retención'
        return 'sin', 'Aún no abierto'

    def resumen_estatus(self):
        estados = {e.modulo: e for e in self.estados.all()}
        celdas, aplican, realizados = [], 0, 0
        for m in MODULOS_RESUMEN:
            est, det = self.estatus_modulo(m.codigo, estados)
            if est != 'na':
                aplican += 1
                if est == 'ok':
                    realizados += 1
            celdas.append({
                'modulo': m,
                'estado': est,
                'detalle': det,
                'url': f'{m.url}?empresa={self.pk}',
            })
        pct = round(realizados / aplican * 100) if aplican else 0
        return {'celdas': celdas, 'aplican': aplican, 'realizados': realizados, 'pct': pct}


class EstadoModulo(models.Model):
    """Avance de una empresa en un módulo (lo reporta el propio módulo)."""

    ESTADOS = [('ok', 'Realizado'), ('proc', 'En proceso'), ('sin', 'Sin iniciar'), ('na', 'No aplica')]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='estados')
    modulo = models.CharField(max_length=10)
    estado = models.CharField(max_length=4, choices=ESTADOS, default='sin')
    detalle = models.CharField(max_length=60, blank=True)
    fecha = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'empresas_estado_modulo'
        constraints = [
            models.UniqueConstraint(fields=['empresa', 'modulo'], name='estado_unico_por_modulo'),
        ]

    def __str__(self):
        return f'{self.empresa} · {self.modulo}: {self.estado}'


class DatoModulo(models.Model):
    """
    Información de trabajo que guardan los módulos para cada empresa.

    Los módulos (calculadoras en JavaScript) usan ``localStorage``; en
    TributoVE esas lecturas/escrituras se redirigen a esta tabla, de modo que
    los datos quedan en el servidor y disponibles desde cualquier equipo.
    """

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='datos')
    clave = models.CharField(max_length=100)
    valor = models.TextField(blank=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'empresas_dato_modulo'
        constraints = [
            models.UniqueConstraint(fields=['empresa', 'clave'], name='dato_unico_por_clave'),
        ]

    def __str__(self):
        return f'{self.empresa} · {self.clave}'
