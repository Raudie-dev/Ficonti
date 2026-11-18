from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'iva'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'iva'
    template_name = 'retenciones_iva/calculadora.html'
