import logging

from django.apps import AppConfig
from django.conf import settings
import os

logger = logging.getLogger('bert_app.apps.BertAppConfig')
if "LOG_LEVEL" in os.environ:
    logger.setLevel(int(os.environ["LOG_LEVEL"]))
    logging.getLogger("asyncio").setLevel(int(os.environ["LOG_LEVEL"]))

class BertAppConfig(AppConfig):
    name = 'bert_app'

    #see https://stackoverflow.com/a/65072601/5122790
    def ready(self, *args, **kwargs):
        if 'bert_app.apps.BertAppConfig' in settings.INSTALLED_APPS:
            from .bert_utils import SidBERT
            try:
                self.predictor = SidBERT()
                logging.info('SidBERT model was successfully initialized.')
            except ValueError:
                logging.error('Error in instantiating SidBERT model, files may be missing!')
        else:
            self.predictor = None
            logger.info('BERT model was NOT successfully initialized. bert_app.apps.BertAppConfig not included in settings.py')

