# Generated by Django 2.2.14 on 2022-04-26 17:02

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0016_auto_20220426_1654"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="order",
            name="items",
        ),
    ]
