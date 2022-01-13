from os.path import join, isdir, isfile, abspath, dirname, splitext
import importlib
import os

from django.core.management.base import BaseCommand, CommandError

from bert_app.model_downloader_seafile import get_write_account_data, SeafileModelSyncer, model_downloader_logger


class Command(BaseCommand):
    def handle(self, *args, **options):
        """"""
        model_downloader_logger.setLevel("INFO")
        settings = importlib.import_module(os.environ["DJANGO_SETTINGS_MODULE"])
        localpath = abspath(join(settings.BASE_DIR, "..", "data")) #TODO specify localpath like this everywhere!
        account, password, server, repoid, repopath, modelversions = get_write_account_data()
        modelsyncer = SeafileModelSyncer(server, account, password, repoid, repopath)
        if modelsyncer.repo is not None:
            print("Do you really want to upload the following:")
            for mname, mversion in modelversions.items():
                if mversion is not None:
                    print(f"{mname} in version {mversion}")
            if input("? [y/n]").lower() == "y":
                modelsyncer.upload_modeldirs(localpath, modelversions, overwrite_version=False)