from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventario", "0003_producto_imagen"),
    ]

    operations = [
        migrations.AlterField(
            model_name="producto",
            name="imagen",
            field=models.ImageField(
                blank=True, upload_to="productos/", verbose_name="imagen"
            ),
        ),
    ]
