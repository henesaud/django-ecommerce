# Generated by Django 2.2.14 on 2022-04-26 16:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0013_auto_20220426_0444"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="cpf",
            field=models.CharField(default=46616168808, max_length=11),
            preserve_default=False,
        ),
    ]
