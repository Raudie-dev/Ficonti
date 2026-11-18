from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'pt'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'pt'
    template_name = 'precios_transferencia/calculadora.html'
