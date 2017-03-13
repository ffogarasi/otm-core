# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from django.contrib.gis.db import models
from django.db.models import Max
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from treemap.models import MapFeature, User
from treemap.audit import Auditable
from treemap.udf import UDFModel
from treemap.instance import Instance


class Team(models.Model):
    instance = models.ForeignKey(Instance)
    name = models.CharField(max_length=255, null=False, blank=False)


class WorkOrder(Auditable, models.Model):
    instance = models.ForeignKey(Instance)
    name = models.CharField(max_length=255, null=False, blank=False)
    reference_num = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('instance', 'reference_num')

    def get_next_reference_num(self):
        """
        Return next sequential reference number for instance.
        """
        agg_result = Instance.objects.filter(id=self.instance.id) \
            .annotate(max_value=Max('workorder__reference_num'))[0]
        max_value = agg_result.max_value or 0
        return max_value + 1

    def save_with_user(self, user, *args, **kwargs):
        if not self.id:
            self.reference_num = self.get_next_reference_num()
        super(WorkOrder, self).save_with_user(user, *args, **kwargs)


class Task(UDFModel, Auditable):
    REQUESTED = 0
    SCHEDULED = 1
    COMPLETED = 2
    CANCELED = 3

    STATUS_CHOICES = (
        (REQUESTED, _('Requested')),
        (SCHEDULED, _('Scheduled')),
        (COMPLETED, _('Completed')),
        (CANCELED, _('Canceled')),
    )

    instance = models.ForeignKey(Instance)
    map_feature = models.ForeignKey(MapFeature)
    work_order = models.ForeignKey(WorkOrder, null=True, related_name='tasks')
    team = models.ForeignKey(Team, null=True)

    reference_num = models.IntegerField(default=0)
    office_notes = models.TextField()
    field_notes = models.TextField()

    status = models.IntegerField(
        choices=STATUS_CHOICES,
        default=REQUESTED)

    requested_on = models.DateField()
    scheduled_on = models.DateField()
    closed_on = models.DateField()

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User)
    updated_at = models.DateTimeField(auto_now=True)

    udf_settings = {
        'Action': {
            'iscollection': False,
            'is_protected': True,
            'defaults': {
                'type': 'choice',
                'protected_choices': [
                    'Plant Tree',
                    'Remove Tree',
                ],
                'choices': [],
            }
        },
    }

    class Meta:
        unique_together = ('instance', 'reference_num')

    def get_next_reference_num(self):
        """
        Return next sequential reference number for instance.
        """
        agg_result = Instance.objects.filter(id=self.instance.id) \
            .annotate(max_value=Max('task__reference_num'))[0]
        max_value = agg_result.max_value or 0
        return max_value + 1

    def save_with_user(self, user, *args, **kwargs):
        """
        Update WorkOrder fields when Task is saved.
        """
        if not self.id:
            self.reference_num = self.get_next_reference_num()

        if self.work_order:
            self.work_order.updated_at = timezone.now()
            self.work_order.save_with_user(user, *args, **kwargs)

        super(Task, self).save_with_user(user, *args, **kwargs)
