from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'ret'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'ret'
    template_name = 'retenciones_islr/calculadora.html'
