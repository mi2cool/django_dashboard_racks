import os
import re
import time
from collections import namedtuple

from celery import shared_task
from datetime import datetime

from django_celery_beat.utils import make_aware
from django.core.files import File

from app.models import Rack, SshConfig, ReportConfig, ReportArchive, Report
from app.utils.paramiko_wrapper import SftpApi, get_sftp_instance_by_hostname
from app.utils.parser import purge
from dashboard_racks import settings
from celery_progress.backend import ProgressRecorder


@shared_task(queue='celery', name='archive_reports', bind=True)
def archive_reports(self, rack_pk):
    progress_recorder = ProgressRecorder(self)
    n_tasks = 4

    rack = Rack.objects.get(pk=rack_pk)
    ssh_config = rack.ssh_config

    progress_recorder.set_progress(1, n_tasks, description=f'Connect to {ssh_config.hostname}')

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
        private_key=ssh_config.private_key.path if ssh_config.private_key else '',
        port=ssh_config.port,
    )

    local_path = settings.MEDIA_ROOT + rack.name

    if not sftp_api.is_connected:
        sftp_api.connect()

    os.makedirs(local_path, exist_ok=True)

    progress_recorder.set_progress(2, n_tasks, description='Download files...')

    n_moved_files = sftp_api.move_from_remote_by_pattern(
        remote_dir=report_config.remote_report_path,
        local_path=local_path,
        remote_regex='.*\.html',
    )

    progress_recorder.set_progress(3, n_tasks, description='Moving to archive..')

    for r in os.listdir(local_path):
        path = local_path + os.sep + r
        f = open(path, encoding='latin-1')

        fname = os.path.basename(r).split('_Testresult')[0]
        dt = datetime.strptime(fname, '%Y-%m-%d_%H-%M-%S')
        dt = make_aware(dt)

        report: Report = Report.objects.get_or_create(
            archive=archive,
            verdict='PASSED' if 'error' not in r.lower() else 'FAILED',
            created=dt,
            name=r)[0]
        report.file.save(name=r, content=File(f), save=False)
        report.save()

    try:
        progress_recorder.set_progress(4, n_tasks, description='Cleanup..')
        purge(dir=local_path, pattern=".*.html")
    except Exception as ex:
        print(f"Error Message: {ex}")

    return 'Download was successful!'


@shared_task()
def write_log_file(email, message):
    print("Write to file")
    with open("log.file", 'w') as lf:
        lines = [email, message]
        lf.writelines(lines)


@shared_task(name="print_msg_main")
def print_message(message, *args, **kwargs):
    x = f"Celery is working!! Message is {message}"
    print(f"Celery is working!! Message is {message}")

    with open("hello.txt", 'w') as my_file:
        my_file.write("Hallo")

    return x
