import sys
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
    # def ready(self, *args, **kwargs):

    #see https://stackoverflow.com/a/65072601/5122790
    def ready(self, *args, **kwargs):
        if 'bert_app.apps.BertAppConfig' in settings.INSTALLED_APPS:
            from .bert_utils import BertPredictor
            self.predictor = BertPredictor()
            logger.info('BERT model was successfully initialized')
        else:
            self.predictor = None
            logger.info('BERT model was NOT successfully initialized. bert_app.apps.BertAppConfig not included in settings.py')

#    if os.environ.get('RUN_MAIN', None) != 'true':
#    else:
#        predictor = "Second BERTAppConfig-Loading intentionally removed, see https://stackoverflow.com/a/52430581/5122790"
#        logging.info(predictor)
#   Please do not do any environment variable checks, as they will not work on the apache server. -Jo
