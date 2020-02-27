# Generated by Django 3.0.3 on 2020-02-27 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('firefly', '0010_auto_20200227_1632'),
    ]

    operations = [
        migrations.CreateModel(
            name='Example_Data',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(blank=True, upload_to='')),
                ('description', models.CharField(max_length=100)),
            ],
        ),
        migrations.AlterModelOptions(
            name='job_submission',
            options={'verbose_name': 'Job Submission'},
        ),
        migrations.RenameField(
            model_name='job_submission',
            old_name='results_id',
            new_name='job_id',
        ),
        migrations.RenameField(
            model_name='sed',
            old_name='results_id',
            new_name='job_id',
        ),
    ]