# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('works_management', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='reference_num',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='workorder',
            name='reference_num',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterUniqueTogether(
            name='task',
            unique_together=set([('instance', 'reference_num')]),
        ),
        migrations.AlterUniqueTogether(
            name='workorder',
            unique_together=set([('instance', 'reference_num')]),
        ),
    ]
