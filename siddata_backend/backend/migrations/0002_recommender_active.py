# Generated by Django 3.1.2 on 2021-11-23 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='recommender',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
