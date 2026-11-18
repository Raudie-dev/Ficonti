from django.urls import path

from . import views

app_name = 'superadmin'

urlpatterns = [
    path('login/', views.login_admin, name='login'),
    path('logout/', views.logout_admin, name='logout'),
    path('', views.panel, name='panel'),
    # Contadores (usuarios normales)
    path('contadores/', views.contadores, name='contadores'),
    path('contadores/nuevo/', views.contador_crear, name='contador_crear'),
    path('contadores/<int:pk>/', views.contador_detalle, name='contador_detalle'),
    path('contadores/<int:pk>/editar/', views.contador_editar, name='contador_editar'),
    path('contadores/<int:pk>/clave/', views.contador_clave, name='contador_clave'),
    path('contadores/<int:pk>/eliminar/', views.contador_eliminar, name='contador_eliminar'),
    path('contadores/<int:pk>/suscripcion/', views.contador_suscripcion, name='contador_suscripcion'),
    path('contadores/<int:pk>/alternar/', views.contador_alternar, name='contador_alternar'),
    path('contadores/<int:pk>/pago/', views.contador_pago, name='contador_pago'),
    # Empresas, estatus y pagos
    path('empresas/', views.empresas, name='empresas'),
    path('estatus/', views.estatus, name='estatus'),
    path('pagos/', views.pagos, name='pagos'),
    path('pagos/<int:pk>/aprobar/', views.pago_aprobar, name='pago_aprobar'),
    path('pagos/<int:pk>/rechazar/', views.pago_rechazar, name='pago_rechazar'),
    path('pagos/<int:pk>/eliminar/', views.pago_eliminar, name='pago_eliminar'),
    path('planes/', views.planes_configuracion, name='planes'),
    path('planes/crear/', views.plan_crear, name='plan_crear'),
    path('planes/<int:pk>/editar/', views.plan_editar, name='plan_editar'),
    path('planes/<int:pk>/eliminar/', views.plan_eliminar, name='plan_eliminar'),
    path('planes/cobro/', views.planes_cobro, name='planes_cobro'),
    # Super administradores
    path('administradores/', views.administradores, name='administradores'),
    path('administradores/nuevo/', views.administrador_crear, name='administrador_crear'),
    path('administradores/<int:pk>/editar/', views.administrador_editar, name='administrador_editar'),
    path('administradores/<int:pk>/eliminar/', views.administrador_eliminar, name='administrador_eliminar'),
    path('mi-cuenta/', views.mi_cuenta, name='mi_cuenta'),
]
