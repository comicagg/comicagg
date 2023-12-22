# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-02-21 15:05
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comics', '0004_rename_fields_votes'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comic',
            old_name='backwards',
            new_name='re1_backwards',
        ),
        migrations.RenameField(
            model_name='comic',
            old_name='base_img',
            new_name='re1_base',
        ),
        migrations.RenameField(
            model_name='comic',
            old_name='regexp',
            new_name='re1_re',
        ),
        migrations.RenameField(
            model_name='comic',
            old_name='url',
            new_name='re1_url',
        ),
        migrations.RenameField(
            model_name='comic',
            old_name='backwards2',
            new_name='re2_backwards',
        ),
        migrations.RenameField(
            model_name='comic',
            old_name='base2',
            new_name='re2_base',
        ),
        migrations.RenameField(
            model_name='comic',
            old_name='regexp2',
            new_name='re2_re',
        ),
        migrations.RenameField(
            model_name='comic',
            old_name='url2',
            new_name='re2_url',
        ),
    ]
