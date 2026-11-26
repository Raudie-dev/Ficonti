"""
Vistas genéricas que heredan las aplicaciones de cada módulo fiscal.

Cada módulo tiene dos vistas:

* ``index``: página completa (hereda ``layouts/app.html`` con sidebar y
  navbar) que muestra la calculadora del módulo.
* ``calculadora``: documento HTML aislado de la calculadora, cargado dentro
  de la página anterior. Recibe la empresa activa y los datos guardados en el
  servidor.
"""

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.generic import TemplateView

from apps.empresas.context_processors import fijar_empresa_activa, obtener_empresa_activa

from .bcv import obtener_tasas_bcv
from .mixins import ContadorRequiredMixin, SuscripcionRequeridaMixin
from .modulos import obtener_modulo


class ModuloMixin:
    codigo = None  # p. ej. 'aif'

    def get_modulo(self):
        modulo = obtener_modulo(self.codigo)
        if modulo is None:
            raise Http404('Módulo no registrado')
        return modulo


class ModuloIndexView(ContadorRequiredMixin, SuscripcionRequeridaMixin, ModuloMixin, TemplateView):
    template_name = 'modulos/pagina.html'

    def get(self, request, *args, **kwargs):
        self.modulo = self.get_modulo()
        # Permite abrir el módulo para una empresa concreta (?empresa=<id>)
        pk = request.GET.get('empresa')
        if pk:
            empresa = request.user.empresas.filter(pk=pk).first()
            if empresa:
                fijar_empresa_activa(request, empresa)
            return redirect(reverse(self.modulo.url_name))
        self.empresa = obtener_empresa_activa(request)
        if self.empresa is None:
            return render(request, 'modulos/sin_empresa.html', {'modulo': self.modulo})
        request.user.registrar_uso(self.modulo.codigo)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'modulo': self.modulo,
            'empresa': self.empresa,
            'url_calculadora': reverse(f'{self.modulo.app}:calculadora'),
            'url_estado': reverse('empresas:estado_modulo', args=[self.empresa.pk]),
        })
        return ctx


@method_decorator(xframe_options_sameorigin, name='dispatch')
class ModuloCalculadoraView(ContadorRequiredMixin, SuscripcionRequeridaMixin, ModuloMixin, TemplateView):
    template_name = None  # '<app>/calculadora.html'

    def get(self, request, *args, **kwargs):
        self.modulo = self.get_modulo()
        self.empresa = obtener_empresa_activa(request)
        if self.empresa is None:
            return render(request, 'modulos/sin_empresa.html', {'modulo': self.modulo})
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['modulo'] = self.modulo
        ctx['empresa'] = self.empresa
        bcv = obtener_tasas_bcv(forzar=False, permitir_red=False)
        emp_data = self.empresa.datos_modulo(self.modulo)
        emp_data['bcv'] = bcv
        ctx['tv_config'] = {
            'modulo': self.modulo.codigo,
            'empresa': json.dumps(emp_data, cls=DjangoJSONEncoder, ensure_ascii=False).replace('</', '<\\/'),
            'bcv': json.dumps(bcv, cls=DjangoJSONEncoder, ensure_ascii=False).replace('</', '<\\/'),
            'urlBcv': reverse('core:api_tasa_bcv'),
            'datos': json.dumps({d.clave: d.valor for d in self.empresa.datos.all()}, cls=DjangoJSONEncoder, ensure_ascii=False).replace('</', '<\\/'),
            'urlDatos': reverse('empresas:datos_modulo', args=[self.empresa.pk]),
            'csrf': get_token(self.request),
        }
        return ctx
