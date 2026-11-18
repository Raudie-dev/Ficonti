from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'cislr'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'cislr'
    template_name = 'conciliacion_islr/calculadora.html'
