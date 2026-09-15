from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventario", "0005_producto_descripcion"),
    ]

    operations = [
        migrations.AddField(
            model_name="categoria",
            name="descripcion",
            field=models.TextField(blank=True, verbose_name="descripción"),
        ),
    ]
