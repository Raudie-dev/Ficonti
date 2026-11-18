from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'sanc'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'sanc'
    template_name = 'sanciones_cot/calculadora.html'
