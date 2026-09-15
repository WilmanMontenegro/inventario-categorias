from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventario", "0002_carrito_factura"),
    ]

    operations = [
        migrations.AddField(
            model_name="producto",
            name="imagen",
            field=models.CharField(
                blank=True,
                help_text="Ruta estática relativa, ej. inventario/productos/mouse.png",
                max_length=200,
                verbose_name="imagen",
            ),
        ),
    ]
