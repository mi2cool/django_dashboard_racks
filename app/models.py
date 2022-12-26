import os
import platform

from django.db import models
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from dashboard_racks import settings


class SshConfig(models.Model):
    hostname = models.CharField(_("Hostname"), max_length=254, default='<hostname>')
    username = models.CharField(_("Username"), max_length=128, null=True)
    password = models.CharField(_("Password"), max_length=128, null=True)
    private_key = models.FileField(_('Private key'), null=True)
    port = models.BigIntegerField(_("Port"), default=21)

    def __str__(self):
        return self.hostname


class ReportConfig(models.Model):
    remote_report_path = models.CharField(
        verbose_name=_('remote report path'),
        max_length=254,
        default='~/'
    )

    report_archive_path = models.CharField(
        verbose_name=_('report archive'),
        max_length=254,
        default=os.path.join(os.environ.get('USERPROFILE'), 'racks', 'report_archive') if platform.system().lower() == 'windows' else os.path.join('~/', 'racks', 'report_archive')
    )

    def __str__(self):
        return 'Report Config'


class Rack(models.Model):
    name = models.CharField(max_length=254, verbose_name=_('Rack name'))
    ssh_config = models.ForeignKey(
        'SshConfig',
        on_delete=models.CASCADE,
        verbose_name='SSH/SFTP configuration',
        null=True
    )
    report_config = models.ForeignKey(
        'ReportConfig',
        on_delete=models.CASCADE,
        verbose_name='Report configuration',
        null=True
    )

    def get_absolute_url(self):
        return reverse_lazy('rack-detail', kwargs={'pk': self.pk})

    def __str__(self):
        return self.name
