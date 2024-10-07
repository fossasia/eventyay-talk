# Generated by Django 4.2.16 on 2024-10-07 16:20

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("submission", "0078_submissionfavourite"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="submissionfavourite",
            unique_together={("user", "submission")},
        ),
    ]
