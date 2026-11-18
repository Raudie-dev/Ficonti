from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'ced'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'ced'
    template_name = 'cedula_fiscal/calculadora.html'
