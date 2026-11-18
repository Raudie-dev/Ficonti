from django.urls import path

from . import views

app_name = 'empresas'

urlpatterns = [
    path('', views.lista, name='lista'),
    path('resumen/', views.resumen, name='resumen'),
    path('activar/', views.activar, name='activar_select'),
    path('<int:pk>/activar/', views.activar, name='activar'),
    path('<int:pk>/editar/', views.editar, name='editar'),
    path('<int:pk>/eliminar/', views.eliminar, name='eliminar'),
    path('<int:pk>/moneda/', views.moneda, name='moneda'),
    # API JSON de los módulos
    path('<int:pk>/estado/', views.estado_modulo, name='estado_modulo'),
    path('<int:pk>/datos/', views.datos_modulo, name='datos_modulo'),
]
