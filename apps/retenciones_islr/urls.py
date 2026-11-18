from django.urls import path
from . import views

app_name = 'retenciones_islr'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('calc/', views.CalculadoraView.as_view(), name='calculadora'),
]
