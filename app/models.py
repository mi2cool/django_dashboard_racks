import os
import platform

from django.db import models
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import CrontabSchedule

from dashboard_racks import settings


class SshConfig(models.Model):
    hostname = models.CharField(_("Hostname"), max_length=254, default='<hostname>')
    username = models.CharField(_("Username"), max_length=128, null=True)
    password = models.CharField(_("Password"), max_length=128, null=True, blank=True)
    private_key = models.FileField(_('Private key'), null=True, blank=True)
    port = models.BigIntegerField(_("Port"), default=22)

    def __str__(self):
        return self.hostname


class ReportConfig(models.Model):
    remote_report_path = models.CharField(
        verbose_name=_('remote report path'),
        max_length=254,
        default='/home/admin/',
    )
    from django_celery_beat.models import PeriodicTasks

    pull_reports_time = models.TimeField(
        verbose_name='Pull reports time',
        null=True,
        blank=True
    )

    contrab_schedule = models.ForeignKey(
        CrontabSchedule,
        on_delete=models.CASCADE,
        null=True,
        related_name='report_config',
        blank=True
    )

    def __str__(self):
        return 'Report Config'


class Rack(models.Model):
    name = models.CharField(max_length=254, verbose_name=_('Rack name'))
    ssh_config = models.ForeignKey(
        'SshConfig',
        on_delete=models.CASCADE,
        verbose_name='SSH/SFTP configuration',
        null=True,
        blank=True
    )
    report_config = models.ForeignKey(
        'ReportConfig',
        on_delete=models.CASCADE,
        verbose_name='Report configuration',
        null=True,
        blank=True
    )
    archive = models.ForeignKey(
        'ReportArchive',
        on_delete=models.CASCADE,
        verbose_name='Archive',
        null=True,
        related_name='rack',
        blank=True
    )

    def get_absolute_url(self):
        return reverse_lazy('rack-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name


class ReportArchive(models.Model):
    name = models.CharField(max_length=254, verbose_name=_('Name of rack'))

    def get_number_of_passed(self):
        n = len([r for r in self.reports.all() if r.verdict.lower() == 'passed'])
        return n

    def get_number_of_failed(self):
        n = len([r for r in self.reports.all() if r.verdict.lower() == 'failed'])
        return n

    def __str__(self):
        return self.name


def rack_archive_report_upload_path(instance, filename):
    return 'archive_{0}/{1}'.format(instance.archive.name, filename)


class Report(models.Model):
    VERDICT_CHOICES = [
        ('', '---------'),  # replace the value '----' with whatever you want, it won't matter
        ('PASSED', 'Passed'),
        ('FAILED', 'Failed'),
    ]

    name = models.CharField(
        max_length=254,
        verbose_name=_('Name of report')
    )
    archive = models.ForeignKey(
        'ReportArchive',
        on_delete=models.CASCADE,
        verbose_name='Archive',
        null=True,
        related_name='reports'
    )

    file = models.FileField(
        upload_to=rack_archive_report_upload_path,
        null=True
    )

    verdict = models.CharField(
        max_length=10,
        choices=VERDICT_CHOICES,
        null=True
    )

    created = models.DateTimeField(
        verbose_name='Created',
        null=True,

    )

    class Meta:
        ordering = ['created']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse_lazy('rack-detail', kwargs={'pk': self.pk, 'rack_pk': self.archive.rack.pk})


class Watchtdog(models.Model):
    name = models.CharField(
        max_length=254,
        null=True
    )
    counter = models.IntegerField()
