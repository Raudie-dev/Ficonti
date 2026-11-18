from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.empresas.models import Empresa
from apps.superadmin.models import SuperAdmin
from apps.suscripciones.models import ConfiguracionPago, Suscripcion
from apps.usuarios.models import Usuario


class Command(BaseCommand):
    help = 'Inicializa el SuperAdmin inicial, configuración de pagos y datos de prueba.'

    def handle(self, *args, **options):
        # 1. SuperAdmin
        admin, creado = SuperAdmin.objects.get_or_create(
            usuario='admin',
            defaults={
                'nombre': 'Administrador Principal',
                'email': 'admin@tributove.com',
                'is_active': True,
            }
        )
        if creado:
            admin.set_password('admin12345')
            admin.save()
            self.stdout.write(self.style.SUCCESS('SuperAdmin creado: usuario "admin", clave "admin12345"'))
        else:
            self.stdout.write('SuperAdmin "admin" ya existía.')

        # 2. Configuración de pagos
        config = ConfiguracionPago.obtener()
        config.monto = Decimal('10.00')
        config.moneda = 'USD'
        config.pago_movil_banco = '0134 - Banesco'
        config.pago_movil_telefono = '0414-1234567'
        config.pago_movil_rif = 'V-12345678-0'
        config.transferencia_banco = '0134 - Banesco Banco Universal'
        config.transferencia_cuenta = '01340001000012345678'
        config.transferencia_beneficiario = 'TributoVE Soluciones C.A.'
        config.zelle_correo = 'pagos@tributove.com'
        config.zelle_titular = 'TributoVE LLC'
        config.save()
        self.stdout.write(self.style.SUCCESS('Configuración de pagos establecida.'))

        # 3. Contador de demostración
        contador, creado_c = Usuario.objects.get_or_create(
            usuario='contador',
            defaults={
                'nombre': 'Lic. Carlos Mendoza (CPC)',
                'telefono': '0412-9876543',
                'email': 'carlos.mendoza@ejemplo.com',
                'is_active': True,
            }
        )
        if creado_c:
            contador.set_password('contador12345')
            contador.save()
            self.stdout.write(self.style.SUCCESS('Contador de prueba creado: usuario "contador", clave "contador12345"'))
        else:
            self.stdout.write('Contador "contador" ya existía.')

        # Activar suscripción por 30 días
        suscripcion, _ = Suscripcion.objects.get_or_create(usuario=contador)
        suscripcion.activo = True
        suscripcion.vence = timezone.localdate() + timedelta(days=30)
        suscripcion.nota = 'Activación de bienvenida / demostración'
        suscripcion.save()

        # 4. Empresa de demostración
        empresa, creada_e = Empresa.objects.get_or_create(
            usuario=contador,
            rif='J-31245678-9',
            defaults={
                'nombre': 'Servicios y Suministros Caracas, C.A.',
                'condicion': 'Sujeto pasivo especial',
                'moneda': 'USD',
                'tasa': Decimal('66.5000'),
            }
        )
        if creada_e:
            self.stdout.write(self.style.SUCCESS(f'Empresa demo creada: "{empresa.nombre}"'))
        else:
            self.stdout.write(f'Empresa "{empresa.nombre}" ya existía.')

        self.stdout.write(self.style.SUCCESS('\n=== Sistema inicializado con éxito ==='))
        self.stdout.write('Portal Contadores:    /login/           (contador / contador12345)')
        self.stdout.write('Portal SuperAdmin:    /superadmin/login/ (admin / admin12345)')
