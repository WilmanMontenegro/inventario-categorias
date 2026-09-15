from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST


from .models import (
    Carrito,
    Categoria,
    Container,
    Empresa,
    Factura,
    Inventario,
    LineaCarrito,
    confirmar_compra,
)


def _empresa_de(user):
    return getattr(user, "empresa", None)


def _container_activo():
    return Container.objects.order_by("-creado").first()


def _carrito_abierto(empresa, container):
    carrito, _ = Carrito.objects.get_or_create(
        empresa=empresa,
        container=container,
        abierto=True,
        defaults={},
    )
    return carrito


def _badge_context(request):
    empresa = _empresa_de(request.user) if request.user.is_authenticated else None
    container = _container_activo()
    cantidad = 0
    if empresa and container:
        carrito = Carrito.objects.filter(
            empresa=empresa, container=container, abierto=True
        ).first()
        if carrito:
            cantidad = carrito.cantidad_items
    return {"carrito_cantidad": cantidad, "container_activo": container}


@require_GET
def inicio(request):
    if request.user.is_authenticated and _empresa_de(request.user):
        return redirect("catalogo")
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("admin:index")
    return redirect("entrar")


@require_http_methods(["GET", "POST"])
def entrar(request):
    error = None
    if request.method == "POST":
        username = request.POST.get("usuario", "").strip()
        password = request.POST.get("clave", "")
        user = authenticate(request, username=username, password=password)
        if user is None:
            error = "Usuario o clave incorrectos."
        elif not hasattr(user, "empresa") or user.empresa is None:
            if user.is_staff:
                login(request, user)
                return redirect("admin:index")
            error = "Este usuario no está vinculado a una empresa."
        else:
            login(request, user)
            return redirect("catalogo")
    return render(request, "inventario/entrar.html", {"error": error})


def _login_demo(request, username, password):
    user = authenticate(request, username=username, password=password)
    if user is None:
        return None
    login(request, user)
    return user


@require_POST
def entrar_demo_admin(request):
    user = _login_demo(request, "admin", "demo1234")
    if user is None or not user.is_staff:
        return render(
            request,
            "inventario/entrar.html",
            {
                "error": (
                    "No hay usuario admin DEMO. Corré "
                    ".\\.venv\\Scripts\\python.exe manage.py seed_demo"
                )
            },
        )
    return redirect("admin:index")


@require_POST
def entrar_demo_comprador(request):
    user = _login_demo(request, "unilago", "demo1234")
    if user is None or _empresa_de(user) is None:
        return render(
            request,
            "inventario/entrar.html",
            {
                "error": (
                    "No hay comprador DEMO. Corré "
                    ".\\.venv\\Scripts\\python.exe manage.py seed_demo"
                )
            },
        )
    return redirect("catalogo")


@require_http_methods(["GET", "POST"])
def salir(request):
    logout(request)
    return redirect("entrar")


@login_required
@require_GET
def catalogo(request):
    empresa = _empresa_de(request.user)
    if empresa is None:
        if request.user.is_staff:
            return redirect("admin:index")
        return redirect("entrar")

    container = _container_activo()
    items = []
    categorias = []
    categoria_activa = None
    if container:
        stock = Inventario.objects.filter(container=container, cantidad__gt=0)
        categorias = list(
            Categoria.objects.filter(
                pk__in=stock.values_list("producto__categoria_id", flat=True)
            ).order_by("nombre")
        )
        cat_id = request.GET.get("categoria")
        if cat_id:
            categoria_activa = Categoria.objects.filter(pk=cat_id).first()
            if categoria_activa:
                stock = stock.filter(producto__categoria=categoria_activa)
            else:
                categoria_activa = None
        items = list(
            stock.select_related("producto", "producto__categoria").order_by(
                "producto__nombre"
            )
        )
    ctx = {
        "empresa": empresa,
        "items": items,
        "categorias": categorias,
        "categoria_activa": categoria_activa,
        **_badge_context(request),
    }
    return render(request, "inventario/catalogo.html", ctx)


@login_required
@require_POST
def agregar_carrito(request, inventario_id):
    empresa = _empresa_de(request.user)
    if empresa is None:
        return HttpResponse("Sin empresa.", status=403)

    inventario = get_object_or_404(
        Inventario.objects.select_related("producto", "container"),
        pk=inventario_id,
    )
    try:
        cantidad = int(request.POST.get("cantidad", "1"))
    except ValueError:
        cantidad = 1
    if cantidad < 1:
        cantidad = 1

    carrito = _carrito_abierto(empresa, inventario.container)
    linea, created = LineaCarrito.objects.get_or_create(
        carrito=carrito,
        inventario=inventario,
        defaults={
            "cantidad": 0,
            "precio_unitario": inventario.precio_venta,
        },
    )
    nueva = linea.cantidad + cantidad
    if nueva > inventario.cantidad:
        return render(
            request,
            "inventario/partials/aviso.html",
            {
                "tipo": "error",
                "mensaje": (
                    f"No hay suficiente inventario de {inventario.producto.nombre}. "
                    f"Disponible: {inventario.cantidad}."
                ),
            },
            status=200,
        )
    linea.cantidad = nueva
    linea.precio_unitario = inventario.precio_venta
    linea.save()

    if request.headers.get("HX-Request"):
        return render(
            request,
            "inventario/partials/agregado.html",
            {
                "producto": inventario.producto.nombre,
                "carrito_cantidad": carrito.cantidad_items,
            },
        )
    return redirect("carrito")


@login_required
@require_GET
def carrito(request):
    empresa = _empresa_de(request.user)
    if empresa is None:
        return redirect("entrar")
    container = _container_activo()
    carrito_obj = None
    if container:
        carrito_obj = Carrito.objects.filter(
            empresa=empresa, container=container, abierto=True
        ).prefetch_related("lineas__inventario__producto").first()
    ctx = {
        "empresa": empresa,
        "carrito": carrito_obj,
        **_badge_context(request),
    }
    return render(request, "inventario/carrito.html", ctx)


@login_required
@require_POST
def quitar_linea(request, linea_id):
    empresa = _empresa_de(request.user)
    linea = get_object_or_404(
        LineaCarrito.objects.select_related("carrito"),
        pk=linea_id,
        carrito__empresa=empresa,
        carrito__abierto=True,
    )
    linea.delete()
    return redirect("carrito")


@login_required
@require_POST
def confirmar(request):
    empresa = _empresa_de(request.user)
    if empresa is None:
        return redirect("entrar")
    container = _container_activo()
    carrito_obj = get_object_or_404(
        Carrito, empresa=empresa, container=container, abierto=True
    )
    try:
        factura = confirmar_compra(carrito_obj)
    except ValidationError as exc:
        mensaje = "; ".join(exc.messages) if hasattr(exc, "messages") else str(exc)
        return render(
            request,
            "inventario/carrito.html",
            {
                "empresa": empresa,
                "carrito": carrito_obj,
                "error": mensaje,
                **_badge_context(request),
            },
        )
    return redirect("factura", numero=factura.numero)


@login_required
@require_GET
def factura(request, numero):
    empresa = _empresa_de(request.user)
    factura_obj = get_object_or_404(
        Factura.objects.prefetch_related("lineas__producto"),
        numero=numero,
        empresa=empresa,
    )
    return render(
        request,
        "inventario/factura.html",
        {
            "empresa": empresa,
            "factura": factura_obj,
            **_badge_context(request),
        },
    )