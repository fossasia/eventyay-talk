# Generated by Django 4.2.10 on 2024-03-05 21:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("person", "0028_user_avatar_license"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="avatar_license",
            field=models.TextField(null=True),
        ),
    ]
