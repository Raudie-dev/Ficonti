from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'conc'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'conc'
    template_name = 'conciliacion/calculadora.html'
