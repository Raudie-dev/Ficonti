from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'ari'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'ari'
    template_name = 'calculo_ari/calculadora.html'
