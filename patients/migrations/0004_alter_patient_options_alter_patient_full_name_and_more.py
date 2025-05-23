# Generated by Django 4.2.7 on 2025-04-28 01:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0003_remove_patient_district'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='patient',
            options={'ordering': ['patient_id']},
        ),
        migrations.AlterField(
            model_name='patient',
            name='full_name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='patient',
            name='gender',
            field=models.CharField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], max_length=10),
        ),
    ]
