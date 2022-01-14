#!/usr/bin/env python
import os
import sys
import logging
import importlib
import traceback
from django.conf import settings


import django.db.utils

DEFAULT_DEFAULT_LOG_LEVEL = "INFO"

def setup_django_dry(logger_name=None):
    """function to setup Django as needed. Can be imported from other scripts such that they don't rely on being started through manage.py, so ones
    that are neither custom commands nor recommenders or the like. They just need to run this function, and if they need to get some settings from
    django this even returns the settings-file to be used. If logger_name is not None, will also return a set-up logger."""
    if not os.environ.get("DJANGO_SETTINGS_MODULE"):
        sys.path.append(os.path.dirname(__file__))
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "siddata_backend.settings")
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true" #needed such that django can display in notebooks
        os.environ["DJANGO_DRYRUN"] = "true"
        import django
        from django.core.wsgi import get_wsgi_application
        django.conf.settings.INSTALLED_APPS = [i for i in django.conf.settings.INSTALLED_APPS if not any(j in i for j in ['BertAppConfig'])]
        get_wsgi_application()
        django.setup()
        setup_logging(*parse_command_line_args())
    settings = importlib.import_module(os.environ["DJANGO_SETTINGS_MODULE"])
    if logger_name is not None:
        logger = logging.getLogger(logger_name)
        if "LOG_LEVEL" in os.environ:
            logger.setLevel(int(os.environ["LOG_LEVEL"]))
    else:
        logger = None
    return settings, logger


def parse_command_line_args():
    """cannot use argparse or the like because Django needs most arguments, so this must do."""
    log_lvl = None #default (then it takes settings.DEFAULT_LOG_LEVEL)
    logfile = None #default
    iterator = iter(sys.argv[1:])
    new_argv = []
    for i in iterator:
        if i == "--log":
            log_lvl = next(iterator)
            assert not log_lvl.startswith("-"), "You have to specify a log-level if you use the arg!"
            assert log_lvl in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], "Log-level needs to be one of [DEBUG, INFO, WARNING, ERROR, CRITICAL]',"
        elif i == "--logfile":
            logfile = next(iterator)
            assert not logfile.startswith("-"), "You have to specify a logfile if you use the arg!"
        else:
            new_argv.append(i)
    sys.argv[1:] = new_argv
    return log_lvl, logfile


def setup_logging(loglevel=None, logfile=None):
    if loglevel is None:
        settings = importlib.import_module(os.environ["DJANGO_SETTINGS_MODULE"])
        loglevel = getattr(settings, "DEFAULT_LOG_LEVEL", DEFAULT_DEFAULT_LOG_LEVEL)
        if not hasattr(settings, "LOGLEVEL_WARN") or settings.LOGLEVEL_WARN:
            print(f"You didn't specify a log-level in the command-line args, so the DEFAULT_LOG_LEVEL from the settings: `{loglevel}` was taken. Note that important warnings may be hidden!")
            print(f"To specify another log-level, run `python manage.py {' '.join(sys.argv[1:])} --log LEVEL` with level being one of [DEBUG, INFO, WARNING, ERROR, CRITICAL].")
            if not getattr(settings, "DEFAULT_LOG_LEVEL", None):
                print(f"There is no DEFAULT_LOG_LEVEL in the settings, so I took the default default. Please add the line `DEFAULT_LOG_LEVEL='INFO'` to your settings.py at {settings.__file__}")
            else:
                print(f"To get rid of this message, you can add `LOGLEVEL_WARN = False` to your `settings.py` file.")
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    kwargs = {'level': numeric_level, 'format': '%(asctime)s %(levelname)-8s %(message)s',
              'datefmt': '%Y-%m-%d %H:%M:%S', 'filemode': 'w'}
    if logfile:
        kwargs['filename'] = logfile
    logging.basicConfig(**kwargs)

    tf_log_translator = {"INFO": "0", "DEBUG": "0", "WARNING": "2", "ERROR": "2", "CRITICAL": "3"} #https://stackoverflow.com/a/42121886/5122790
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = tf_log_translator[loglevel.upper()]
    os.environ['LOG_LEVEL'] = str(numeric_level)
    import tensorflow as tf
    tf.get_logger().setLevel(loglevel.upper())



if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
    setup_logging(*parse_command_line_args())
    sys.path.append(os.path.join(settings.BASE_DIR, "apps"))

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc

    try:
        execute_from_command_line(sys.argv)
        #TODO - remove this try/catch block as soon as everybody's transitioned
    except django.db.utils.ProgrammingError as e:
        if e.args[0].split("\n")[0] == 'relation "django_apscheduler_djangojob" does not exist':
            traceback.print_exc()
            logging.critical("The table `django_apscheduler_djangojob` does not exist! Make sure to execute migrations! Alternatively, on Unix, you can also run scripts/deployment/quickstart.sh!")
        else:
            raise e
    except RuntimeError as e:
        if e.args[0] == 'Model class django_apscheduler.models.DjangoJob doesn\'t declare an explicit app_label and isn\'t in an application in INSTALLED_APPS.':
            traceback.print_exc()
            logging.critical(f"You have to add `django_apscheduler` to the INSTALLED_APPS in your settings.py!")
            exit(-1)
        else:
            raise e
    except AttributeError as e:
        if e.args[0] == "'Settings' object has no attribute 'SCHEDULER_CONFIG'":
            traceback.print_exc()
            logging.critical(f"You have to add the SCHEDULER_CONFIG as it is in the settings_default.py to your your settings.py!")
            exit(-1)
        elif e.args[0] == "'Settings' object has no attribute 'SCHEDULER_AUTOSTART'":
            traceback.print_exc()
            logging.critical(f"You have to add the SCHEDULER_AUTOSTART as it is in the settings_default.py to your your settings.py!")
            exit(-1)
        else:
            raise e


