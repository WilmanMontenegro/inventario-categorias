from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction


class Categoria(models.Model):
    nombre = models.CharField("nombre", max_length=120, unique=True)
    descripcion = models.TextField("descripción", blank=True)

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField("nombre", max_length=200)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        verbose_name="categoría",
    )
    imagen = models.ImageField("imagen", upload_to="productos/", blank=True)
    descripcion = models.TextField("descripción", blank=True)

    class Meta:
        verbose_name = "producto"
        verbose_name_plural = "productos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @property
    def inicial(self):
        return (self.nombre[:1] or "?").upper()


class Container(models.Model):
    codigo = models.CharField("código", max_length=64, unique=True)
    creado = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "container"
        verbose_name_plural = "containers"
        ordering = ["-creado"]

    def __str__(self):
        return self.codigo


class Inventario(models.Model):
    container = models.ForeignKey(
        Container,
        on_delete=models.CASCADE,
        related_name="inventario",
        verbose_name="container",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="inventario",
        verbose_name="producto",
    )
    cantidad = models.PositiveIntegerField("cantidad")
    costo_base = models.DecimalField("costo base", max_digits=14, decimal_places=2)
    iva = models.DecimalField("IVA", max_digits=14, decimal_places=2)
    precio_venta = models.DecimalField("precio de venta", max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = "inventario"
        verbose_name_plural = "inventarios"
        unique_together = [("container", "producto")]
        ordering = ["producto__nombre"]

    def __str__(self):
        return f"{self.container} — {self.producto}"


class Empresa(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="empresa",
        verbose_name="usuario",
    )
    nit = models.CharField("NIT", max_length=32, unique=True)
    camara_comercio = models.CharField("registro de cámara de comercio", max_length=120)
    nombre = models.CharField("nombre de la empresa", max_length=200)
    representante_legal = models.CharField("representante legal", max_length=200)
    contacto = models.CharField("contacto", max_length=120)
    correo = models.EmailField("correo")

    class Meta:
        verbose_name = "empresa"
        verbose_name_plural = "empresas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Entrega(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="entregas",
        verbose_name="empresa",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="entregas",
        verbose_name="producto",
    )
    container = models.ForeignKey(
        Container,
        on_delete=models.PROTECT,
        related_name="entregas",
        verbose_name="container",
    )
    cantidad = models.PositiveIntegerField("cantidad")
    creado = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "entrega"
        verbose_name_plural = "entregas"
        ordering = ["-creado"]

    def __str__(self):
        return f"{self.empresa} ← {self.producto} ({self.cantidad})"


class Carrito(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="carritos",
        verbose_name="empresa",
    )
    container = models.ForeignKey(
        Container,
        on_delete=models.PROTECT,
        related_name="carritos",
        verbose_name="container",
    )
    abierto = models.BooleanField("abierto", default=True)
    creado = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "carrito"
        verbose_name_plural = "carritos"
        ordering = ["-creado"]

    def __str__(self):
        estado = "abierto" if self.abierto else "cerrado"
        return f"Carrito {self.empresa} ({estado})"

    @property
    def total(self):
        return sum((linea.subtotal for linea in self.lineas.all()), Decimal("0"))

    @property
    def cantidad_items(self):
        return sum(linea.cantidad for linea in self.lineas.all())


class LineaCarrito(models.Model):
    carrito = models.ForeignKey(
        Carrito,
        on_delete=models.CASCADE,
        related_name="lineas",
        verbose_name="carrito",
    )
    inventario = models.ForeignKey(
        Inventario,
        on_delete=models.PROTECT,
        related_name="lineas_carrito",
        verbose_name="inventario",
    )
    cantidad = models.PositiveIntegerField("cantidad", default=1)
    precio_unitario = models.DecimalField(
        "precio unitario", max_digits=14, decimal_places=2
    )

    class Meta:
        verbose_name = "línea de carrito"
        verbose_name_plural = "líneas de carrito"
        unique_together = [("carrito", "inventario")]

    def __str__(self):
        return f"{self.inventario.producto} × {self.cantidad}"

    @property
    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def clean(self):
        if self.cantidad > self.inventario.cantidad:
            raise ValidationError(
                {"cantidad": "No hay suficiente inventario en el container."}
            )


class Factura(models.Model):
    numero = models.CharField("número", max_length=32, unique=True)
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="facturas",
        verbose_name="empresa",
    )
    container = models.ForeignKey(
        Container,
        on_delete=models.PROTECT,
        related_name="facturas",
        verbose_name="container",
    )
    carrito = models.OneToOneField(
        Carrito,
        on_delete=models.PROTECT,
        related_name="factura",
        verbose_name="carrito",
    )
    total = models.DecimalField("total", max_digits=14, decimal_places=2)
    creado = models.DateTimeField("creado", auto_now_add=True)

    class Meta:
        verbose_name = "factura"
        verbose_name_plural = "facturas"
        ordering = ["-creado"]

    def __str__(self):
        return self.numero


class LineaFactura(models.Model):
    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name="lineas",
        verbose_name="factura",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="lineas_factura",
        verbose_name="producto",
    )
    cantidad = models.PositiveIntegerField("cantidad")
    precio_unitario = models.DecimalField(
        "precio unitario", max_digits=14, decimal_places=2
    )
    subtotal = models.DecimalField("subtotal", max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = "línea de factura"
        verbose_name_plural = "líneas de factura"

    def __str__(self):
        return f"{self.producto} × {self.cantidad}"


@transaction.atomic
def confirmar_compra(carrito: Carrito) -> Factura:
    if not carrito.abierto:
        raise ValidationError("Este carrito ya está cerrado.")
    lineas = list(carrito.lineas.select_related("inventario", "inventario__producto"))
    if not lineas:
        raise ValidationError("El carrito está vacío.")

    for linea in lineas:
        inv = Inventario.objects.select_for_update().get(pk=linea.inventario_id)
        if linea.cantidad > inv.cantidad:
            raise ValidationError(
                f"No hay stock de {inv.producto.nombre}: "
                f"pide {linea.cantidad}, hay {inv.cantidad}."
            )
        inv.cantidad -= linea.cantidad
        inv.save(update_fields=["cantidad"])

    total = sum((linea.subtotal for linea in lineas), Decimal("0"))
    secuencia = Factura.objects.count() + 1
    factura = Factura.objects.create(
        numero=f"FAC-DEMO-{secuencia:04d}",
        empresa=carrito.empresa,
        container=carrito.container,
        carrito=carrito,
        total=total,
    )
    LineaFactura.objects.bulk_create(
        [
            LineaFactura(
                factura=factura,
                producto=linea.inventario.producto,
                cantidad=linea.cantidad,
                precio_unitario=linea.precio_unitario,
                subtotal=linea.subtotal,
            )
            for linea in lineas
        ]
    )
    carrito.abierto = False
    carrito.save(update_fields=["abierto"])
    return factura
