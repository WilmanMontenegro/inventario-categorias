from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from inventario.models import Inventario, LineaCarrito, confirmar_compra
from inventario.models import Carrito, Empresa


class CompraDemoTests(TestCase):
    def setUp(self):
        from django.core.management import call_command

        call_command("seed_demo")

    def test_login_y_catalogo(self):
        client = Client()
        self.assertEqual(client.get("/entrar/").status_code, 200)
        resp = client.post(
            "/entrar/",
            {"usuario": "unilago", "clave": "demo1234"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "CONT-DEMO-001")
        self.assertContains(resp, "DEMO")
        self.assertContains(resp, "Computadores")
        self.assertContains(resp, "Periféricos")
        self.assertContains(resp, "/media/productos/")
        self.assertContains(resp, "Portátil 14 pulgadas")
        from inventario.models import Categoria
        self.assertTrue(Categoria.objects.get(nombre="Periféricos").descripcion)

    def test_admin_login_redirige_a_entrar(self):
        client = Client()
        resp = client.get("/admin/login/?next=/admin/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/entrar/")

    def test_filtro_categoria(self):
        from django.contrib.auth import get_user_model
        from inventario.models import Categoria

        client = Client()
        client.force_login(get_user_model().objects.get(username="unilago"))
        cat = Categoria.objects.get(nombre="Componentes")
        resp = client.get(f"/catalogo/?categoria={cat.pk}")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "SSD 1TB DEMO")
        self.assertNotContains(resp, "Mouse inalámbrico DEMO")

    def test_confirmar_baja_stock(self):
        empresa = Empresa.objects.get(nit="900123456-1")
        inv = Inventario.objects.select_related("container").first()
        stock_antes = inv.cantidad
        carrito = Carrito.objects.create(
            empresa=empresa, container=inv.container, abierto=True
        )
        LineaCarrito.objects.create(
            carrito=carrito,
            inventario=inv,
            cantidad=2,
            precio_unitario=inv.precio_venta,
        )
        factura = confirmar_compra(carrito)
        inv.refresh_from_db()
        self.assertEqual(inv.cantidad, stock_antes - 2)
        self.assertTrue(factura.numero.startswith("FAC-DEMO-"))
        carrito.refresh_from_db()
        self.assertFalse(carrito.abierto)

    def test_sin_stock_falla(self):
        empresa = Empresa.objects.get(nit="900123456-1")
        inv = Inventario.objects.first()
        carrito = Carrito.objects.create(
            empresa=empresa, container=inv.container, abierto=True
        )
        LineaCarrito.objects.create(
            carrito=carrito,
            inventario=inv,
            cantidad=inv.cantidad + 5,
            precio_unitario=inv.precio_venta,
        )
        with self.assertRaises(ValidationError):
            confirmar_compra(carrito)

    def test_salir_get_cierra_sesion(self):
        from django.contrib.auth import get_user_model

        client = Client()
        client.force_login(get_user_model().objects.get(username="unilago"))
        resp = client.get("/salir/", follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Entrar")
        self.assertNotIn("_auth_user_id", client.session)
        self.assertEqual(client.get("/catalogo/").status_code, 302)

    def test_badge_habla_de_unidades(self):
        from django.contrib.auth import get_user_model

        client = Client()
        client.force_login(get_user_model().objects.get(username="unilago"))
        resp = client.get("/catalogo/")
        self.assertContains(resp, "unidad")

    def test_producto_detalle(self):
        from django.contrib.auth import get_user_model

        client = Client()
        client.force_login(get_user_model().objects.get(username="unilago"))
        inv = Inventario.objects.select_related("producto").first()
        resp = client.get(reverse("producto_detalle", args=[inv.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, inv.producto.nombre)
        self.assertContains(resp, "Volver al catálogo")
        self.assertContains(resp, "Agregar")
        # Card del catálogo enlaza a la ficha
        cat = client.get("/catalogo/")
        self.assertContains(cat, reverse("producto_detalle", args=[inv.pk]))


class CategoriaModalAdminTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        from django.core.management import call_command

        call_command("seed_demo")
        self.client = Client()
        self.client.force_login(get_user_model().objects.get(username="admin"))

    def test_agregar_modal_crea(self):
        from inventario.models import Categoria

        url = reverse("admin:inventario_categoria_agregar")
        self.assertContains(self.client.get(url), "Agregar categoría")
        resp = self.client.post(
            url,
            {
                "nombre": "Nueva demo",
                "descripcion": "Solo para test",
                "_form_submitted": "True",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("HX-Redirect"), reverse("admin:inventario_categoria_changelist"))
        self.assertTrue(Categoria.objects.filter(nombre="Nueva demo").exists())

    def test_editar_modal_actualiza(self):
        from inventario.models import Categoria

        cat = Categoria.objects.get(nombre="Periféricos")
        url = reverse("admin:inventario_categoria_editar", args=[cat.pk])
        self.assertContains(self.client.get(url), "Editar categoría")
        resp = self.client.post(
            url,
            {
                "nombre": "Periféricos",
                "descripcion": "Descripción actualizada en modal",
                "_form_submitted": "True",
            },
        )
        self.assertEqual(resp.headers.get("HX-Redirect"), reverse("admin:inventario_categoria_changelist"))
        cat.refresh_from_db()
        self.assertEqual(cat.descripcion, "Descripción actualizada en modal")

    def test_lista_abre_modal_agregar(self):
        resp = self.client.get(reverse("admin:inventario_categoria_changelist"))
        self.assertContains(resp, 'hx-target="#modal-content"')
        self.assertContains(resp, reverse("admin:inventario_categoria_agregar"))
        self.assertContains(resp, 'title="Editar"')
        self.assertContains(resp, 'title="Eliminar"')

    def test_producto_lista_tiene_acciones_ficha(self):
        from inventario.models import Producto

        resp = self.client.get(reverse("admin:inventario_producto_changelist"))
        self.assertContains(resp, 'title="Editar"')
        self.assertContains(resp, 'title="Eliminar"')
        self.assertContains(resp, "lista-acciones")
        prod = Producto.objects.first()
        self.assertContains(
            resp, reverse("admin:inventario_producto_change", args=[prod.pk])
        )
        self.assertContains(
            resp, reverse("admin:inventario_producto_delete", args=[prod.pk])
        )

    def test_container_lista_tiene_acciones_ficha(self):
        from inventario.models import Container

        resp = self.client.get(reverse("admin:inventario_container_changelist"))
        self.assertContains(resp, "lista-acciones")
        self.assertContains(resp, 'title="Editar"')
        self.assertContains(resp, 'title="Eliminar"')
        cont = Container.objects.get(codigo="CONT-DEMO-001")
        self.assertContains(
            resp, reverse("admin:inventario_container_change", args=[cont.pk])
        )
        self.assertContains(
            resp, reverse("admin:inventario_container_delete", args=[cont.pk])
        )

    def test_eliminar_modal_borra(self):
        from inventario.models import Categoria

        cat = Categoria.objects.create(nombre="Temporal", descripcion="")
        url = reverse("admin:inventario_categoria_eliminar", args=[cat.pk])
        self.assertContains(self.client.get(url), "Eliminar categoría")
        resp = self.client.post(url, {"_form_submitted": "True"})
        self.assertEqual(resp.headers.get("HX-Redirect"), reverse("admin:inventario_categoria_changelist"))
        self.assertFalse(Categoria.objects.filter(pk=cat.pk).exists())

