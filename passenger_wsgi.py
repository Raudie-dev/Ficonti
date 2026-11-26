import os
import sys

# Rutas del proyecto para despliegue en cPanel con Phusion Passenger
BASE_DIR = '/home/ficovppl/Ficonti'
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Incluir las rutas en sys.path para resolución de módulos y paquetes Django
for p in [
    BASE_DIR,
    os.path.join(BASE_DIR, 'confi'),
    os.path.join(BASE_DIR, 'tributove'),
    CURRENT_DIR,
]:
    if p and p not in sys.path:
        sys.path.insert(0, p)

# Módulo de configuración de Django del proyecto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tributove.settings')

# Carga de la aplicación WSGI
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
