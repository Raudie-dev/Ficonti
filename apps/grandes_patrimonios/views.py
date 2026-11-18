from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'igp'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'igp'
    template_name = 'grandes_patrimonios/calculadora.html'
