
### install redisw with docker 
```
docker pull redis 
docker run -d --name redis-stack-server -p 6379:6379 redis/redis-stack-server:latest
docker exec -it redis-stack redis-cli
```

### Schedule with celery 
[Celery Schedule](https://docs.celeryq.dev/en/stable/userguide/periodic-tasks.html)


### Run celery
```
celery -A dashboard_racks beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### celery beat integrated (used in this app)
[django_celery_beat](https://django-celery-beat.readthedocs.io/en/latest/)
    
run worker with beat:
```
$ celery -A [project-name] worker --beat --scheduler django --loglevel=info
celery -A dashboard_racks worker --beat --scheduler django --loglevel=info

celery -A dashboard_racks beat -l debug -S django
```

### Sample that worked
[realpython.com/django-celery-tasks](https://realpython.com/asynchronous-tasks-with-django-and-celery/)
```
python -m celery -A dashboard_racks worker -l info
```


### Celery as a daemon service 
```https://docs.celeryq.dev/en/stable/userguide/daemonizing.html```
