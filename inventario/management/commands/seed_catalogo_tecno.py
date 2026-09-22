"""Carga catálogo Tecnotecnología desde hojas de cotización del cliente.

Precios: donde el EXW no venía en texto usable se usa estimado demo (COP).
Baterías: USD del PDF de fábrica × TRM. Aires solares: precios COP del brochure.
"""

from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from inventario.models import Categoria, Container, Inventario, Producto

FOTOS = Path(__file__).resolve().parents[2] / "static" / "inventario" / "productos" / "tecno"
TRM = Decimal("4100")  # COP por USD — estimado demo
CANTIDAD_DEMO = 10
CONTAINER_CODIGO = "CONT-TECNO-001"

CAT_DESC = {
    "Picadoras de carne": "Picadoras eléctricas de cocina.",
    "Arroceras": "Arroceras eléctricas varias capacidades.",
    "Hornos": "Hornos eléctricos y afines.",
    "Baterías portátiles": "Estaciones de energía / power stations.",
    "Cerraduras inteligentes": "Cerraduras con APP, huella y WiFi/Bluetooth.",
    "Aires acondicionados": "Aires split convencionales.",
    "Aires solares": "Aires híbridos solares ACDC.",
}


def _cop(valor) -> Decimal:
    return Decimal(str(valor)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _desde_costo(costo: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    """costo base, IVA 19%, precio de venta con margen demo ~35%."""
    costo = _cop(costo)
    iva = _cop(costo * Decimal("0.19"))
    precio = _cop(costo * Decimal("1.35"))
    return costo, iva, precio


def _desde_usd(usd) -> tuple[Decimal, Decimal, Decimal]:
    return _desde_costo(Decimal(str(usd)) * TRM)


def _desde_precio_venta(precio) -> tuple[Decimal, Decimal, Decimal]:
    """Cuando el doc ya trae precio de venta en COP."""
    precio = _cop(precio)
    costo = _cop(precio / Decimal("1.35"))
    iva = _cop(costo * Decimal("0.19"))
    return costo, iva, precio


def _foto(rel: str) -> Path | None:
    p = FOTOS / rel
    return p if p.is_file() else None


# nombre, categoría, descripción, costo/iva/precio, foto relativa tecno/
def _catalogo():
    items = []

    # --- Picadoras (modelos; EXW no en texto → estimado) ---
    picadoras = [
        ("BZ-01", "300W/400W, 2L/3L, SS + PP"),
        ("BZ-011", "300W/400W, 2L/3L, SS + PP"),
        ("BZ-02", "300W/400W, 2L/3L, SS + PP"),
        ("BZ-03", "300W/400W, 2L/3L, SS + PP"),
        ("BZ-04", "300W/400W, 2L/3L, SS + PP"),
        ("BZ-05A", "300W/400W, 2L/3L, SS + PP"),
        ("BZ-05", "300W/400W, 2L/3L, SS + PP"),
        ("BZ-06", "300W/400W, 2L/3L, SS + PP"),
        ("L806", "300W/400W, 2L/3L, SS + PP"),
        ("210H", "300W/400W, 2L/3L, SS + PP"),
    ]
    for modelo, esp in picadoras:
        c, i, p = _desde_costo(380000)
        items.append(
            (
                f"Picadora de carne {modelo}",
                "Picadoras de carne",
                f"{esp}. Precio demo (EXW no legible en cotización).",
                c,
                i,
                p,
                f"picadoras/{modelo}.jpeg"
                if _foto(f"picadoras/{modelo}.jpeg")
                else f"picadoras/{modelo}.png",
            )
        )

    # --- Baterías (USD PDF fábrica, orden ≈ modelos del Word) ---
    baterias_usd = [
        ("HRX-150Z", 32, "145Wh / 200W CA"),
        ("HRX-300", 91, "270Wh / 300W CA"),
        ("HRX-300Z", 143, "288Wh / 300W CA + carga inalámbrica"),
        ("HRX-300E", 208, "294Wh / 300W CA"),
        ("HRX-500Z", 247, "520Wh / 500W CA"),
        ("HRX-600B", 370, "577Wh / 600W CA"),
        ("HRX-600Z", 247, "520Wh / 600W CA"),
        ("HRX-1200Z", 494, "1008Wh / 1200W CA"),
        ("HRX-2400Z", 325, "2016Wh / 2400W CA"),
        ("HRX-3000Z", 546, "2688Wh / 3000W CA"),
        ("HRX-5000Z", 767, "5376Wh / 3000W CA"),
    ]
    for modelo, usd, esp in baterias_usd:
        c, i, p = _desde_usd(usd)
        ext = "jpeg" if _foto(f"baterias/{modelo}.jpeg") else "png"
        items.append(
            (
                f"Estación de energía {modelo}",
                "Baterías portátiles",
                f"{esp}. EXW ≈ USD {usd} (PDF fábrica × TRM {TRM}).",
                c,
                i,
                p,
                f"baterias/{modelo}.{ext}",
            )
        )

    # --- Aires convencionales ---
    aires = [
        ("9000BTU Económico", 850000, "GMCC/LINGDA, R32/R410A, solo frío o frío/calor"),
        ("9000BTU Gama alta", 1100000, "RECHI, EER 2,85"),
        ("12000BTU Económico", 1200000, "HIGHLY, 3500W refrigeración"),
        ("12000BTU Gama alta", 1450000, "HIGHLY/GMCC, EER 2,8"),
        ("18000BTU Económico", 1600000, "5000W refrigeración"),
        ("18000BTU Gama alta", 1900000, "EER 2,75"),
        ("24000BTU", 2400000, "7000W refrigeración"),
        ("36000BTU T3", 3200000, "10000W refrigeración, T3"),
    ]
    for nombre, costo, esp in aires:
        c, i, p = _desde_costo(costo)
        items.append(
            (
                f"Aire acondicionado {nombre}",
                "Aires acondicionados",
                f"{esp}. Precio demo (EXW no en texto).",
                c,
                i,
                p,
                "aires/aires-01.jpeg",
            )
        )

    # --- Aires solares (precios COP brochure) ---
    solares = [
        (
            "DGWA2-ACDC-12KR2",
            3384943,
            "Híbrido solar 12K BTU, 3500W frío, WiFi",
        ),
        (
            "DGWA1-ACDC-18KR2",
            4221222,
            "Híbrido solar 18K BTU, 5010W frío, WiFi",
        ),
        (
            "DGWA1-ACDC-24KR2",
            5100000,
            "Híbrido solar 24K BTU, 6400W frío (precio estimado demo)",
        ),
    ]
    for modelo, precio, esp in solares:
        c, i, p = _desde_precio_venta(precio)
        items.append(
            (
                f"Aire solar híbrido {modelo}",
                "Aires solares",
                esp,
                c,
                i,
                p,
                "aires/aires-01.jpeg",
            )
        )

    # --- Cerraduras ---
    cerraduras = [
        ("RK-1", "Aleación aluminio, Tuya, ojo de gato / facial"),
        ("RK-2A", "Hierro + plástico, Tuya"),
        ("RK-3A", "Aluminio + hierro + plástico"),
        ("RK4", "Aleación aluminio, ojo de gato"),
        ("RK5", "Hierro + plástico"),
        ("RK-6", "Aleación aluminio, electroplaca"),
        ("RK7", "Aluminio + plástico, facial"),
        ("RK8", "Aluminio + plástico, facial"),
        ("RZ1", "Hierro + acrílico, Tuya BT/WiFi"),
        ("RZ2", "Hierro + vidrio, Tuya WiFi"),
        ("RZ3", "Acero + vidrio, Tuya WiFi"),
        ("RZ4", "Acero + acrílico, Tuya BT/WiFi"),
        ("RZ5", "Metal + plástico, Tuya WiFi"),
        ("RZ6", "Aluminio + plástico, Tuya WiFi"),
        ("RA4", "Aluminio táctil — EXW USD 23,60"),
        ("RA5", "Aluminio táctil con cámara"),
        ("RA6", "Aluminio + plástico, voz ES"),
        ("RA7", "Aluminio + plástico, voz ES"),
        ("RA8", "Aluminio + plástico"),
        ("RA9", "Aluminio + plástico, voz ES"),
        ("RA10", "Aluminio + plástico"),
        ("RA11", "Metal + plástico, Tuya BT"),
        ("RA12", "Aluminio + plástico, Tuya BT"),
        ("RB-1", "Aluminio + plástico, Tuya WiFi"),
        ("HTL-01", "Aluminio táctil, tarjeta IC"),
        ("GL-01", "Plástico ABS, puerta vidrio/madera"),
    ]
    for modelo, esp in cerraduras:
        if modelo == "RA4":
            c, i, p = _desde_usd("23.60")
        else:
            c, i, p = _desde_costo(165000)
        ext = "jpeg" if _foto(f"cerraduras/{modelo}.jpeg") else "png"
        items.append(
            (
                f"Cerradura inteligente {modelo}",
                "Cerraduras inteligentes",
                f"{esp}. MOQ OEM típico 200–300 pcs.",
                c,
                i,
                p,
                f"cerraduras/{modelo}.{ext}",
            )
        )

    # --- Hornos (una ficha por imagen / línea de cotización) ---
    hornos = [
        ("Horno 12L 600W", "hornos-01.png", 140000),
        ("Horno 15L 650W", "hornos-02.jpeg", 155000),
        ("Horno 15L 750W", "hornos-03.png", 165000),
        ("Horno 15L 650W (línea 4)", "hornos-04.jpeg", 155000),
        ("Horno 20L 1000W", "hornos-05.jpeg", 210000),
        ("Horno 20L 1000W (línea 6)", "hornos-06.jpeg", 210000),
        ("Horno 20L 1360W", "hornos-07.jpeg", 240000),
        ("Horno 28L 1600W", "hornos-08.jpeg", 280000),
        ("Horno 32L 1500W", "hornos-09.jpeg", 300000),
        ("Horno 32L 1500W (línea 10)", "hornos-10.jpeg", 300000),
        ("Horno 32L 1500W (línea 11)", "hornos-11.jpeg", 300000),
        ("Horno 38L 2000W", "hornos-12.jpeg", 360000),
        ("Horno 42L 2000W", "hornos-13.jpeg", 390000),
        ("Horno 38L 2000W (línea 14)", "hornos-14.jpeg", 360000),
        ("Horno 55L 2000W", "hornos-15.jpeg", 450000),
        ("Horno 48L con placas 1700W", "hornos-16.jpeg", 520000),
        ("Marcador desayuno 3 en 1", "hornos-17.jpeg", 280000),
        ("Horno 15L 2000W inox 304", "hornos-18.jpeg", 320000),
        ("Horno de freír 23L 1600W", "hornos-19.jpeg", 340000),
    ]
    for nombre, foto, costo in hornos:
        c, i, p = _desde_costo(costo)
        items.append(
            (
                nombre,
                "Hornos",
                "Ficha de cotización fábrica. Precio demo (EXW no en texto).",
                c,
                i,
                p,
                f"hornos/{foto}",
            )
        )

    # --- Arroceras (por línea / imagen) ---
    arroceras = [
        ("Arrocera mecánica PP 3–6L", "arroceras-01.jpeg", 95000),
        ("Arrocera mecánica PP 2–6L", "arroceras-02.jpeg", 90000),
        ("Arrocera mecánica PP 3–6L (línea 3)", "arroceras-03.png", 95000),
        ("Arrocera mecánica PP 3–5L", "arroceras-04.png", 88000),
        ("Arrocera inox 2–6L", "arroceras-05.jpeg", 120000),
        ("Arrocera mecánica PP 3–6L (línea 6)", "arroceras-06.jpeg", 95000),
        ("Arrocera inox 3–6L", "arroceras-07.png", 125000),
        ("Arrocera PP revest. hierro 2–6L", "arroceras-08.jpeg", 100000),
        ("Arrocera PP revest. hierro 2/4/6L", "arroceras-09.jpeg", 98000),
        ("Arrocera PP revest. hierro 2–6L (línea 10)", "arroceras-10.jpeg", 100000),
        ("Arrocera PP 2L/4L", "arroceras-11.jpeg", 85000),
        ("Arrocera 1,2L 200W", "arroceras-12.png", 70000),
        ("Arrocera 2L 400W", "arroceras-13.png", 80000),
        ("Arrocera 2L botón", "arroceras-14.jpeg", 85000),
        ("Arrocera 3L táctil cerámica", "arroceras-15.jpeg", 150000),
        ("Arrocera 4L botón", "arroceras-16.jpeg", 110000),
        ("Arrocera 3L/5L botón-táctil", "arroceras-17.png", 130000),
        ("Arrocera 2L/3L botón-táctil", "arroceras-18.jpeg", 115000),
        ("Arrocera 2L/3L mecánica aluminio", "arroceras-19.jpeg", 105000),
    ]
    for nombre, foto, costo in arroceras:
        c, i, p = _desde_costo(costo)
        items.append(
            (
                nombre,
                "Arroceras",
                "Ficha de cotización fábrica. Precio demo (EXW no en texto).",
                c,
                i,
                p,
                f"arroceras/{foto}",
            )
        )

    return items


def _poner_foto(producto, rel):
    origen = _foto(rel)
    if origen is None:
        return
    if producto.imagen:
        try:
            if Path(producto.imagen.path).is_file():
                return
        except ValueError:
            pass
    with origen.open("rb") as fh:
        producto.imagen.save(origen.name, File(fh), save=True)


class Command(BaseCommand):
    help = "Carga productos Tecnotecnología (cotizaciones del cliente) al container CONT-TECNO-001."

    @transaction.atomic
    def handle(self, *args, **options):
        container, _ = Container.objects.get_or_create(codigo=CONTAINER_CODIGO)
        n = 0
        for nombre, cat_nombre, descripcion, costo, iva, precio, foto in _catalogo():
            categoria, _ = Categoria.objects.update_or_create(
                nombre=cat_nombre,
                defaults={"descripcion": CAT_DESC.get(cat_nombre, "")},
            )
            producto, _ = Producto.objects.update_or_create(
                nombre=nombre,
                defaults={"categoria": categoria, "descripcion": descripcion},
            )
            _poner_foto(producto, foto)
            Inventario.objects.update_or_create(
                container=container,
                producto=producto,
                defaults={
                    "cantidad": CANTIDAD_DEMO,
                    "costo_base": costo,
                    "iva": iva,
                    "precio_venta": precio,
                },
            )
            n += 1

        self.stdout.write(self.style.SUCCESS(f"Catálogo Tecno listo: {n} productos."))
        self.stdout.write(f"Container: {container.codigo}")
        self.stdout.write(
            "Nota: muchos precios son demo — el EXW venía en tablas/imagenes no legibles."
        )
