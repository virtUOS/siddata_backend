# Model-Uploader

This is a model-uploader and -downloader class, that downloads custom data for your models (in the following the term *models* shall refer to this data) from a repository in Seafile on-demand. You can specify which versions of which models you need and download them with a custom command, whereas the backend itself only warns if new versions are available, keeping the old one. You can also manually upload new models.

## What's new

Version 2 is done! There is a ton of new functionality, so reading this README completely would probably a good idea.

#### New Settings

You'll need to add the following variables to your settings: 
* `SIDDATA_SEAFILE_REPO_BASEPATH` - v1 of ModelUpDown always took the root of the Seafile-Library as Base for the model-repository, which restricts it a lot, so now you can specify a directory as new base. Currently that is `backend_synced_models`.
* `SIDDATA_SEAFILE_MODEL_VERSIONS` - is a dictionary `{modelname: modelversion}`. While the old version of ModelUpDown just synced the entire `data` directory, v2 introduces the concepts of individual *models* (which are subdirectories of the `data` directory) and their *versions*. If you specify eg `SIDDATA_SEAFILE_MODEL_VERSIONS = {"Sidbert": 1}`, ModelUpDown will 
    * If you just run `manage.py runserver ...` check if the files in `data/Sidbert` are up-to-date with Version 1 of the `Sidbert` model on Seafile
    * If you run `manage.py download_model` download Version 1 of the `Sidbert` model from Seafile, if you don't have it yet
    * If you run `manage.py upload_model` upload the current contents of `data/Sidbert` to Seafile as Version 1 of the `Sidbert` model from Seafile, if there are any changes to it (also ensuring not to overwrite the remote version).

## Overview

### How does it work 

The ModelUpDownloader takes a directory on Seafile and treats it as remote-repository for Siddata-Models. You can specify multiple models in different version, and the ModelUpDown ensures that the correct version of each model is synced to the respective instance.

In the settings, you specify the models and versions you want to sync (see previous section), such that these versions are synced. On the Seafile-Repository, every Model and Version are mapped to subdirectories of your base-dir, such that you can also manually download version 1 from the `Sidbert` model at `SIDDATA_SEAFILE_REPO_BASEPATH/Sidbert/1`. On your local machine there are no sub-directories for model-versions, as you at every point in time are supposed to be using only one version of each model.

Within a concrete version of a model, it is ensured that all files are up-to-date. This is done by looking at the last-edited-time of each of the individual files. When either uploading, downloading or checking for models on the remote repository, the last-edited-times of all files that comprise this modelversion are compared. Whenever there are files that either have no correspondance on remote (in the case of upload) or local (in the case of download/checking), or the last-edited-time of one file is older than remote/local, the model is assumed to have changed - and only those files that really are new/updated are uploaded/downloaded. 

Conretely this means that every time you call eg. `upload_modeldirs`, it looks at the *last-modified-date* of all local files of all of your models and compares these to a remote `last_changes.txt`-file it downloads from Seafile for the demanded version of each of your models. All those files, for which the local *last-modified-date* is newer than the seafile-correspondence or for which there is no such correspondence will then be uploaded. Files that exist only on the remote and not locally (by name) are untouched, those of the same name will be overwritten. Further, it uploads the updated `last_changes.txt`, such that the next time this comparison is run the newer files are considered.

### Usecases

There are three main Usecases for the ModelUpDownLoader: 

#### Downloading a new model-version

Downloading a new model-version should only be done by explicit commands and not in productive operation, as it may be that a new version of the model is incompatible with the old version of the code still in operation.

To download a new version, you should specify the model and version in the *settings.py* as for example `SIDDATA_SEAFILE_MODEL_VERSIONS = {"Sidbert": 1}`, will then, on execution, download version 1 of the `Sidbert` model. The download-command can be invoked using the command  `python manage.py download_model`, and the code of that is at the location `siddata_backend/backend/management/commands/download_model.py`.

A minimal code to download models can look like this:

```python
from django.conf import settings
from bert_app.model_downloader_seafile import get_read_account_data, SeafileModelSyncer, model_downloader_logger
from os.path import abspath, join

model_downloader_logger.setLevel("INFO")
localpath = abspath(join(settings.BASE_DIR, "..", "data")) 
account, password, server, repoid, repopath, modelversions = get_read_account_data()
modelsyncer = SeafileModelSyncer(server, account, password, repoid, repopath)
if modelsyncer.repo is not None:
    modelsyncer.download_modeldirs(localpath, modelversions, force_delete=False, fail_if_absent=True)
```

For the `get_read_account_data()` method, see section **Other Information/Settings**.

The `download_modeldirs` method requires as arguments the path where the models should be downloaded (which is the data-dir set in your settings.py file), the modelversions as available as the variable `SIDDATA_SEAFILE_MODEL_VERSIONS`, as well as the following optinal arguments:
* `warn_other_direction` (bool, default=True): If True, warns if you have local files that are newer than their remote correspondance
* `force_delete` (bool, default=False): If True, the Downloader won't care if it deletes files that don't exist for this model-version (on a version-level).
* `fail_if_absent` (bool, default=False): If True, the Downloader will fail if the requested version of the requested model does not exist.

A few specialitys of model-downloading: 

* It may be the case that there are files in your local data-directory that would need to be deleted to create the model-version as requested. If that is the case, the model-downloader will check if these files are available as **any other version of that model**. If they are, the modeldownloader will just delete them and inform you that you can still restore the previous version by downloading the respective version from the repository. If the files are not available as any version (meaning the files are not backed up online), and `force_delete=False`, it will only download them after confirmation.

#### Uploading a new model-version

Is possible with the `manage.py upload_model` command, and the code is available at `python manage.py download_model`. To allow for uploading, you need an account that can write to the respective seafile-repository, which is why you'll need the following additional configurations in your settings.py:

```python
SIDDATA_SEAFILE_REPOWRITE_ACC = 'sid-sf-modw' #or even your personal account, if you have write-access to the repo
SIDDATA_SEAFILE_REPOWRITE_PASSWORD = '...'
```

Minimal code to download a model looks like this:

```python
import os

from bert_app.model_downloader_seafile import get_write_account_data, SeafileModelSyncer, model_downloader_logger
from django.conf import settings

model_downloader_logger.setLevel("INFO")
localpath = os.path.abspath(os.path.join(settings.BASE_DIR, "..", "data")) 
account, password, server, repoid, repopath, modelversions = get_write_account_data()
modelsyncer = SeafileModelSyncer(server, account, password, repoid, repopath)
if modelsyncer.repo is not None:
    print("Do you really want to upload the following:")
    for mname, mversion in modelversions.items():
        if mversion is not None:
            print(f"{mname} in version {mversion}")
    if input("? [y/n]").lower() == "y":
        modelsyncer.upload_modeldirs(localpath, modelversions, overwrite_version=False)
```

The `upload_modeldirs` method finds those models in the `modeldir` specified in `modelversions`. The following step depends on if you want to upload a new version or update an already uploaded one: If you want to upload a **new** version of that model, it will simply upload all those files to `model/version`, and if you only want to **update a version**, it will check if there are files for which the respective modelversion on Seafile is not up-to-date. If `overwrite_version=True`, it will then update those files that are updated. Afterwards, in all cases of successful upload, the `lastchanges.txt` file gets updated for every model, such that Seafile knows that all files are now up-do-date. It takes as arguments the `localpath` and the `modelversions` as in the settings, as well as the following optional arguments:

* `overwrite_version` (bool, default=False): If set to True, you can update already uploaded model-versions. If set to False, it will check if the uploaded version is still up-to-date, and raises a `NoOverwriteException` if it isn't.
* `check_otherversions` (bool, default=True): If set to True, it will check if the precise data of an individual model is already uploaded as some version of that model on the remote-respository, and will warn you and ask for confirmation if you still want to upload that model in that version.

#### Checking if the current model-version is still up-do-date (to be used in productive operation).

As constantly downloading updated versions of models can be disruptive in productive code, it makes sense to only issue a warning if new versions are available, such that the `download_model` command can manually be invoked. For that, you can use the `warn_newfiles` method of the Model-Syncer:

```python
import os
from bert_app.model_downloader_seafile import get_read_account_data, SeafileModelSyncer, model_downloader_logger
from django.conf import settings

localpath = os.path.abspath(os.path.join(settings.BASE_DIR, "..", "data"))
model_downloader_logger.setLevel(int(os.getenv("LOG_LEVEL", "WARNING")))
account, password, server, repoid, repopath, modelversions = get_read_account_data()
if any([i is not None for i in modelversions.values()]):
    modelsyncer = SeafileModelSyncer(server, account, password, repoid, repopath)
    modelsyncer.warn_newfiles(localpath, modelversions)
```


## Other information

### Settings


The `get_write_account_data`/`get_read_account_data` functions are convenience functions that get the respective username/password and all other data the downloader needs from either your settings.py or from environment-variables, with proper warnings if these are non-existant or false. For it to work. For them to work, you should make sure that the following settings are set:

```python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) #relative to the settings.py!
SIDDATA_SEAFILE_SERVER = 'https://myshare.uni-osnabrueck.de'
SIDDATA_SEAFILE_REPOID = '0b3948a7-9483-4e26-a7bb-a123496ddfcf' #for modelupdown v2 (subject to change!)
SIDDATA_SEAFILE_REPOREAD_ACC = 'sid-sf-modr' #or even your personal account, if you have write-access to the repo
SIDDATA_SEAFILE_REPOREAD_PASSWORD = '...'
SIDDATA_SEAFILE_REPO_BASEPATH = "backend_synced_models/" #subject to change
SIDDATA_SEAFILE_MODEL_VERSIONS = {"Sidbert": 1, "Other": 1} #subject to change
```


### Logging

The verbosity level of this module can be customized, as visualized in the example code. To customize it, you can import and set it like this:

```python
from bert_app.model_downloader_seafile import model_downloader_logger

model_downloader_logger.setLevel("INFO")
```

In those files where the uploading/donwloading is the main task, I think it's useful to set the verbosity level to `INFO`, whereas in other cases, I think it's best to set it to the default log-level you have anyway like this:
```python
model_downloader_logger.setLevel(int(os.getenv("LOG_LEVEL", "WARNING")))
```

## Requirements

### Python-requirements:

The basis for this is the `python-seafile` package from PyPI, however its current version (v0.1.0) has errors for binary files and doesn't allow to upload files larger than 2 GB, which is why instead a custom version from *https://github.com/cstenkamp/python-seafile.git is used*, which fixes these two issues. It can be installed in the currently needed version via pip using `pip install git+https://github.com/cstenkamp/python-seafile.git@v0.1.2#egg=python_seafile`. For that package work, you need make sure to have the `requests-toolbelt`-package or manually `pip install requests-toolbelt`.

Note that the version of python-seafile was bumped from version 0.1.1 to version 0.1.2 for version 2 of the model-updownloader. **As I screwed something up with the install-command for the old version, you may need to manually run `pip uninstall python-seafile` or `pip uninstall seafileapi` before installing this one!**

The python-package however only contains the bindings, and you also need to install `seafile-cli` on your system. The best source for how to do that on Linux is imo available at *https://download.seafile.com/published/seafile-user-manual/syncing_client/install_linux_client.md* (seriously, try this one first and don't believe other sources, it was a major struggle for me).

A short documentation for the `python-seafile`-package is available at *https://github.com/haiwen/python-seafile/blob/master/doc.md*.

#### How to get the passwords

Note that **passwords should never be shared via git or non-encrypted messengers**, so unfortunately the process of getting them is a bit more tedious. At https://myshare.uni-osnabrueck.de/library/124ddb62-7339-4659-a5fb-b626f5702787/siddata/Projektmanagement/Berechtigungsmanagement, you'll find several `.kbdx`-Files. These are KeePass-files. [KeePass](https://keepass.info/) is a password-manager, and these files contain the account-data in an enctrypted manner. To get them, you first need to download KeePass itself, for Windows that is possible at https://keepass.info/download.html, while for Linux I recommend https://keepassxc.org/download/#linux. After having installed KeePass, download the file `SIDDATA-team-shared-AI-chain.kbdx` from the given link and open it using KeePass. Now you'll need an additional password to be able to view the actual account-passwords, which can unfortunately also not be shared over Slack. Current ways are using an S/MIME encrypted Email to Sebastian Osada (see https://www.rz.uni-osnabrueck.de/dienste/unios_ca/antrag_benutzer.html for how to get such a certificate easily for your @uos-mail-account), or by calling Sebastian Osada personally. Unfortunately, this is the only secure way to share passwords and account-data, so please make sure to follow these guidelines and not to accidentially upload/write your passwords somewhere unsafe.

**Luckily**, the new place for the files is at a repository that you should be able to access with your normal **rz-login**-credentials. If that is the case, you can simply use your university-email and password for the Model-UpDownloader. Please make sure however not to store your password unencryptedly in textual files like the `settings.py`, but use environment-variables instead.

#### Setting Env-Vars

If you decide for the env-vars-way, you first need to set these. Good resources on how to set environment-variables are:
 * Windows (`cmd`/`powershell`/`anaconda prompt`): https://www.computerhope.com/issues/ch000549.htm
 * Linux (`terminal`): https://www.serverlab.ca/tutorials/linux/administration-linux/how-to-set-environment-variables-in-linux/
 * PyCharm (both Win & Linux): https://stackoverflow.com/questions/42708389/how-to-set-environment-variables-in-pycharm