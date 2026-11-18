from decimal import Decimal
from django.test import Client, TestCase
from django.urls import reverse

from apps.core.modulos import MODULOS
from apps.empresas.models import DatoModulo, Empresa, EstadoModulo
from apps.superadmin.models import SuperAdmin
from apps.suscripciones.models import Suscripcion
from apps.usuarios.models import Usuario


class TributoVETestSuite(TestCase):
    def setUp(self):
        # Crear superadmin
        self.superadmin = SuperAdmin.objects.create(
            usuario='superadmin_test',
            nombre='SuperAdmin Tester',
            email='sa@test.com',
            is_active=True,
        )
        self.superadmin.set_password('AdminPass123!')
        self.superadmin.save()

        # Crear contador con suscripción activa
        self.contador = Usuario.objects.create(
            usuario='contador_test',
            nombre='Contador Tester',
            telefono='0414-1112233',
            email='contador@test.com',
            is_active=True,
        )
        self.contador.set_password('ContadorPass123!')
        self.contador.save()

        self.suscripcion = Suscripcion.objects.get(usuario=self.contador)
        self.suscripcion.activo = True
        self.suscripcion.save()

        # Crear empresa
        self.empresa = Empresa.objects.create(
            usuario=self.contador,
            nombre='Inversiones Alfa C.A.',
            rif='J-12345678-0',
            condicion='Sujeto pasivo especial',
            moneda='USD',
            tasa=Decimal('65.0000'),
        )

    def test_login_usuario_normal(self):
        """Verifica que el usuario normal inicia sesión en /login/ y accede al sistema."""
        client = Client()
        res = client.post(reverse('usuarios:login'), {
            'usuario': 'contador_test',
            'clave': 'ContadorPass123!',
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Inversiones Alfa C.A.')

    def test_login_superadmin_aislado(self):
        """Verifica que el superadmin inicia sesión en /superadmin/login/ y accede al panel."""
        client = Client()
        res = client.post(reverse('superadmin:login'), {
            'usuario': 'superadmin_test',
            'clave': 'AdminPass123!',
        })
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('superadmin:panel'))

        res_panel = client.get(reverse('superadmin:panel'))
        self.assertEqual(res_panel.status_code, 200)
        self.assertContains(res_panel, 'Panel de Control General')
        self.assertContains(res_panel, 'SUPERADMIN')

    def test_usuario_normal_no_puede_entrar_a_superadmin(self):
        """Un usuario normal autenticado no debe poder entrar al panel de superadmin."""
        client = Client()
        client.login(usuario='contador_test', password='ContadorPass123!')

        res = client.get(reverse('superadmin:panel'))
        self.assertEqual(res.status_code, 302)
        self.assertIn('/superadmin/login/', res.url)

    def test_todos_los_9_modulos_fiscales(self):
        """Verifica que cada uno de los 9 módulos y sus calculadoras renderizan correctamente."""
        client = Client()
        client.login(usuario='contador_test', password='ContadorPass123!')

        session = client.session
        session['empresa_activa'] = self.empresa.pk
        session.save()

        for m in MODULOS:
            with self.subTest(modulo=m.codigo):
                res_index = client.get(reverse(f'{m.app}:index'))
                self.assertEqual(res_index.status_code, 200)
                self.assertContains(res_index, 'moduloFrame')

                res_calc = client.get(reverse(f'{m.app}:calculadora'))
                self.assertEqual(res_calc.status_code, 200)
                self.assertContains(res_calc, 'tv-bridge')

    def test_sincronizacion_datos_modulo(self):
        """Verifica el guardado vía AJAX de datos de módulo en el servidor."""
        client = Client()
        client.login(usuario='contador_test', password='ContadorPass123!')

        url = reverse('empresas:datos_modulo', args=[self.empresa.pk])
        payload = {'aif_activos': '[{"desc":"Maquinaria","costo":15000}]'}
        res = client.post(url, data=payload, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()['ok'])

        # Verificar en base de datos
        dato = DatoModulo.objects.get(empresa=self.empresa, clave='aif_activos')
        self.assertIn('Maquinaria', dato.valor)

    def test_sincronizacion_estado_modulo(self):
        """Verifica la recepción de postMessage/estado en la base de datos."""
        client = Client()
        client.login(usuario='contador_test', password='ContadorPass123!')

        url = reverse('empresas:estado_modulo', args=[self.empresa.pk])
        payload = {'modulo': 'aif', 'estado': 'ok', 'detalle': 'Calculado y conciliado'}
        res = client.post(url, data=payload, content_type='application/json')
        self.assertEqual(res.status_code, 200)

        estado = EstadoModulo.objects.get(empresa=self.empresa, modulo='aif')
        self.assertEqual(estado.estado, 'ok')
        self.assertEqual(estado.detalle, 'Calculado y conciliado')

    def test_pwa_manifest_y_service_worker(self):
        """Verifica la disponibilidad de manifest.json, sw.js y la página offline de la PWA."""
        client = Client()

        # 1. Manifest
        res_manifest = client.get(reverse('core:manifest'))
        self.assertEqual(res_manifest.status_code, 200)
        self.assertIn('application/manifest+json', res_manifest['Content-Type'])
        data = res_manifest.json()
        self.assertEqual(data['short_name'], 'TributoVE')
        self.assertEqual(data['display'], 'standalone')
        self.assertTrue(len(data['icons']) >= 2)

        # 2. Service Worker
        res_sw = client.get(reverse('core:service_worker'))
        self.assertEqual(res_sw.status_code, 200)
        self.assertIn('application/javascript', res_sw['Content-Type'])
        self.assertEqual(res_sw['Service-Worker-Allowed'], '/')
        self.assertContains(res_sw, 'tributove')

        # 3. Offline fallback
        res_offline = client.get(reverse('core:offline'))
        self.assertEqual(res_offline.status_code, 200)
        self.assertContains(res_offline, 'Sin Conexión')
