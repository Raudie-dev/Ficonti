"""
Registro central de los módulos fiscales de TributoVE.

Cada módulo es una aplicación Django independiente (``apps.<app>``). Este
registro sólo describe metadatos comunes (nombre, grupo del menú, ícono,
banderas) para construir el sidebar, el resumen de estatus, etc.
"""

from dataclasses import dataclass

from django.urls import reverse


@dataclass(frozen=True)
class Modulo:
    codigo: str          # identificador corto (se usa en estatus y en los JS)
    app: str             # nombre de la aplicación Django / namespace de URLs
    nombre: str          # nombre completo
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


# Orden del menú lateral
MODULOS = [
    Modulo('plan', 'planificacion', 'Planificación fiscal', 'Planificación', 'Planificación',
           'bi-graph-up-arrow', 'Planificación fiscal para sujetos pasivos especiales.',
           solo_spe=True, solo_bs=True),
    Modulo('ret', 'retenciones_islr', 'Retenciones de ISLR', 'Ret. ISLR', 'Consultas',
           'bi-search', 'Consultor de retenciones de ISLR (Decreto 1.808).', consulta=True),
    Modulo('iva', 'retenciones_iva', 'Retenciones de IVA', 'Ret. IVA', 'Consultas',
           'bi-receipt', 'Calculadora y libro de retenciones de IVA.', solo_spe=True),
    Modulo('cal', 'calendario', 'Calendario fiscal', 'Calendario', 'Consultas',
           'bi-calendar-event', 'Obligaciones fiscales de contribuyentes especiales.',
           solo_spe=True, consulta=True),
    Modulo('dif', 'impuesto_diferido', 'Impuesto diferido', 'Imp. diferido', 'Contabilidad fiscal',
           'bi-hourglass-split', 'NIC 12, Sección 29 y BA VEN-NIF 11.', solo_spe=True),
    Modulo('igp', 'grandes_patrimonios', 'Grandes patrimonios', 'Gr. patrimonios', 'Contabilidad fiscal',
           'bi-bank', 'Impuesto a los Grandes Patrimonios.'),
    Modulo('conc', 'conciliacion', 'Conciliación bancaria', 'Conciliación', 'Contabilidad fiscal',
           'bi-arrow-left-right', 'Conciliación multicuenta con retenciones IVA/ISLR.'),
    Modulo('aif', 'ajuste_inicial', 'Ajuste inicial fiscal', 'Ajuste inicial', 'Contabilidad fiscal',
           'bi-sliders', 'Actualización de activos y pasivos no monetarios.'),
    Modulo('ced', 'cedula_fiscal', 'Cédula fiscal', 'Cédula fiscal', 'Contabilidad fiscal',
           'bi-journal-text', 'Conciliación fiscal y liquidación del ISLR.'),
]

MODULOS_POR_CODIGO = {m.codigo: m for m in MODULOS}

# Orden de las columnas del resumen de estatus
ORDEN_RESUMEN = ['plan', 'iva', 'ret', 'cal', 'dif', 'igp', 'conc', 'aif', 'ced']
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
