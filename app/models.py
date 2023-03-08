import os
import platform

from django.db import models
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from django_celery_beat.models import PeriodicTasks

from app.utils.parser import purge
from dashboard_racks import settings


class SshConfig(models.Model):
    name = models.CharField(_("Name"), max_length=64, blank=True, null=True)
    hostname = models.CharField(_("Hostname"), max_length=254, default='<hostname>')
    username = models.CharField(_("Username"), max_length=128, null=True)
    password = models.CharField(_("Password"), max_length=128, null=True, blank=True)
    private_key = models.FileField(_('Private key'), null=True, blank=True)
    port = models.BigIntegerField(_("Port"), default=22)

    def __str__(self):
        return self.hostname


class ReportConfig(models.Model):
    name = models.CharField(max_length=64, verbose_name=_('name'), blank=True, null=True)
    remote_report_path = models.CharField(
        verbose_name=_('remote report path'),
        max_length=254,
        default='/home/admin/',
    )

    periodic_task = models.OneToOneField(
        PeriodicTask,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name


class Rack(models.Model):
    name = models.CharField(max_length=254, verbose_name=_('Rack name'))
    ssh_config = models.OneToOneField(
        'SshConfig',
        on_delete=models.CASCADE,
        verbose_name='SSH/SFTP configuration',
        null=True,
        blank=True
    )
    report_config = models.OneToOneField(
        'ReportConfig',
        on_delete=models.CASCADE,
        verbose_name='Report configuration',
        null=True,
        blank=True
    )
    archive = models.OneToOneField(
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

    def get_latest_report(self):
        x = self.reports.all().first()
        reports = self.reports.all().order_by('created').reverse()
        last =  reports.first().created.strftime("%d.%m.%Y, %H:%M:%S") if reports else None
        return last

    def __str__(self):
        return self.name


def rack_archive_report_upload_path(instance, filename):
    name = 'archive_{0}/{1}'.format(instance.archive.name, filename)
    archive_dir = os.path.join(settings.MEDIA_ROOT, os.path.dirname(name))
    media_file = os.path.join(settings.MEDIA_ROOT, filename)

    if not os.path.exists(archive_dir):
        os.mkdir(archive_dir)

    # rm if already exists
    purge(archive_dir, f"{filename.split('.html')[0]}(_[a-zA-Z0-9]{{7}}.||.)html")

    if os.path.exists(media_file):
        os.remove(media_file)
    return name


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
