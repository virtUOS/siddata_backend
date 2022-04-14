"""
This module contains all db-related tasks which needs to be executed periodically or as a cron job.
The main packages used here to schedule these tasks are `django-apscheduler` and `apscheduler`
For reference follow below links:
    - https://apscheduler.readthedocs.io/en/stable/index.html
    - https://medium.com/better-programming/introduction-to-apscheduler-86337f3bb4a6
    - https://github.com/jcass77/django-apscheduler#quick-start
    - https://medium.com/@mrgrantanderson/replacing-cron-and-running-background-tasks-in-django-using-apscheduler-and-django-apscheduler-d562646c062e#318c

For any specific job, a function should be created which should encapsulate all details of the task, and it should be
decoupled from the task scheduler, i.e. it should only do the task required. e.g. `task_dummy` function.
All tasks should follow the naming convention as `task_<name of task>`.

To execute (schedule) any task, the task should be added as a job in the `add_jobs` function of this module, which schedules and starts these tasks.
The add_jobs function either gets automatically executed by the AppConfig with the start of Django (see scheduled_tasks.scheduler.start, backend.apps.BackendConfig), or
executed using the runapscheduler-command (backend.management.commands.runapscheduler.Command), which make sure these tasks will be scheduled with start of django application.
Further, the tasks will be added to a database-entry which can be managed through the Django-Management-Interface.
"""

from apscheduler.triggers.cron import CronTrigger
from django_apscheduler.models import DjangoJobExecution
from django.conf import settings

import csv
import glob
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
import inspect

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
import backend.models
from backend.models import WebResource
from settings import BASE_DIR

from bert_app import recommender_backbone
from recommenders import recommender_functions
from dashboard import raw_data
from scheduled_tasks import educational_resource_functions


def delete_old_job_executions(max_age=604_800):
    """This job deletes all apscheduler job executions older than `max_age` from the database."""
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


def add_jobs(scheduler):
    """
    Here new tasks can be added for scheduled execution.
    """
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    # Add Jobs here
    # - replace_existing in combination with the unique ID prevents duplicate copies of the job
    # scheduler.add_job("core.models.MyModel.my_class_method", "cron", id="my_class_method", hour=0, replace_existing=True)
    scheduler.add_job(delete_old_job_executions, trigger=CronTrigger(day_of_week="mon", hour="00", minute="00"),
                      id="delete_old_job_executions", max_instances=1, replace_existing=True, )

    scheduler.add_job(task_add_backend_resources, 'interval', minutes=10, id="add_backend_resources", replace_existing=True)
    scheduler.add_job(task_classify_new_resources_bert, 'cron', start_date=today, hour=20, id="classify_new_resources_bert", replace_existing=True)
    scheduler.add_job(task_execute_recommender_cron_functions,'interval',hours=6, id="execute_recommender_cron_functions", replace_existing=True)
    scheduler.add_job(task_initialize_templates, id="initialize_templates", replace_existing=True)
    scheduler.add_job(task_collect_educational_resources, 'cron', start_date=today, hour=20, replace_existing=True)

    scheduler.add_job(task_create_rawdataexportcsv, 'cron', start_date=today, hour=23, id="create_rawdataexportcsv", replace_existing=True)
    scheduler.add_job(task_create_rawdataexportcsv, next_run_time=datetime.now() + timedelta(minutes=1), id="create_rawdataexportcsv", replace_existing=True)

    scheduler.add_job(task_send_admin_report, 'cron', start_date=tomorrow, hour=0, id="send_admin_report", replace_existing=True)


def task_dummy():
    """
    Create the dummy task which you want to accomplish here.
    This task should be agnostic of scheduled time, i.e. just do the task.
    :return:
    """
    logger = logging.getLogger("scheduled_tasks.db_tasks.task_dummy")
    if "LOG_LEVEL" in os.environ and not getattr(settings, "QUIET_SCHEDULER", False):
        logger.setLevel(int(os.environ["LOG_LEVEL"]))
    else:
        logger.setLevel(logging.WARNING)

    logger.info("I am doing some task.")

    logger.info(f"Task completed at time: {datetime.now()}")


def task_add_backend_resources():
    """
    This function add new rows in backend_resources table.
    It will read files from data folder and add all rows from the csv into database if valid, and move file
    to processed folder.

    No header is required, but the order of the columns should be as follow:
        - title;description;url
    Name of the file should have following extension:
        - .csv
    Place of the file: BASE_DIR / 'data' / 'csv_files' / 'database' / 'resources'
        -

    :return:
    """

    logger = logging.getLogger("scheduled_tasks.db_tasks.task_add_backend_resources")
    if "LOG_LEVEL" in os.environ and not getattr(settings, "QUIET_SCHEDULER", False):
        logger.setLevel(int(os.environ["LOG_LEVEL"]))
    else:
        logger.setLevel(logging.WARNING)
    logger.info("Checking for new files in data folder for new resources.")
    base_dir = Path(BASE_DIR)
    data_dir = base_dir.parent / 'data' / 'csv_files' / 'database' / 'resources'

    # check for all csv files in the current folder
    csv_files = glob.glob(str(data_dir) + "/*.csv")
    for file in csv_files:
        logger.debug(f"processing file: {file}")
        resource_objs = []  # database objects for resource model
        with open(file, mode='r') as current_file:
            csv_reader = csv.reader(current_file, delimiter=';')
            line_count = 0
            for row in csv_reader:
                # if line_count == 0:
                #     logger.debug(f"Headers/column names are: {', '.join(row)}")
                #     line_count += 1
                #     continue
                # # check for validity of values:
                if row[0] == '':  # if there is no title skip the row
                    continue
                if row[1] == '':  # if there is no description, skip the row
                    continue
                # check for validity of url field:
                validate = URLValidator()
                try:  # if url is not valid skip the row
                    validate(row[2])
                except ValidationError:
                    logger.debug(f"url field is not valid for this row {', '.join(row)}")
                    continue

                # add row to the database in backend_resources if it is already not there
                if not WebResource.objects.filter(
                        title=row[0],
                        description=row[1],
                        source=row[2]
                ).exists():
                    resource_objs.append(
                        WebResource(
                            title=row[0],
                            description=row[1],
                            source=row[2]
                        ))

                line_count += 1
        logger.debug("Adding rows in backend_resources model")
        WebResource.objects.bulk_create(resource_objs)  # use of bulk create is used for faster execution

        logger.debug("moving file to old dir")
        os.rename(file, str(data_dir / 'old' / Path(file).stem) + datetime.now().strftime("%d%m%Y%H%M%S") + ".csv")


def task_classify_new_resources_bert():
    """
    This function is responsible for scheduling the classification of new resources.
    Resources get classified into a DDC class with the SidBERT app.
    :return:
    """
    logger = logging.getLogger("scheduled_tasks.db_tasks.task_classify_new_resources_bert")
    if "LOG_LEVEL" in os.environ and not getattr(settings, "QUIET_SCHEDULER", False):
        logger.setLevel(int(os.environ["LOG_LEVEL"]))
    else:
        logger.setLevel(logging.WARNING)
    logger.info("Checking for new database resources without ddc label.")
    classifier = recommender_backbone.ProfessionsRecommenderBackbone()
    count_updated_resources_bert = classifier.update_resources_bert()
    if count_updated_resources_bert == 0:
        logger.info('No new resources to classify for SidBERT')
    else:
        msg = 'Updated '+str(count_updated_resources_bert) + 'new resources with DDC labels.'
        logger.info(msg)
        #utils.add_report_message(msg, 'BERT Classification')


def task_execute_recommender_cron_functions():
    logger = logging.getLogger("scheduled_tasks.task_execute_recommender_cron")
    if "LOG_LEVEL" in os.environ and not getattr(settings, "QUIET_SCHEDULER", False):
        logger.setLevel(int(os.environ["LOG_LEVEL"]))
    else:
        logger.setLevel(logging.WARNING)
    logger.info('Starting recommender cron job functions')
    for recommender in recommender_functions.get_active_recommenders():
        recommender.execute_cron_functions()
    logger.info('Recommender cron job functions executed successfully')


def task_initialize_templates():
    logger = logging.getLogger("scheduled_tasks.task_initialize_templates")
    if "LOG_LEVEL" in os.environ and not getattr(settings, "QUIET_SCHEDULER", False):
        logger.setLevel(int(os.environ["LOG_LEVEL"]))
    else:
        logger.setLevel(logging.WARNING)
    logger.info('Starting recommender initialize template functions')
    for recommender in recommender_functions.get_active_recommenders():
        recommender.initialize_templates()
    logger.info('Recommender initialize template functions executed successfully')


def task_collect_educational_resources():
    logger = logging.getLogger("scheduled_tasks.task_collect_educational_resources")
    logger.info('Collecting educational resources')
    educational_resource_functions.collect_educational_resources()
    logger.info('Collecting educational resources finished')


def task_create_rawdataexportcsv():
    logger = logging.getLogger("scheduled_tasks."+inspect.currentframe().f_code.co_name)
    if "LOG_LEVEL" in os.environ and not getattr(settings, "QUIET_SCHEDULER", False):
        logger.setLevel(int(os.environ["LOG_LEVEL"]))
    else:
        logger.setLevel(logging.WARNING)
    logger.info('Start exporting raw data...')
    raw_data.get_raw_data()
    logger.info('Raw data successful.')


def task_send_admin_report():
    report = backend.models.AdminReport.get_pending_report()
    report.send_to_admins()
