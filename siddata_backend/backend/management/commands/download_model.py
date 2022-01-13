from os.path import join, abspath

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from bert_app.model_downloader_seafile import get_read_account_data, SeafileModelSyncer, model_downloader_logger


class Command(BaseCommand):
    def handle(self, *args, **options):
        """"""
        model_downloader_logger.setLevel("INFO")
        localpath = abspath(join(settings.BASE_DIR, "..", "data")) #TODO specify localpath like this everywhere!
        account, password, server, repoid, repopath, modelversions = get_read_account_data()
        modelsyncer = SeafileModelSyncer(server, account, password, repoid, repopath)
        if modelsyncer.repo is not None:
            modelsyncer.download_modeldirs(localpath, modelversions, force_delete=False, fail_if_absent=True)
