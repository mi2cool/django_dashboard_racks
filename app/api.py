import os
from datetime import datetime

import pytz
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.core.files import File

from dashboard_racks import settings
from .models import Rack, ReportArchive, Report
from .utils.paramiko_wrapper import SftpApi, get_sftp_instance_by_hostname

sftp = None
sftp_api = None


def delete_selected_reports(request, rack_pk):
    prefix = 'cb_report_'
    rack = get_object_or_404(Rack, pk=rack_pk)

    reports = []
    for k, v in request.POST.items():
        if prefix in k and v == 'on':
            pk = int(k.replace(prefix, ''))
            report = Report.objects.get(pk=pk)
            reports.append(report)

    for report in reports:
        file_path = os.path.join(settings.MEDIA_ROOT, report.file.name)
        if os.path.exists(file_path):
            os.remove(file_path)
        report.delete()

    next = request.GET.get('next', '/')
    return HttpResponseRedirect(next)


def archive_reports(request, rack_pk):
    rack = get_object_or_404(Rack, pk=rack_pk)
    ssh_config = rack.ssh_config
    report_config = rack.report_config
    archive, created = ReportArchive.objects.get_or_create(name=rack.name)
    if not rack.archive:
        rack.archive = archive
        rack.save()

    sftp_api = get_sftp_instance_by_hostname(
        hostname=ssh_config.hostname,
        username=ssh_config.username,
        password=ssh_config.password,
        private_key=ssh_config.private_key.url,
        port=ssh_config.port,
    )

    local_path = settings.MEDIA_ROOT + os.sep + rack.name

    if not sftp_api.is_connected:
        sftp_api.connect()

    os.makedirs(local_path, exist_ok=True)

    n_moved_files = sftp_api.move_from_remote_by_pattern(
        remote_dir=report_config.remote_report_path,
        local_path=local_path,
        remote_regex='.*\.html',
    )

    for r in os.listdir(local_path):
        path = local_path + os.sep + r
        f = open(path)

        fname = os.path.basename(r).split('_Testresult')[0]
        dt = datetime.strptime(fname, '%Y-%m-%d_%H-%M-%S')

        report: Report = Report.objects.get_or_create(
            archive=archive,
            verdict='PASSED' if 'error' not in r.lower() else 'FAILED',
            created=dt,
            name=r)[0]
        report.file.save(name=r, content=File(f), save=False)
        if os.path.exists(r):
            os.remove(r)
        report.save()

    messages.success(request, f'Moved {n_moved_files} files from {ssh_config.hostname} to archive.', extra_tags='success')

    next = request.GET.get('next', '/')
    return HttpResponseRedirect(next)
