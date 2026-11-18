from django.urls import path
from . import views

app_name = 'cedula_fiscal'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('calc/', views.CalculadoraView.as_view(), name='calculadora'),
]
