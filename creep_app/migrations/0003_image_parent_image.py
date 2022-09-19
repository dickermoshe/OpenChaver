# Generated by Django 4.1.1 on 2022-09-18 20:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('creep_app', '0002_alter_image_is_nsfw'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='parent_image',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='creep_app.image'),
        ),
    ]
