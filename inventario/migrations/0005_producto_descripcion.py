from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventario", "0004_producto_imagen_archivo"),
    ]

    operations = [
        migrations.AddField(
            model_name="producto",
            name="descripcion",
            field=models.TextField(blank=True, verbose_name="descripción"),
        ),
    ]
