# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import screencapper.receiver.models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Picture',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.ImageField(upload_to=screencapper.receiver.models.upload_to)),
                ('url', models.URLField()),
                ('uploaded', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
