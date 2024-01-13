# Generated by Django 4.2.7 on 2024-01-03 23:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comics', '0012_add_comic_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comic',
            name='active',
        ),
        migrations.RemoveField(
            model_name='comic',
            name='ended',
        ),
        migrations.AlterField(
            model_name='comic',
            name='no_images',
            field=models.BooleanField(default=False, help_text='Use it to hide the images of the comic, but allow a notification to the users.', verbose_name='Hide images in Strips'),
        ),
    ]
