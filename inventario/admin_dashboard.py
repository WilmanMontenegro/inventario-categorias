"""Dashboard admin (Unfold) + stats."""

from django.db.models import Sum
from django.templatetags.static import static


def dashboard_stats():
    from .models import Container, Empresa, Factura, Inventario, Producto

    container = Container.objects.order_by("-creado").first()
    unidades = Inventario.objects.aggregate(t=Sum("cantidad"))["t"] or 0
    return {
        "containers": Container.objects.count(),
        "productos": Producto.objects.count(),
        "unidades": unidades,
        "empresas": Empresa.objects.count(),
        "facturas": Factura.objects.count(),
        "container_activo": container,
        "lineas_stock": Inventario.objects.filter(cantidad__gt=0).count(),
    }


def dashboard_callback(request, context):
    context.update({"dash": dashboard_stats()})
    return context


def unfold_stylesheet(request):
    return static("inventario/css/admin-unfold.css")
