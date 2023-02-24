from celery import shared_task
from datetime import datetime

from app.models import Watchtdog


@shared_task()
def write_log_file(email, message):
    print("Write to file")
    with open("log.file", 'w') as lf:
        lines =[email, message]
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
    w.counter +=1
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
