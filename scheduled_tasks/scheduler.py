import logging, os

from apscheduler.schedulers.background import BackgroundScheduler
from scheduled_tasks.db_tasks import add_jobs

from django.conf import settings

##############################################################

scheduler = BackgroundScheduler(settings.SCHEDULER_CONFIG, timezone=settings.TIME_ZONE)

def start():
    """
    This function is responsible for scheduling and starting all tasks when running the backend. It gets automatically executed
    both when you run manage.py (as long as `backend.apps.BackendConfig` and `django_apscheduler` are in settings.INSTALLED_APPS),
    which means you don't have to run anything manually. All jobs added here will automatically be stored in a special Django-Database.
    These tasks can be scheduled to run on a particular time, or after fix intervals.
    Taken from https://medium.com/@mrgrantanderson/replacing-cron-and-running-background-tasks-in-django-using-apscheduler-and-django-apscheduler-d562646c062e#318c.
    Note that there MAY still be issues in productive settings, because the scheduler will be multithreaded, and "if each worker process ends up running its own
    scheduler then this could result in jobs being missed or executed multiple times, as well as duplicate entries in the DjangoJobExecution tables being created."
    (see https://github.com/jcass77/django-apscheduler#quick-start, https://stackoverflow.com/questions/65989475/configure-django-apscheduler-with-apache-mod-wsgi/67160634#67160634)
    If you DON'T want to start the scheduler automatically, make sure to set `SCHEDULER_AUTOSTART = False` in the settings.py. In that case you'd have to manually run
    the command at backend.management.commands.runapscheduler.Command.
    """
    logger = logging.getLogger("apscheduler")
    if settings.DEBUG:
        # Hook into the apscheduler logger
        if "LOG_LEVEL" in os.environ and not getattr(settings, "QUIET_SCHEDULER", False):
            logger.setLevel(int(os.environ["LOG_LEVEL"]))
        else:
            logger.setLevel(logging.WARNING)
        logger.debug("Scheduling all tasks")

    add_jobs(scheduler=scheduler)
    logger.info("starting scheduler")
    scheduler.start()
