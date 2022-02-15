# Generated by Django 3.2.8 on 2022-02-13 20:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('picks', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RaceResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.SmallIntegerField()),
                ('points', models.SmallIntegerField()),
                ('driver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='picks.racedriver')),
                ('race', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='picks.race')),
            ],
            options={
                'verbose_name': 'Race Result',
                'verbose_name_plural': 'Race Results',
                'ordering': ('race', 'position'),
                'unique_together': {('race', 'position'), ('race', 'driver')},
            },
        ),
    ]