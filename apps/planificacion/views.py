from apps.core.views_modulo import ModuloCalculadoraView, ModuloIndexView


class IndexView(ModuloIndexView):
    codigo = 'plan'


class CalculadoraView(ModuloCalculadoraView):
    codigo = 'plan'
    template_name = 'planificacion/calculadora.html'
