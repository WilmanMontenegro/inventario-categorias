from decimal import Decimal
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from inventario.models import (
    Categoria,
    Container,
    Empresa,
    Entrega,
    Inventario,
    Producto,
)

User = get_user_model()
FOTOS = Path(__file__).resolve().parents[2] / "static" / "inventario" / "productos"

CAT_DESC = {
    "Computadores": "Equipos de cómputo: portátiles y monitores.",
    "Periféricos": "Accesorios: mouse, teclado, audífonos, webcam, hubs.",
    "Componentes": "Partes internas: SSD, memoria RAM.",
}

# nombre, categoría, cantidad, costo, iva, precio, archivo, descripción
PRODUCTOS_DEMO = [
    ("Portátil 14\" i5 DEMO", "Computadores", 12, "1850000", "351500", "2599000", "portatil-14.png", "Portátil 14 pulgadas, Intel i5. DEMO."),
    ("Portátil 15\" Ryzen DEMO", "Computadores", 8, "2100000", "399000", "2899000", "portatil-15.png", "Portátil 15 pulgadas, AMD Ryzen. DEMO."),
    ("Monitor 24\" DEMO", "Computadores", 15, "420000", "79800", "599000", "monitor.png", "Monitor 24 pulgadas Full HD. DEMO."),
    ("Mouse inalámbrico DEMO", "Periféricos", 40, "28000", "5320", "45900", "mouse.png", "Mouse inalámbrico, receptor USB. DEMO."),
    ("Teclado mecánico DEMO", "Periféricos", 25, "95000", "18050", "149900", "teclado.png", "Teclado mecánico, switch rojo. DEMO."),
    ("Audífonos USB DEMO", "Periféricos", 20, "62000", "11780", "99900", "audifonos.png", "Audífonos USB con micrófono. DEMO."),
    ("Webcam Full HD DEMO", "Periféricos", 18, "88000", "16720", "129900", "webcam.png", "Cámara web 1080p. DEMO."),
    ("Hub USB-C DEMO", "Periféricos", 22, "45000", "8550", "79900", "hub.png", "Hub USB-C, 4 puertos. DEMO."),
    ("SSD 1TB DEMO", "Componentes", 30, "180000", "34200", "259000", "ssd.png", "Disco SSD 1 TB. DEMO."),
    ("Memoria RAM 16GB DEMO", "Componentes", 35, "145000", "27550", "209000", "ram.png", "Memoria RAM 16 GB DDR4. DEMO."),
]


def _poner_foto(producto, archivo):
    if producto.imagen:
        try:
            if Path(producto.imagen.path).is_file():
                return
        except ValueError:
            pass
    origen = FOTOS / archivo
    if not origen.is_file():
        return
    with origen.open("rb") as fh:
        producto.imagen.save(archivo, File(fh), save=True)


class Command(BaseCommand):
    help = "Carga datos sintéticos DEMO para la demo del corte 1."

    @transaction.atomic
    def handle(self, *args, **options):
        container, _ = Container.objects.get_or_create(codigo="CONT-DEMO-001")

        productos = []
        for nombre, cat_nombre, cantidad, costo, iva, precio, archivo, descripcion in PRODUCTOS_DEMO:
            categoria, _ = Categoria.objects.update_or_create(
                nombre=cat_nombre,
                defaults={"descripcion": CAT_DESC.get(cat_nombre, "")},
            )
            producto, _ = Producto.objects.update_or_create(
                nombre=nombre,
                defaults={"categoria": categoria, "descripcion": descripcion},
            )
            _poner_foto(producto, archivo)
            Inventario.objects.update_or_create(
                container=container,
                producto=producto,
                defaults={
                    "cantidad": cantidad,
                    "costo_base": Decimal(costo),
                    "iva": Decimal(iva),
                    "precio_venta": Decimal(precio),
                },
            )
            productos.append(producto)

        user, created = User.objects.get_or_create(
            username="unilago",
            defaults={
                "email": "demo@unilago-demo.local",
                "first_name": "Local",
                "last_name": "Unilago DEMO",
            },
        )
        user.set_password("demo1234")
        user.save()

        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@demo.local",
                "first_name": "Admin",
                "last_name": "DEMO",
            },
        )
        admin_user.set_password("demo1234")
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        empresa, _ = Empresa.objects.update_or_create(
            nit="900123456-1",
            defaults={
                "usuario": user,
                "camara_comercio": "CC-DEMO-45821",
                "nombre": "Tech Corner Unilago DEMO",
                "representante_legal": "Ana Pérez DEMO",
                "contacto": "3105551212",
                "correo": "demo@unilago-demo.local",
            },
        )

        Entrega.objects.get_or_create(
            empresa=empresa,
            producto=productos[0],
            container=container,
            defaults={"cantidad": 2},
        )

        self.stdout.write(self.style.SUCCESS("Seed DEMO listo (con imagenes)."))
        self.stdout.write("Admin: admin / demo1234 -> /admin/")
        self.stdout.write("Comprador: unilago / demo1234 -> catalogo")
        self.stdout.write(f"Container: {container.codigo}")
        self.stdout.write(f"Productos: {len(PRODUCTOS_DEMO)}")
