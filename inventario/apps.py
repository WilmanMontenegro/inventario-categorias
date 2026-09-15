from django.apps import AppConfig


class InventarioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inventario"
    verbose_name = "Inventario"

    def ready(self):
        from unfold.sites import UnfoldAdminSite

        UnfoldAdminSite.site_header = "Eureka s&s"
        UnfoldAdminSite.site_title = "Eureka s&s"
        UnfoldAdminSite.index_title = "Inicio"
        UnfoldAdminSite.site_url = "/"
