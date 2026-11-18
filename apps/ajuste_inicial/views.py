from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'aif'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'aif'
    template_name = 'ajuste_inicial/calculadora.html'
