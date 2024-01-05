# Generated by Django 4.2.7 on 2023-12-08 15:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comics', '0008_comic_rename_referer'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ComicHistory',
            new_name='Strip',
        ),
        migrations.AlterModelOptions(
            name='unreadcomic',
            options={'ordering': ['user', '-strip']},
        ),
        migrations.RenameField(
            model_name='unreadcomic',
            old_name='history',
            new_name='strip',
        ),
    ]