import sys
import logging

from django.apps import AppConfig
from django.conf import settings
import os

is_manage_py = any(arg.casefold().endswith("manage.py") for arg in sys.argv)
is_runserver = any(arg.casefold() == "runserver" for arg in sys.argv)

logger = logging.getLogger('bert_app.apps.CollaborativeFilteringApp')
if "LOG_LEVEL" in os.environ:
    logger.setLevel(int(os.environ["LOG_LEVEL"]))
    logging.getLogger("asyncio").setLevel(int(os.environ["LOG_LEVEL"]))

class CollaborativeFilteringAppConfig(AppConfig):
    name = 'collaborative_filtering_app'
    # def ready(self, *args, **kwargs):

    #see https://stackoverflow.com/a/65072601/5122790
    def ready(self, *args, **kwargs):
        if (is_manage_py and is_runserver) or (not is_manage_py):
            if 'collaborative_filtering_app.apps.CollaborativeFilteringAppConfig' in settings.INSTALLED_APPS:
                logger.info('Collaborative Filtering App was successfully initialized')
            else:
                self.predictor = None
                logger.info('Collaborative Filtering App was NOT successfully initialized. collaborative_filtering_app.apps.CollaborativeFilteringAppConfig not included in settings.py')
