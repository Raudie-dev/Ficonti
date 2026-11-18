from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'dif'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'dif'
    template_name = 'impuesto_diferido/calculadora.html'
