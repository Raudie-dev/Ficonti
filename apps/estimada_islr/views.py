from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'est'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'est'
    template_name = 'estimada_islr/calculadora.html'
