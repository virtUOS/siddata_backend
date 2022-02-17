"""
Using this command, you can manually run the scheduler, as specified in https://github.com/jcass77/django-apscheduler#quick-start.
Note that when running the Siddata-Backend either productivly or using manage.py, you DONT NEED TO RUN THIS, as the `backend.apps.BackendConfig`
(backend.apps.BackendConfig) ensures that a Background-Scheduler is run whenever the main backend is run.
"""

import logging

from django.conf import settings

from apscheduler.schedulers.blocking import BlockingScheduler
from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Runs apscheduler per command (also gets auto-started thanks to the backend-app-config!)"

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(settings.SCHEDULER_CONFIG, timezone=settings.TIME_ZONE)
        try:
            scheduler.add_jobstore(DjangoJobStore(), "default")
        except ValueError:
            pass
        from scheduled_tasks.db_tasks import add_jobs
        add_jobs(scheduler)

        try:
            logger.info("Starting scheduler...")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Stopping scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully!")