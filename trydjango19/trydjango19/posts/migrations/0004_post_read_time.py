# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-28 08:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0003_auto_20170424_2330'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='read_time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]