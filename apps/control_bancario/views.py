from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'cban'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'cban'
    template_name = 'control_bancario/calculadora.html'
