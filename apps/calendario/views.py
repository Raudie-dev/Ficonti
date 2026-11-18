from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'cal'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'cal'
    template_name = 'calendario/calculadora.html'
