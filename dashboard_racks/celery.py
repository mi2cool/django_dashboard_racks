import os
from collections import namedtuple

from celery import Celery, shared_task

# from app.models import Rack, SshConfig, ReportConfig
# from app.utils.paramiko_wrapper import get_sftp_instance_by_hostname

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dashboard_racks.settings')

app = Celery('dashboard_racks')
# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


# @app.task(bind=True)
# def debug_task(self):
#     print(f'Request: {self.request!r}')
#
#     import schedule as schedule
#     from celery import shared_task
#     from celery.schedules import crontab
#
#     from dashboard_racks.celery import app
#     import logging


# @app.on_after_finalize.connect
# def setup_periodic_tasks(sender, **kwargs):
#     # Calls test('hello') every 10 seconds.
#     sender.add_periodic_task(10.0, test.s('hello'), name='add every 10')
#
#     # Calls test('world') every 30 seconds
#     sender.add_periodic_task(30.0, test.s('world'), expires=10)
#
#     # # Executes every Monday morning at 7:30 a.m.
#     # sender.add_periodic_task(
#     #     crontab(hour=7, minute=30, day_of_week=1),
#     #     test.s('Happy Mondays!'),
#     # )

@app.task
def test(arg='test'):

    with open("/home/micha/webapps/dashboard_rackz/aaaa.txt", 'w') as my_file:
        my_file.write("Hallo")

    print(arg + '3')

    return 11


@app.task
def add(x, y):
    z = x + y
    print(z)


@shared_task(queue='celery', name='mytask')
def say_hello2():
    import logging
    from celery.utils.log import get_task_logger
    logger = get_task_logger('celery.task')
    logger2 = logging.getLogger('mycelery')
    logger.setLevel(logging.DEBUG)
    logger.error("foobar")
    logger2.error("foobar")

