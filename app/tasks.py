import os
import re
import time
from collections import namedtuple

from celery import shared_task
from datetime import datetime

from django_celery_beat.utils import make_aware
from django.core.files import File

from app.models import Watchtdog, Rack, SshConfig, ReportConfig, ReportArchive, Report
from app.utils.paramiko_wrapper import SftpApi, get_sftp_instance_by_hostname
from dashboard_racks import settings
from celery_progress.backend import ProgressRecorder

def purge(dir, pattern):
    for f in os.listdir(dir):
        if re.search(pattern, f):
            os.remove(os.path.join(dir, f))

@shared_task(queue='celery', name='archive_reports', bind=True)
def archive_reports(self, rack_pk):
    progress_recorder = ProgressRecorder(self)

    rack = Rack.objects.get(pk=rack_pk)
    ssh_config = rack.ssh_config

    progress_recorder.set_progress(1, 3, description=f'Connect to {ssh_config.hostname}')

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

    progress_recorder.set_progress(2, 3, description='Download files...')

    n_moved_files = sftp_api.move_from_remote_by_pattern(
        remote_dir=report_config.remote_report_path,
        local_path=local_path,
        remote_regex='.*\.html',
    )

    progress_recorder.set_progress(3, 3, description='Moving to archive..')

    for r in os.listdir(local_path):
        path = local_path + os.sep + r
        f = open(path)

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

    purge(dir=local_path, pattern=".*_Testresult.html")

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


@shared_task(queue='celery', name='pull_reports_task')
def pull_reports(*args, **kwargs):
    w, created = Watchtdog.objects.get_or_create(name="test_task")
    w.counter += 1
    w.save()
    print("pull reports")
    return "pull reports"
    # rack = Rack.objects.first()
    # ssh_config: SshConfig = rack.ssh_config
    # report_config: ReportConfig = rack.report_config
    #
    # sftp_api = get_sftp_instance_by_hostname(
    #     hostname=ssh_config.hostname,
    #     username=ssh_config.username,
    #     password=ssh_config.password,
    #     private_key=ssh_config.private_key.path if ssh_config.private_key else '',
    #     port=ssh_config.port,
    # )
    #
    # try:
    #     if not sftp_api.is_connected:
    #         sftp_api.connect()
    #
    #     sftp = sftp_api.get_sftp()
    #     reports = [x for x in sftp.listdir(report_config.remote_report_path) if x.endswith('.html')]
    #
    #     remote_report_collection = []
    #     Report = namedtuple('report', ['name', 'tag'])
    #     _err_cnt = 0
    #     for r in reports:
    #         _tag = 'success'
    #         if 'error' in r.lower():
    #             _tag = 'danger'
    #             _err_cnt += 1
    #         remote_report_collection.append(Report(r, _tag))
    #
    # except Exception as ex:
    #     messages.success(self.request, f"Failed to connect to {self.object.ssh_config.hostname}", extra_tags='danger')
    #     messages.success(self.request, f"Error message: {str(ex)}", extra_tags='danger')
    #
    # if reports:
    #     context['reports'] = reports
    # return context
    #
    #
