# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-31 15:11
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comics', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comic',
            old_name='last_check',
            new_name='last_update',
        ),
    ]
