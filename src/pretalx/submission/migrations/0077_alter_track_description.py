# Generated by Django 4.2.10 on 2024-02-22 10:00

from django.db import migrations
import tinymce.models


class Migration(migrations.Migration):

    dependencies = [
        ("submission", "0076_alter_cfp_text"),
    ]

    operations = [
        migrations.AlterField(
            model_name="track",
            name="description",
            field=tinymce.models.HTMLField(),
        ),
    ]
