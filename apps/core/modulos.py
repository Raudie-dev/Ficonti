"""
Registro central de los módulos fiscales de TributoVE.

Cada módulo es una aplicación Django independiente (``apps.<app>``). Este
registro sólo describe metadatos comunes (nombre, grupo del menú, ícono,
banderas) para construir el sidebar desplegable (Menús 1, 2, 3 y 4),
el resumen de estatus, etc.
"""

from dataclasses import dataclass

from django.urls import reverse


@dataclass(frozen=True)
class Modulo:
    codigo: str          # identificador corto (se usa en estatus y en los JS)
    app: str             # nombre de la aplicación Django / namespace de URLs
    nombre: str          # nombre completo en el menú lateral
    corto: str           # nombre corto para tablas
    grupo: str           # grupo del menú lateral
    icono: str           # clase de Bootstrap Icons
    descripcion: str = ''
    solo_spe: bool = False   # pensado para sujetos pasivos especiales
    solo_bs: bool = False    # trabaja siempre en bolívares
    consulta: bool = False   # módulo de consulta (no genera estatus)

    @property
    def url(self):
        return reverse(f'{self.app}:index')

    @property
    def url_name(self):
        return f'{self.app}:index'

    @property
    def categoria(self):
        return self.grupo

    @property
    def trackeable(self):
        return not self.consulta


# Módulos activos del Panel de Usuario Ajustado (Menús 1, 2 y 3)
# Se eliminaron del menú: Impuesto diferido (dif), Ajuste inicial fiscal (aif) y Cédula fiscal (ced).
MODULOS = [
    # 1. PLANIFICACIÓN
    Modulo('plan', 'planificacion', 'Planificación fiscal', 'Planificación', 'Planificación',
           'bi-graph-up-arrow', 'Planificación fiscal para sujetos pasivos especiales.',
           solo_spe=True, solo_bs=True),

    # 2. CONSULTAS
    Modulo('ret', 'retenciones_islr', 'Retenciones (ISLR)', 'Ret. ISLR', 'Consultas',
           'bi-search', 'Consultor de retenciones de ISLR (Decreto 1.808).', consulta=True),
    Modulo('sanc', 'sanciones_cot', 'Simulador Sanciones', 'Sanciones', 'Consultas',
           'bi-shield-exclamation', 'Simulador de sanciones SENIAT (COT 2020), concurrencia e intereses moratorios.',
           consulta=True),
    Modulo('cal', 'calendario', 'Calendario fiscal', 'Calendario', 'Consultas',
           'bi-calendar-event', 'Obligaciones fiscales de contribuyentes especiales.',
           solo_spe=True, consulta=True),

    # 3. CONTABILIDAD FISCAL
    Modulo('ari', 'calculo_ari', 'Calculo ARI', 'Cálculo ARI', 'Contabilidad fiscal',
           'bi-person-badge', 'Determinación del porcentaje de retención ISLR sobre sueldos y salarios (Formulario AR-I).',
           solo_bs=True),
    Modulo('est', 'estimada_islr', 'ISLR Estimada', 'ISLR Estimada', 'Contabilidad fiscal',
           'bi-calculator', 'Declaración estimada de rentas personas jurídicas (Arts. 156 y 158 RLISLR).',
           solo_bs=True),
    Modulo('igp', 'grandes_patrimonios', 'Grandes patrimonios', 'Gr. patrimonios', 'Contabilidad fiscal',
           'bi-bank', 'Impuesto a los Grandes Patrimonios (IGP).'),
    Modulo('ing', 'auditoria_ingresos', 'Conciliacion Ingresos', 'Concil. Ingresos', 'Contabilidad fiscal',
           'bi-funnel-fill', 'Separación y conciliación de ingresos gravables vs. abonos no gravables para auditorías bancarias.'),
    Modulo('conc', 'conciliacion', 'Conciliación bancaria', 'Concil. Bancaria', 'Contabilidad fiscal',
           'bi-arrow-left-right', 'Conciliación multicuenta con retenciones IVA/ISLR y asientos.'),
    Modulo('cislr', 'conciliacion_islr', 'Conciliacion Fiscal Pro (8)', 'Fiscal Pro (8)', 'Contabilidad fiscal',
           'bi-file-earmark-spreadsheet', 'Balance de comprobación, conciliación Art. 27, API, Dec. 1.808, dictamen y 25 reglas.'),
    Modulo('pt', 'precios_transferencia', 'Precios de Transferencia', 'Precios Transf.', 'Contabilidad fiscal',
           'bi-globe-americas', 'Operaciones con partes vinculadas (OCDE / PT-99), rango intercuartil y análisis funcional.'),
]

# Módulos legados (mantenidos en diccionario por compatibilidad de rutas internas)
_MODULOS_LEGADOS = [
    Modulo('iva', 'retenciones_iva', 'Retenciones de IVA', 'Ret. IVA', 'Consultas',
           'bi-receipt', 'Calculadora y libro de retenciones de IVA.', solo_spe=True),
    Modulo('cban', 'control_bancario', 'Control bancario 6 cuentas', 'Control 6 bancos', 'Contabilidad fiscal',
           'bi-columns-gap', 'Cruce automático de traspasos entre 6 bancos editables, tasas BCV y Libro de Ventas.'),
    Modulo('ced', 'cedula_fiscal', 'Cédula fiscal', 'Cédula fiscal', 'Contabilidad fiscal',
           'bi-journal-text', 'Conciliación fiscal mensual y liquidación del ISLR.'),
    Modulo('aif', 'ajuste_inicial', 'Ajuste inicial fiscal', 'Ajuste inicial', 'Contabilidad fiscal',
           'bi-sliders', 'Actualización de activos y pasivos no monetarios (RAR).'),
    Modulo('dif', 'impuesto_diferido', 'Impuesto diferido', 'Imp. diferido', 'Contabilidad fiscal',
           'bi-hourglass-split', 'NIC 12, Sección 29 y BA VEN-NIF 11.', solo_spe=True),
]

MODULOS_POR_CODIGO = {m.codigo: m for m in (_MODULOS_LEGADOS + MODULOS)}

# Orden de las columnas del resumen de estatus (los 11 módulos del Panel Ajustado)
ORDEN_RESUMEN = [
    'plan', 'ret', 'sanc', 'cal',
    'ari', 'est', 'igp', 'ing', 'conc', 'cislr', 'pt',
]
MODULOS_RESUMEN = [MODULOS_POR_CODIGO[c] for c in ORDEN_RESUMEN]


def obtener_modulo(codigo):
    return MODULOS_POR_CODIGO.get(codigo)


def menu_agrupado():
    """Devuelve [(grupo, [modulos...]), ...] preservando el orden."""
    grupos = []
    for m in MODULOS:
        if not grupos or grupos[-1][0] != m.grupo:
            grupos.append((m.grupo, []))
        grupos[-1][1].append(m)
    return grupos
