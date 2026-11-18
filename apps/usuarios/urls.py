from django.urls import path

from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('recuperar-clave/', views.recuperar_view, name='recuperar'),
    path('mi-cuenta/', views.mi_cuenta_view, name='mi_cuenta'),
]
