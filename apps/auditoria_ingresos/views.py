from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'ing'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'ing'
    template_name = 'auditoria_ingresos/calculadora.html'
