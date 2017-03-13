# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division

from django.contrib.gis.geos import Point
from django.utils import timezone
from django.test.utils import override_settings

from treemap.audit import UserTrackingException
from treemap.models import Plot
from treemap.tests.base import OTMTestCase
from treemap.tests import make_instance, make_commander_user

from works_management.models import Team, Task, WorkOrder


def make_team(instance, name='Test Team'):
    t = Team()
    t.instance = instance
    t.name = name
    t.save()
    return t


def make_work_order(instance, user):
    w = WorkOrder()
    w.instance = instance
    w.created_by = user
    w.save_with_user(user)
    return w


def make_task(instance, user, map_feature, name='Test Task', team=None):
    t = Task()
    t.instance = instance
    t.map_feature = map_feature
    t.team = team
    t.name = name
    t.created_by = user
    t.requested_on = timezone.now()
    t.scheduled_on = timezone.now()
    t.closed_on = timezone.now()
    t.save_with_user(user)
    return t


def make_plot(instance, user):
    p = Point(0, 0)
    plot = Plot(geom=p, instance=instance)
    plot.save_with_user(user)
    return plot


@override_settings(FEATURE_BACKEND_FUNCTION=None)
class WorksManagementTests(OTMTestCase):
    def setUp(self):
        self.instance = make_instance()
        self.instance.initialize_udfs([Task.__name__], [Task])
        self.user = make_commander_user(self.instance)
        self.team = make_team(self.instance)

    def test_work_order(self):
        w = make_work_order(self.instance, self.user)

        plot = make_plot(self.instance, self.user)
        t = make_task(self.instance, self.user, plot)
        t.work_order = w
        t.save_with_user(self.user)
        self.assertEqual(1, w.tasks.count())

        # Test that WorkOrder updated_at field updates when Tasks update
        old_updated_at = w.updated_at
        t.status = Task.COMPLETED
        t.save_with_user(self.user)

        w = WorkOrder.objects.get(id=w.id)
        self.assertTrue(w.updated_at > old_updated_at)

    def test_cannot_call_save_on_workorder(self):
        # WorkOrder is Auditible and should only allow calling save_with_user.
        w = make_work_order(self.instance, self.user)
        with self.assertRaises(UserTrackingException):
            w.save()

    def test_cannot_call_save_on_task(self):
        # Task is Auditible and should only allow calling save_with_user.
        t = make_task(self.instance, self.user,
                      make_plot(self.instance, self.user))
        with self.assertRaises(UserTrackingException):
            t.save()

    def test_task_udf(self):
        t = make_task(self.instance, self.user,
                      make_plot(self.instance, self.user))
        t.udfs['Action'] = 'Plant Tree'
        t.save_with_user(self.user)

        count = Task.objects.filter(**{'udf:Action': 'Plant Tree'}).count()
        self.assertEqual(1, count)
