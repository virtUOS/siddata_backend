import sys
import os, logging
from django.apps import AppConfig
from django.conf import settings

is_manage_py = any(arg.casefold().endswith("manage.py") for arg in sys.argv)
is_runserver = any(arg.casefold() == "runserver" for arg in sys.argv)

class BackendConfig(AppConfig):
    name = 'backend'

    def ready(self):
        """
        schedule tasks using django_apscheduler. We're doing this as part of the BackendAppConfig, as for example done here:
        https://medium.com/@mrgrantanderson/replacing-cron-and-running-background-tasks-in-django-using-apscheduler-and-django-apscheduler-d562646c062e
        however this may lead to problems, see https://github.com/jcass77/django-apscheduler#quick-start.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        if "LOG_LEVEL" in os.environ:
            self.logger.setLevel(int(os.environ["LOG_LEVEL"]))

        if not str(os.environ.get("DJANGO_DRYRUN")).lower() == "true":
            #DJANGO_DRYRUN is set in manage.py:setup_django_dry for things that need to set up django to get to its database and settings, but not actually run the backend
            if not is_manage_py:
                if settings.DEBUG:
                    self.logger.critical("You seem to be running productively with the settings.DEBUG flag enabled!")
            if (is_manage_py and is_runserver):
                if not "--noreload" in sys.argv:
                    self.logger.warning("It seems like you're running the backend non-productively and are not using `--noreload`. The backend will load twice as fast if you include that as command-line-argument!")
                #warn if there are settings in the settings_default that you don't have in your settings
                sys.path.append(os.path.join(settings.BASE_DIR, "..", "scripts", "deployment"))
                import compare_settings
                compare_settings.compare_settings(print_fn=self.logger.warning, ignore_diffs={"ALLOWED_HOSTS", "STATIC_ROOT", "LOGLEVEL_WARN", "DEFAULT_LOG_LEVEL", "QUIET_SCHEDULER"})
                import check_requirements
                check_requirements.main()
            if (is_manage_py and is_runserver) or (not is_manage_py):
                from scheduled_tasks import scheduler
                if settings.SCHEDULER_AUTOSTART:
                    scheduler.start()