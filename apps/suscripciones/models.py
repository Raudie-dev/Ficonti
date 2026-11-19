from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

MONEDAS = [
    ('USD', 'USD · Dólares americanos'),
    ('VES', 'Bs · Bolívares'),
    ('EUR', 'EUR · Euros'),
    ('COP', 'COP · Pesos colombianos'),
    ('CNY', 'CNY · Yuan chino'),
]


METODOS_PAGO = [
    ('pago_movil', 'Pago Móvil'),
    ('transferencia', 'Transferencia Bancaria'),
    ('zelle', 'Zelle'),
    ('efectivo', 'Efectivo en divisas'),
    ('otro', 'Otro'),
]

MODULOS_DISPONIBLES = [
    ('planificacion', 'Planificación fiscal'),
    ('retenciones_islr', 'Retenciones (ISLR)'),
    ('sanciones_cot', 'Simulador Sanciones'),
    ('calendario', 'Calendario fiscal'),
    ('calculo_ari', 'Calculo ARI'),
    ('estimada_islr', 'ISLR Estimada'),
    ('grandes_patrimonios', 'Grandes patrimonios'),
    ('auditoria_ingresos', 'Conciliación de Ingresos'),
    ('conciliacion', 'Conciliación bancaria'),
    ('conciliacion_islr', 'Conciliacion Fiscal Pro'),
    ('precios_transferencia', 'Precios de Transferencia'),
]


class PlanSuscripcion(models.Model):
    """Planes de suscripción SaaS configurables por el SuperAdmin."""

    nombre = models.CharField('nombre comercial del plan', max_length=100)
    codigo = models.SlugField('código único (identificador)', max_length=50, unique=True)
    etiqueta_badge = models.CharField('etiqueta badge', max_length=30, default='PRO', help_text='Ej: STARTER, PRO, ENTERPRISE, TEST')
    precio_mensual = models.DecimalField('precio mensual ($ USD)', max_digits=10, decimal_places=2, default=Decimal('10.00'))
    precio_anual = models.DecimalField('precio anual ($ USD)', max_digits=10, decimal_places=2, default=Decimal('80.00'))
    moneda = models.CharField('moneda', max_length=3, choices=MONEDAS, default='USD')
    limite_usuarios = models.PositiveIntegerField('límite de usuarios (0 = ilimitado)', default=1)
    limite_empresas = models.PositiveIntegerField('límite de empresas (0 = ilimitado)', default=5)
    mostrar_en_landing = models.BooleanField('mostrar en la página principal (Index / Landing)', default=True)
    incluye_ia = models.BooleanField('incluir motor de IA / módulos avanzados', default=False)
    api_propia = models.BooleanField('acceso a API Propia', default=False)
    modulos = models.JSONField('módulos incluidos', default=list, blank=True)
    activo = models.BooleanField('activo', default=True)
    orden = models.PositiveIntegerField('orden', default=0)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'planes_suscripcion'
        ordering = ['orden', 'precio_mensual', 'creado']
        verbose_name = 'plan de suscripción'
        verbose_name_plural = 'planes de suscripción'

    def __str__(self):
        return f'{self.nombre} (${self.precio_mensual}/mes)'

    @property
    def total_modulos(self):
        return len(self.modulos or [])

    @property
    def modulos_nombres(self):
        dict_nombres = dict(MODULOS_DISPONIBLES)
        return [dict_nombres.get(m, m) for m in (self.modulos or [])]


class Suscripcion(models.Model):
    """Mensualidad del contador. Sin suscripción vigente no puede usar los módulos."""

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='suscripcion',
    )
    plan = models.ForeignKey(
        PlanSuscripcion, null=True, blank=True, on_delete=models.SET_NULL, related_name='suscripciones',
    )
    activo = models.BooleanField('activa', default=False)
    vence = models.DateField('vence', null=True, blank=True)
    nota = models.CharField('nota', max_length=200, blank=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'suscripciones'
        verbose_name = 'suscripción'
        verbose_name_plural = 'suscripciones'

    def __str__(self):
        return f'Suscripción de {self.usuario}'

    @property
    def vigente(self):
        return bool(self.activo and (self.vence is None or self.vence >= timezone.localdate()))

    @property
    def esta_activa(self):
        return self.vigente

    @property
    def estado(self):
        if self.vigente:
            return 'Activo'
        return 'Vencido' if self.vence else 'Pendiente'

    @property
    def get_estado_display(self):
        return self.estado

    @property
    def estado_css(self):
        return {'Activo': 'success', 'Vencido': 'danger', 'Pendiente': 'warning'}[self.estado]

    @property
    def dias_restantes(self):
        if not self.vence:
            return None
        return (self.vence - timezone.localdate()).days

    @property
    def fecha_fin(self):
        return self.vence

    def registrar_pago(self, monto, moneda='USD', dias=None, registrado_por=None, nota='', referencia='', metodo='pago_movil', plan=None, ciclo='mensual', estado='aprobado'):
        dias = dias or settings.TRIBUTOVE.get('DIAS_POR_PAGO', 30)
        hoy = timezone.localdate()
        if estado == 'aprobado':
            base = self.vence if self.vence and self.vence > hoy else hoy
            self.vence = base + timedelta(days=dias)
            self.activo = True
            if plan:
                self.plan = plan
            self.save()
        return Pago.objects.create(
            suscripcion=self, plan=plan or self.plan, monto=monto or Decimal('0'), moneda=moneda, dias=dias,
            ciclo=ciclo, estado=estado, registrado_por=registrado_por, nota=nota, referencia=referencia, metodo=metodo,
        )


ESTADOS_PAGO = [
    ('pendiente', 'Pendiente'),
    ('aprobado', 'Aprobado'),
    ('rechazado', 'Rechazado'),
]

CICLOS_PAGO = [
    ('mensual', 'Mensual'),
    ('anual', 'Anual'),
]


class Pago(models.Model):
    suscripcion = models.ForeignKey(Suscripcion, on_delete=models.CASCADE, related_name='pagos')
    plan = models.ForeignKey(
        PlanSuscripcion, null=True, blank=True, on_delete=models.SET_NULL, related_name='pagos',
    )
    fecha = models.DateField('fecha', default=timezone.localdate)
    monto = models.DecimalField('monto', max_digits=14, decimal_places=2, default=0)
    moneda = models.CharField('moneda', max_length=3, choices=MONEDAS, default='USD')
    dias = models.PositiveIntegerField('días agregados', default=30)
    ciclo = models.CharField('ciclo de facturación', max_length=20, choices=CICLOS_PAGO, default='mensual')
    estado = models.CharField('estado del pago', max_length=20, choices=ESTADOS_PAGO, default='aprobado')
    metodo = models.CharField('método de pago', max_length=30, choices=METODOS_PAGO, default='pago_movil', blank=True)
    referencia = models.CharField('referencia / comprobante', max_length=60, blank=True)
    nota = models.CharField('nota', max_length=200, blank=True)
    registrado_por = models.ForeignKey(
        'superadmin.SuperAdmin', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='pagos_registrados',
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pagos'
        ordering = ['-fecha', '-creado']
        verbose_name = 'pago'
        verbose_name_plural = 'pagos'

    def __str__(self):
        return f'{self.moneda} {self.monto} · {self.fecha:%d/%m/%Y} ({self.get_estado_display()})'

    @property
    def dias_agregados(self):
        return self.dias

    def aprobar(self, admin=None):
        self.estado = 'aprobado'
        if admin:
            self.registrado_por = admin
        self.save()
        # Extender la suscripción
        hoy = timezone.localdate()
        sus = self.suscripcion
        base = sus.vence if sus.vence and sus.vence > hoy else hoy
        sus.vence = base + timedelta(days=self.dias)
        sus.activo = True
        if self.plan:
            sus.plan = self.plan
        sus.save()

    def rechazar(self, admin=None, motivo=''):
        self.estado = 'rechazado'
        if admin:
            self.registrado_por = admin
        if motivo:
            self.nota = f'{self.nota} [Rechazado: {motivo}]'.strip()
        self.save()


class ConfiguracionPago(models.Model):
    """Configuración general de la mensualidad y datos de cobro bancario."""

    monto = models.DecimalField('monto mensual ($)', max_digits=14, decimal_places=2, null=True, blank=True, default=Decimal('10.00'))
    monto_anual = models.DecimalField('monto anual ($)', max_digits=14, decimal_places=2, null=True, blank=True, default=Decimal('100.00'))
    moneda = models.CharField('moneda base', max_length=3, choices=MONEDAS, default='USD')
    contacto = models.CharField('contacto (WhatsApp o correo)', max_length=150, blank=True)
    instrucciones = models.TextField('instrucciones generales', blank=True)

    # Pago Móvil
    pago_movil_banco = models.CharField('banco pago móvil', max_length=80, blank=True)
    pago_movil_telefono = models.CharField('teléfono pago móvil', max_length=40, blank=True)
    pago_movil_rif = models.CharField('cédula / RIF pago móvil', max_length=30, blank=True)

    # Transferencia bancaria nacional
    transferencia_banco = models.CharField('banco transferencia', max_length=80, blank=True)
    transferencia_beneficiario = models.CharField('beneficiario transferencia', max_length=120, blank=True)
    transferencia_cuenta = models.CharField('número de cuenta transferencia (20 dígitos)', max_length=30, blank=True)

    # Zelle
    zelle_correo = models.CharField('correo Zelle', max_length=120, blank=True)
    zelle_titular = models.CharField('titular Zelle', max_length=120, blank=True)

    class Meta:
        db_table = 'configuracion_pago'
        verbose_name = 'configuración de pago'

    def __str__(self):
        return 'Configuración de pago'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def obtener(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def monto_mensualidad_usd(self):
        return self.monto
