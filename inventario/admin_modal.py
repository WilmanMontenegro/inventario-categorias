"""Lista admin con modal Unfold: agregar / editar / eliminar sin salir.

Uso:
    class FooAdmin(ModalListaAdmin):
        modal_form_class = FooDialogForm
        modal_campos = ("nombre", "descripcion")
        list_display = ("nombre", "descripcion")  # se agrega «acciones»
"""

from django.contrib import admin, messages
from django.db.models.deletion import ProtectedError
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import action
from unfold.forms import BaseDialogForm


def html_acciones(opts, object_id):
    """Editar / Eliminar en modal (HTMX)."""
    edit_url = reverse(
        f"admin:{opts.app_label}_{opts.model_name}_editar",
        args=[object_id],
    )
    del_url = reverse(
        f"admin:{opts.app_label}_{opts.model_name}_eliminar",
        args=[object_id],
    )
    return format_html(
        '<div class="lista-acciones">'
        '<a href="{}" class="lista-acciones__btn" title="Editar" aria-label="Editar"'
        ' hx-get="{}" hx-target="#modal-content" hx-select="#dialog"'
        ' x-on:htmx:after-on-load="openModal = true">'
        '<span class="material-symbols-outlined" aria-hidden="true">edit</span></a>'
        '<a href="{}" class="lista-acciones__btn lista-acciones__btn--peligro"'
        ' title="Eliminar" aria-label="Eliminar"'
        ' hx-get="{}" hx-target="#modal-content" hx-select="#dialog"'
        ' x-on:htmx:after-on-load="openModal = true">'
        '<span class="material-symbols-outlined" aria-hidden="true">delete</span></a>'
        "</div>",
        edit_url,
        edit_url,
        del_url,
        del_url,
    )


def html_acciones_ficha(opts, object_id):
    """Editar / Eliminar en ficha (pantalla propia, sin modal)."""
    edit_url = reverse(
        f"admin:{opts.app_label}_{opts.model_name}_change",
        args=[object_id],
    )
    del_url = reverse(
        f"admin:{opts.app_label}_{opts.model_name}_delete",
        args=[object_id],
    )
    return format_html(
        '<div class="lista-acciones">'
        '<a href="{}" class="lista-acciones__btn" title="Editar" aria-label="Editar">'
        '<span class="material-symbols-outlined" aria-hidden="true">edit</span></a>'
        '<a href="{}" class="lista-acciones__btn lista-acciones__btn--peligro"'
        ' title="Eliminar" aria-label="Eliminar">'
        '<span class="material-symbols-outlined" aria-hidden="true">delete</span></a>'
        "</div>",
        edit_url,
        del_url,
    )


class FichaAdmin(ModelAdmin):
    # ponytail: un Guardar; otro registro = flecha atrás + Agregar
    modal_agregar = False
    # Columna acción (Editar/Eliminar) → change/delete; sin click en la fila
    lista_acciones = True

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_save_and_add_another"] = False
        extra_context["show_save_and_continue"] = False
        return super().changeform_view(request, object_id, form_url, extra_context)

    def get_list_display(self, request):
        display = list(super().get_list_display(request))
        if self.lista_acciones and "acciones" not in display:
            display.append("acciones")
        return display

    def get_list_display_links(self, request, list_display):
        if self.lista_acciones:
            return ()
        return super().get_list_display_links(request, list_display)

    @admin.display(description="acción")
    def acciones(self, obj):
        return html_acciones_ficha(self.opts, obj.pk)


class ModelDialogForm(BaseDialogForm):
    """Form de modal: widgets Unfold en la subclase; initial desde el objeto."""

    model = None

    def __init__(
        self,
        request: HttpRequest,
        object_id: int | str | None = None,
        *args,
        **kwargs,
    ):
        super().__init__(request, object_id, *args, **kwargs)
        if object_id and not self.is_bound and self.model:
            obj = self.model.objects.filter(pk=object_id).first()
            if not obj:
                return
            for name, field in self.fields.items():
                if name == "_form_submitted":
                    continue
                if hasattr(obj, name):
                    field.initial = getattr(obj, name)


class ModalListaAdmin(FichaAdmin):
    """Factor común: lista + modal. Parametrizar modal_form_class y modal_campos."""

    modal_agregar = True
    modal_form_class = None
    modal_campos = ()
    modal_eliminar_aviso = ""
    actions_list = ["agregar"]
    actions_row = ["editar", "eliminar"]
    list_display_links = ()

    def get_urls(self):
        self._sync_modal_dialogs()
        return super().get_urls()

    def _sync_modal_dialogs(self):
        if not self.modal_form_class:
            return
        nombre = self.opts.verbose_name
        aviso = self.modal_eliminar_aviso or (
            f"¿Seguro que quieres eliminar esta {nombre}? "
            "Si está en uso, no se podrá borrar."
        )
        type(self).agregar.dialog.update(
            {
                "title": f"Agregar {nombre}",
                "form_class": self.modal_form_class,
                "form_submit_text": "Guardar",
            }
        )
        type(self).editar.dialog.update(
            {
                "title": f"Editar {nombre}",
                "form_class": self.modal_form_class,
                "form_submit_text": "Guardar",
            }
        )
        type(self).eliminar.dialog.update(
            {
                "title": f"Eliminar {nombre}",
                "description": aviso,
                "form_submit_text": "Eliminar",
            }
        )

    def get_list_display(self, request):
        display = list(super().get_list_display(request))
        if "acciones" not in display:
            display.append("acciones")
        return display

    def get_actions_list(self, request):
        return []

    def get_actions_row(self, request):
        return []

    def _modal_redirect(self):
        return HttpResponse(
            headers={
                "HX-Redirect": reverse(
                    f"admin:{self.opts.app_label}_{self.opts.model_name}_changelist"
                ),
            }
        )

    def _datos_modal(self, form):
        return {campo: form.cleaned_data[campo] for campo in self.modal_campos}

    @admin.display(description="acción")
    def acciones(self, obj):
        return html_acciones(self.opts, obj.pk)

    @action(
        description="Agregar",
        url_path="agregar",
        icon="add",
        permissions=["add"],
        dialog={
            "title": "Agregar",
            "form_class": BaseDialogForm,
            "form_submit_text": "Guardar",
        },
    )
    def agregar(self, request, form):
        self.model.objects.create(**self._datos_modal(form))
        messages.success(request, f"{self.opts.verbose_name.capitalize()} agregada.")
        return self._modal_redirect()

    @action(
        description="Editar",
        url_path="editar",
        icon="edit",
        permissions=["change"],
        dialog={
            "title": "Editar",
            "form_class": BaseDialogForm,
            "form_submit_text": "Guardar",
        },
    )
    def editar(self, request, form, object_id):
        obj = self.model.objects.get(pk=object_id)
        for campo, valor in self._datos_modal(form).items():
            setattr(obj, campo, valor)
        obj.save(update_fields=list(self.modal_campos))
        messages.success(request, f"{self.opts.verbose_name.capitalize()} guardada.")
        return self._modal_redirect()

    @action(
        description="Eliminar",
        url_path="eliminar",
        icon="delete",
        permissions=["delete"],
        dialog={
            "title": "Eliminar",
            "description": "",
            "form_submit_text": "Eliminar",
        },
    )
    def eliminar(self, request, form, object_id):
        obj = self.model.objects.get(pk=object_id)
        etiqueta = str(obj)
        try:
            obj.delete()
        except ProtectedError:
            messages.error(
                request,
                f"No se puede eliminar «{etiqueta}»: está en uso.",
            )
        else:
            messages.success(request, f"«{etiqueta}» eliminada.")
        return self._modal_redirect()
