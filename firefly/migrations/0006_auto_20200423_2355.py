# Generated by Django 3.0.3 on 2020-04-23 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('firefly', '0005_auto_20200423_1844'),
    ]

    operations = [
        migrations.AlterField(
            model_name='example_data',
            name='example_id',
            field=models.IntegerField(unique=True),
        ),
    ]
