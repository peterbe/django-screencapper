# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CallbackResponse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField()),
                ('status_code', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField()),
                ('callback_url', models.URLField()),
                ('submitted', models.DateTimeField(default=django.utils.timezone.now)),
                ('number', models.IntegerField(default=10)),
                ('post_files', models.BooleanField(default=False)),
                ('post_files_individually', models.BooleanField(default=False)),
                ('post_file_name', models.CharField(default=b'files', max_length=100)),
                ('download', models.BooleanField(default=False)),
                ('stats', jsonfield.fields.JSONField(default=dict)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='callbackresponse',
            name='submission',
            field=models.ForeignKey(to='api.Submission'),
            preserve_default=True,
        ),
    ]
