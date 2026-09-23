from django.urls import path

from . import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("entrar/", views.entrar, name="entrar"),
    path("entrar/admin/", views.entrar_demo_admin, name="entrar_demo_admin"),
    path(
        "entrar/comprador/",
        views.entrar_demo_comprador,
        name="entrar_demo_comprador",
    ),
    path("salir/", views.salir, name="salir"),
    path("catalogo/", views.catalogo, name="catalogo"),
    path(
        "catalogo/<int:inventario_id>/",
        views.producto_detalle,
        name="producto_detalle",
    ),
    path(
        "carrito/agregar/<int:inventario_id>/",
        views.agregar_carrito,
        name="agregar_carrito",
    ),
    path("carrito/", views.carrito, name="carrito"),
    path("carrito/quitar/<int:linea_id>/", views.quitar_linea, name="quitar_linea"),
    path("carrito/confirmar/", views.confirmar, name="confirmar"),
    path("factura/<str:numero>/", views.factura, name="factura"),
]
