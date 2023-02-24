from django_celery_beat.models import PeriodicTask, IntervalSchedule, PeriodicTasks

# executes every 10 seconds.
schedule, created = IntervalSchedule.objects.get_or_create(
    every=10,
    period=IntervalSchedule.SECONDS,
)
PeriodicTask.objects.create(
    interval=schedule,                  # we created this above.
    name='test',          # simply describes this periodic task.
    task='app.tasks.add',  # name of task.
    args=[1]
)