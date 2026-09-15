from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, User
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.widgets import UnfoldAdminTextareaWidget, UnfoldAdminTextInputWidget

from .admin_modal import FichaAdmin, ModalListaAdmin, ModelDialogForm
from .models import (
    Carrito,
    Categoria,
    Container,
    Empresa,
    Entrega,
    Factura,
    Inventario,
    LineaCarrito,
    LineaFactura,
    Producto,
)

# Importar auth.admin ya registra User/Group → Unfold solo User (sin Grupos en la demo).
admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


class CategoriaDialogForm(ModelDialogForm):
    model = Categoria
    nombre = forms.CharField(
        label="Nombre",
        max_length=120,
        widget=UnfoldAdminTextInputWidget(),
    )
    descripcion = forms.CharField(
        label="Descripción",
        required=False,
        widget=UnfoldAdminTextareaWidget(attrs={"rows": 3}),
    )

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"].strip()
        qs = Categoria.objects.filter(nombre=nombre)
        if self.object_id:
            qs = qs.exclude(pk=self.object_id)
        if qs.exists():
            raise forms.ValidationError("Ya existe una categoría con ese nombre.")
        return nombre


class InventarioInline(TabularInline):
    model = Inventario
    extra = 1
    tab = True


class LineaCarritoInline(TabularInline):
    model = LineaCarrito
    extra = 0
    tab = True


class LineaFacturaInline(TabularInline):
    model = LineaFactura
    extra = 0
    tab = True
    readonly_fields = ("producto", "cantidad", "precio_unitario", "subtotal")


@admin.register(Categoria)
class CategoriaAdmin(ModalListaAdmin):
    modal_form_class = CategoriaDialogForm
    modal_campos = ("nombre", "descripcion")
    modal_eliminar_aviso = (
        "¿Seguro que quieres eliminar esta categoría? "
        "Si tiene productos, no se podrá borrar."
    )
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre", "descripcion")
    fields = ("nombre", "descripcion")


class ProductoAdminForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ("imagen", "nombre", "categoria", "descripcion")
        widgets = {
            "nombre": UnfoldAdminTextInputWidget(),
            "descripcion": UnfoldAdminTextareaWidget(attrs={"rows": 3}),
        }


@admin.register(Producto)
class ProductoAdmin(FichaAdmin):
    # ponytail: una ficha = ver+editar; no pantalla solo-lectura
    form = ProductoAdminForm
    list_display = ("miniatura", "nombre", "categoria")
    list_filter = ("categoria",)
    search_fields = ("nombre", "descripcion")
    list_filter_sheet = False
    fieldsets = (
        (None, {"fields": ("imagen", "nombre", "categoria", "descripcion")}),
    )

    @admin.display(description="imagen")
    def miniatura(self, obj):
        if not obj.imagen:
            return "—"
        return format_html(
            '<img src="{}" alt="" width="38" height="38" '
            'style="object-fit:cover;border-radius:6px;display:block">',
            obj.imagen.url,
        )


@admin.register(Container)
class ContainerAdmin(FichaAdmin):
    list_display = ("codigo", "creado")
    search_fields = ("codigo",)
    inlines = [InventarioInline]


@admin.register(Inventario)
class InventarioAdmin(FichaAdmin):
    list_display = (
        "container",
        "producto",
        "cantidad",
        "costo_base",
        "iva",
        "precio_venta",
    )
    list_filter = ("container", "producto__categoria")
    search_fields = ("producto__nombre", "container__codigo")
    list_filter_sheet = False


@admin.register(Empresa)
class EmpresaAdmin(FichaAdmin):
    list_display = ("nombre", "nit", "usuario", "representante_legal", "correo")
    search_fields = ("nombre", "nit", "correo")
    raw_id_fields = ("usuario",)


@admin.register(Entrega)
class EntregaAdmin(FichaAdmin):
    list_display = ("empresa", "producto", "container", "cantidad", "creado")
    list_filter = ("empresa", "container")
    search_fields = ("empresa__nombre", "producto__nombre")
    list_filter_sheet = False


@admin.register(Carrito)
class CarritoAdmin(FichaAdmin):
    list_display = ("empresa", "container", "abierto", "creado")
    list_filter = ("abierto",)
    search_fields = ("empresa__nombre", "container__codigo")
    inlines = [LineaCarritoInline]
    list_filter_sheet = False


@admin.register(Factura)
class FacturaAdmin(FichaAdmin):
    list_display = ("numero", "empresa", "container", "total", "creado")
    search_fields = ("numero", "empresa__nombre")
    inlines = [LineaFacturaInline]
    readonly_fields = ("numero", "empresa", "container", "carrito", "total", "creado")
