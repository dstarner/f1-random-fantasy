# Generated by Django 4.0.2 on 2022-02-12 17:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('picks', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schedule',
            name='year',
            field=models.PositiveIntegerField(unique=True),
        ),
    ]