from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('inicio/', views.inicio, name='inicio'),
    path('landing/', views.landing_redirect, name='landing_redirect'),
    path('manifest.json', views.manifest_view, name='manifest'),
    path('sw.js', views.service_worker_view, name='service_worker'),
    path('offline/', views.offline_view, name='offline'),
]