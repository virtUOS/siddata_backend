from os import listdir
import os
from os.path import join, isdir, isfile, abspath, dirname, splitext, getmtime, basename
import time
from datetime import datetime, timezone
from functools import partial, partialmethod
from collections import namedtuple
import warnings, traceback, sys
import logging
from functools import wraps
import io

try:
    import python_seafile
except ModuleNotFoundError:
    print("!!!!!!!!!!!!!!!!", file=sys.stderr)
    print("Cannot find python_seafile, make sure to re-run `pip install -r requirements.txt`!", file=sys.stderr)
    exit(1)
#https://github.com/haiwen/python-seafile/blob/master/doc.md
#how to install seafile-cli on your system: see https://download.seafile.com/published/seafile-user-manual/syncing_client/install_linux_client.md
#on pypi seafileapi is broken (v0.1.0), and even the original repo has an error with binary files -> take git+https://github.com/cstenkamp/python-seafile.git@v0.1.2#egg=python_seafile
#docs @ https://github.com/haiwen/python-seafile/blob/master/doc.md

from siddata_backend import settings

DOCUMENTATIONLINK = 'https://git.siddata.de/uos/siddata_backend/src/branch/develop/doc/model_updownloader.md'

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)
if "LOG_LEVEL" in os.environ:
    logger.setLevel(int(os.environ["LOG_LEVEL"]))
model_downloader_logger = logger #another reference, to be imported from outside, to set the level


#TODO:
# * have the possibility to hash files instead of using last-changed-date
# * be able to specify "latest" instead of a version-number, which picks the highest number
# * For all files in version n of a model in seafile, check if the file is equal to version n-1, and if so, don't store it on seafile to save storage!
# * Warnen wenn eine neuere Version auf Seafile verfügbar ist, auch wenn ich sie nicht demanded habe
# * Use Profiler to check if runtime improvements are possible
# * commit-hash und hostname mitschreiben in das last_changes beim hochladen (am besten sogar pro-file)
# * beim runterladen warnen wenn im remote-ordner dateien existieren die nicht in last_changes stehen
# * method to clear those files of MODELNAME,MODELVERSION remotely that are not in the last_changes.txt (und drauf hinweisen dass man das runnen kann bei der warnung " There are remote-files that you didn't up..."
# * befehl zum version auf seafile löschen
# * add support for completely syncing files (also deleting directories that are not needed etc)
# * ne klare trennung zwischen sync und nicht-sync haben (in ersterem Fall löscht er remote alles was lokal nicht vorkommt, inklusive Ordnern (was er jetzt halt noch nicht macht)), in zweiterem fall archiviert er basically.


####################################################################################################

flatten = lambda l: [item for sublist in l for item in sublist]

def silence_requests(fn):
    @wraps(fn)
    def wrapped(*args, requests_loglevel=logging.WARNING, **kwargs):
        if requests_loglevel is not None:
            level_bkp = logging.getLogger("requests").level
            prop_bkp = logging.getLogger("urllib3").propagate
            logging.getLogger("urllib3").propagate = False
            logging.getLogger("requests").setLevel(requests_loglevel)
            logging.getLogger("urllib3").setLevel(requests_loglevel)
            res = fn(*args, **kwargs)
            logging.getLogger("requests").setLevel(level_bkp)
            logging.getLogger("urllib3").setLevel(level_bkp)
            logging.getLogger("urllib3").propagate = prop_bkp
            return res
        return fn(*args, **kwargs)
    return wrapped

SeafileModelDownloaderAttrs = namedtuple('SeafileModelDownloaderAttrs', 'account password server repoid repopath modelversions')


def get_readwrite_account_data(accvarname, pwvarname, servervarname, repoidvarname, repopathvarname, versionsvarname):
    res = []
    for varname in [accvarname, pwvarname, servervarname, repoidvarname, repopathvarname, versionsvarname]:
        if os.environ.get(varname):
            res.append(os.environ[varname])
            if hasattr(settings, varname):
                warnings.warn(f"!! Note that the variable '{varname}' is specified as environment-variable as well as the settings.py! The environment-variable is taken !!")
        elif hasattr(settings, varname):
            res.append(getattr(settings, varname))
        else:
            raise ValueError(f"The variable '{varname}' was not found! As specified in {DOCUMENTATIONLINK}, please add it to your 'settings.py' at '{abspath(settings.__file__)}' (note that env-vars precede over vars in settings).")
    return SeafileModelDownloaderAttrs(*res)

get_read_account_data = partial(get_readwrite_account_data, 'SIDDATA_SEAFILE_REPOREAD_ACC', 'SIDDATA_SEAFILE_REPOREAD_PASSWORD', 'SIDDATA_SEAFILE_SERVER', 'SIDDATA_SEAFILE_REPOID', 'SIDDATA_SEAFILE_REPO_BASEPATH', 'SIDDATA_SEAFILE_MODEL_VERSIONS')
get_write_account_data = partial(get_readwrite_account_data, 'SIDDATA_SEAFILE_REPOWRITE_ACC', 'SIDDATA_SEAFILE_REPOWRITE_PASSWORD', 'SIDDATA_SEAFILE_SERVER', 'SIDDATA_SEAFILE_REPOID', 'SIDDATA_SEAFILE_REPO_BASEPATH', 'SIDDATA_SEAFILE_MODEL_VERSIONS')

####################################################################################################

class WrongPasswordException(Exception):
    ...

class NoOverwriteException(Exception):
    ...

class ModelNotExistantError(Exception):
    ...

####################################################################################################

class SeafileModelSyncer():
    '''This is a model-uploader and -downloader class, that downloads the model from seafile if it detects any new changes.
    How does it work: You basically only need the `upload_modeldirs`, `download_modeldirs` and `warn_newfiles` methods.
    Upload:
        Every time you call `upload_modeldirs`, it checks if the remote correspondances of the versions of your models as
        specified in the settings are up-to-date with your local model-directories by comparing their last-modified-date
        with those last-modified-dates on the remote server. All those files that are newer than their remote correspondance
        (or all files, if you are uploading a new version of a model) are then uploaded. Files that exist only on the remote
        and not locally (by name) are untouched, those of the same name will be overwritten. For more info, take a look at the
        `doc/model_updownloader.md` file.
    Download:
        It compares the last-modified-dates for the remote correspondances of the version of the models as requested in your
        settings, downloading those ones that are updated compared to your local data-files. Note that locally you can always
        have only one version of each model at any given time. For all those files which either don't exist in your local tree
        or are newer in the respective version of the remote, it will download them and set the last-modified-date accordingly.
        You can also use the `warn_newfiles` method, which will only warn if there are updates to the versions instead of downloading
        them right away, to be used in productive environments.
    '''
    LASTCHANGED_NAME = 'last_changes.txt'
    REMOTE_SEP = '/'


    @silence_requests
    def __init__(self, remoteurl, accountname, accountpassword, remoterepo, repopath):
        self.remoteurl = remoteurl
        self.accountname = accountname
        self.accountpassword = accountpassword
        self.remoterepo = remoterepo
        self.repopath = repopath if repopath.startswith(self.REMOTE_SEP) else self.REMOTE_SEP+repopath
        if not self.repopath.endswith(self.REMOTE_SEP): self.repopath = self.repopath+self.REMOTE_SEP

        try:
            self.client = python_seafile.connect(remoteurl, accountname, accountpassword)
        except python_seafile.exceptions.ClientHttpError as e:
            if hasattr(e, "code") and e.code == 502:
                traceback.print_exc()
                print("Got an Error 502 from Seafile, is it possible that Seafile is down? Check https://myshare.uni-osnabrueck.de/, and if it's down, have patience!", file=sys.stderr)
                raise
            else:
                # print('Original Error:', '\n', file=sys.stderr)
                # traceback.print_exc()
                raise WrongPasswordException(f"You have a wrong username/password-combination. Note that (1) Env-vars precede over what you specified in 'settings.py' and (2) The caveats as listed in {DOCUMENTATIONLINK}.")

        self.repo = self.client.repos.get_repo(remoterepo)
        try:
            self.root = self.repo.get_dir(self.repopath)
        except python_seafile.exceptions.DoesNotExist as e:
            logging.error(f"Seafile-Syncer: The directory {self.repopath} does not exist on your remote-repo {settings.SIDDATA_SEAFILE_REPOID}. Are you sure it is the correct one?")
            logging.error("Please update the setting `settings.SIDDATA_SEAFILE_REPOID` to `b20a34c4-69cf-4e7c-a3f2-8f597095cea5`, in case you didn't update this setting since changing from Seafile-Syncer v1\n")
            time.sleep(4)
            self.repo = None
        else:
            self.can_upload = self._test_if_upload()
            self._write_remote_readme()


    def warn_newfiles(self, localpath, modelversions):
        if self.repo is not None:
            to_download, _ = self._check_newfiles_modeldir(localpath, modelversions, warn_other_direction=False, show_warns=True)
            if flatten([i["files"] for i in to_download.values()]):
                logger.error("There are new model-files that you may have to download! Run `manage.py download_model` to do that!")
                time.sleep(4)


    @silence_requests
    def upload_modeldirs(self, modeldir, modelversions, overwrite_version=False, check_otherversions=True):
        '''High-Level function to sync a complete model-dir (all components) from local directory to Seafile.
           Finds those models in the `modeldir` specified in `modelversions`, then checks if there are files for which
           the respective modelversion on Seafile is not up-to-date. If a new modelversion is specified, it uploads the
           files anyway, and if a current version would need to be overwritten, it only does so if `overwrite_version`
           (else raises a `NoOverwriteException`). Afterwards overwrites the `lastchanges.txt` file for every model,
           such that Seafile knows that all files are now up-do-date.
           if check_otherversions, it will check if that dataset is already uploaded in another version and will warn if so.'''
        assert self.can_upload, f"The account you're using does not have the permissions to upload to this server/directory! Maybe you need to use another account, see {DOCUMENTATIONLINK}"
        logger.info('SeafileModelSyncer checking if there are changes in models that can be uploaded...')
        to_upload = self._get_new_files_to_upload(modeldir, modelversions)
        if check_otherversions:
            for key, val in to_upload.copy().items():
                uploadedversions = self._compare_local_allpossibleremote(key, val["from_lasttimes"])
                if uploadedversions and str(uploadedversions) != str(val["version"]):
                    if input(f"You are about to upload the model `{key}` to Seafile as version {val['version']}, however the exact files you are about to upload are already "
                             f"online as version {uploadedversions}. Do you want to additionally upload under the new version number anyway? [y/n]").lower() != "y":
                        del to_upload[key]

        upload_num = {key: (len(val['files']), val['version']) for key, val in to_upload.items() if val["files"]}
        upload_str = ", ".join(f"{val[0]} files for {key} as version {val[1]}" for key, val in upload_num.items())
        for nonexistant_model in {key for key, val in to_upload.items() if not val["from_lasttimes"]}:
            logger.error(f"You want to upload the model {nonexistant_model} to the Seafile-Repo, but you have no such model in your data-directory!")
        if ([val[0] for val in upload_num.values()]):
            logger.info(f"Have to upload: {upload_str}")
            self._check_and_rename_files(modeldir, to_upload)
            for componentname, content in to_upload.items():
                if len(content["files"]) > 0:
                    self._upload_local_files(modeldir, componentname, content, overwrite_version=overwrite_version, write_lastchanged=True)
                    folder = self.repo.get_dir(join(self.root.path, componentname, str(content["version"])))
                    remotes = self._get_all_remotefiles_in_dir(folder)
                    too_much_files = set(remotes) - set([self.LASTCHANGED_NAME]) - set(content["from_lasttimes"].keys())
                    if too_much_files:
                        logger.critical("There are remote-files that you didn't upload in the same directory this version was uploaded! They will not be downloaded when this version is requested.")
                        logger.critical(f"The files are: {too_much_files}")
                    not_uploaded = set(content["from_lasttimes"].keys()) - set(remotes)
                    if not_uploaded:
                        print("DEBUG")
                    print(f"Done uploading {componentname}.")
        else:
            logger.info(f"No changes to upload!")


    @silence_requests
    def download_modeldirs(self, modeldir, modelversions, warn_other_direction=True, force_delete=False, fail_if_absent=False):
        '''High-Level function to sync a complete model-dir from Seafile to a local directory.
           Checks first which files need to be downloadTed, and only updates those.'''
        logger.info("You requested: "+", ".join(f"Version {version} of model `{model}`" for model, version in modelversions.items()))
        to_download, _ = self._check_newfiles_modeldir(modeldir, modelversions, warn_other_direction, fail_if_absent=fail_if_absent)
        for modelname, content in to_download.items():
            if len(content["files"]) > 0:
                mdir = join(modeldir, modelname)
                os.makedirs(mdir, exist_ok=True)
                #TODO: how do we deal with deleting local files?
                #  --> check if the local changestxt corresponds to ANY remote version
                did_download = self._download_remote_files(mdir, modelname, content, force_delete=force_delete)
                if not did_download:
                    print()
                local_files = set(self._get_all_local_files(join(modeldir, modelname), flat=True))
                assert set(to_download[modelname]["from_lasttimes"].keys()) == local_files

    ########################################################################################################################
    ########################################################################################################################
    #private methods

    def _write_remote_readme(self):
        CONTENT = f"""This directory is used as model-repository for the Siddata-Backend. 
**PLEASE DO NOT DELETE OR EDIT ANY FILES MANUALLY UNLESS YOU KNOW WHAT YOU ARE DOING!!**

This directory contains a subdirectory for every model that can be imported by the SeafileModelSyncer, and of each of those models,
it can contain multiple versions (stored as subdirectories). 

Manually editing the contents of the directories will lead to errors
unless `{self.LASTCHANGED_NAME}` is edited as well, which you should only do if you know what you're doing! All changes to this directory
and all its subdirectories should only be done by the SeafileModelSyncer and its methods `download_modeldirs` and `upload_modeldirs`. 

You can find its documentation at {DOCUMENTATIONLINK}"""
        if self.can_upload:
            try:
                self.repo.get_file(join(self.root.path, "README.md"))
            except python_seafile.exceptions.DoesNotExist:
                fh = io.StringIO(CONTENT)
                self.root.upload(fh, "README.md")

    def _test_if_upload(self):
        # logging.info(self.repo.is_readonly()) / logging.info(self.repo.perm) #these don't tell the truth...
        url = f'{self.repo.client.server}/api2/repos/{self.repo.id}/dir/'
        perms = list(set([i['permission'] for i in self.repo.client._send_request('GET', url).json()]))
        if len(perms) == 1 and perms[0] == 'rw':
            return True
        return False

    def _get_all_remotefiles_in_dir(self, folder):
        cont = []
        for i in folder.ls(force_refresh=True):
            if isinstance(i, python_seafile.files.SeafDir):
                cont.extend([join(i.name, j) for j in self._get_all_remotefiles_in_dir(i)])
            else:
                cont.append(i.name)
        return cont

    def _check_and_rename_files(self, modeldir, filedict):
        """Myshare/Seafile doesn't like German Umlaute etc, so to make sure no UTF-Encoding-errors occurs this renames
        the files to ensure consistency."""
        for key in filedict:
            for num, fname in enumerate(filedict[key]):
                if not all(ord(char) < 128 for char in fname):
                    newname = fname.replace('ö', 'oe').replace('Ö', 'Oe').replace('Ü', 'Üe').replace('ü', 'ue').replace('ä', 'ae').replace('Ä', 'Ae').replace('ß', 'ss')
                    newname = ''.join([char for char in newname if ord(char) < 128])
                    os.rename(join(modeldir, fname), join(modeldir, newname))
                    logger.info(f"Renamed file {fname} to {newname}")
                    filedict[key][num] = newname
        return None #changes in-place


    @silence_requests
    def _check_newfiles_modeldir(self, modeldir, modelversions, warn_other_direction=True, show_warns=True, fail_if_absent=False):
        '''Function to test-sync a complete model-dir from Seafile to a local directory.
           Checks if there are files that need to be downloaded, and only updates those.'''
        logger.info('SeafileModelSyncer checking for new updates on the model-repository on Seafile...')
        to_download = self._get_new_files_to_download(modeldir, modelversions)
        for name, val in to_download.items():
            if len(val["files"]) > 0 and show_warns:
                logger.info(f'There are new files for model `{name}` on remote which I want to download: {val["files"]}')
            if not val["from_lasttimes"]:
                err = f'You requested version {val["version"]} for model `{name}`, but there is no such version for that model!'
                if fail_if_absent:
                    raise ModelNotExistantError(err)
                logging.critical(err)
                time.sleep(4)
        if warn_other_direction:
            to_upload = self._get_new_files_to_upload(modeldir, modelversions)
            for name, val in to_upload.items():
                existing = set(k for k in val["to_lasttimes"].keys() if k in val["files"])
                if len(existing) > 0 and show_warns:
                    logger.warning(f'Some of your files for model `{name}` are newer than their remote correspondance: {existing}')
                if len(set(val["files"])-existing) > 0 and show_warns:
                    logger.warning(f'You have files for model `{name}` that have no remote correspondance: {set(val["files"])-existing}')
        else:
            to_upload = None
        if sum(len(val["files"]) for val in to_download.values()) == 0:
            logger.info(f'No updates.')
        return to_download, to_upload


    def _get_all_local_files(self, base_path, abpath=False, flat=False, ignore_lastchanges=True):
        '''gets all local files, starting from base_path.
         If flat==True:
           result is a recursive dictionary of dictionaries, where every
           subdirectory is represented as another dictionary (name: {content}) and every file is listed under the
           dictionaries "." attribute, like this:
           root_dir = {"sub_dir_1": {"sub_sub_dir": {".": ["file1", "file2"]}, ".": ["file_in_subdir1"]}, "sub_dir_2": {}}
         Otherwise, the result is a non-nested list with all filenames, ignoring empty paths. If abpath is not set,
           the list of filenames contains paths starting from root, otherwise absolute paths, like this:
           res = ["sub_dir_1/sub_sub_dir/file1", "sub_dir_1/sub_sub_dir/file2", "sub_dir_1/file_in_subdir1"]
        '''
        def get_local_dir_recur(base_path, lodir, ldir, abpath=False, flat=False):
            for i in sorted(listdir(join(base_path, lodir))):
                if isdir(join(base_path, lodir, i)):
                    if flat:
                        get_local_dir_recur(base_path, join(lodir, i), ldir, abpath, flat)
                    else:
                        ldir[i] = get_local_dir_recur(base_path, join(lodir, i), {}, abpath, flat)
                else:
                    if flat:
                        ldir.append(join(lodir, i))
                    else:
                        if '.' in ldir: ldir['.'].append(join(lodir, i) if abpath else i)
                        else: ldir['.'] = [join(lodir, i) if abpath else i]
            return ldir
        all_locals = [] if flat else {}
        if not isdir(base_path): return all_locals
        get_local_dir_recur(base_path, '', all_locals, abpath, flat)
        all_locals = [i.replace(os.sep, '/') for i in all_locals] #windows-fixes
        for fname in all_locals:
            if not all(ord(char) < 128 for char in fname):
                wrongs = [i for i in fname if ord(i) >= 128]
                raise UnicodeError(f'!! One of your local files ({fname}) has a non-ASCII-characters in it (namely {",".join(wrongs)}). If you are uploading model-files, please rename the file such that no such signs are there anymore. If you are downloading, you can just delete that file.')
        if ignore_lastchanges:
            return [i for i in all_locals if i != self.LASTCHANGED_NAME]
        return all_locals


    def _create_lastchanges(self, for_path, write_out=False):
        '''Creates a string (and saves it as last_changes.txt) which maps the local files to their last-change-date. This is used
           to determine which files need to be uploaded. returns string and filename'''
        files = self._get_all_local_files(for_path, True, True)
        last_changed = {i: datetime.fromtimestamp(time.mktime(time.gmtime(getmtime(join(for_path, i))))) for i in files}
        #TODO attention, time.mktime makes local time out of that!
        assert not any(":" in key for key in last_changed.keys()), 'Colons in Filenames are forbidden!'
        if write_out:
            self._write_lastchangedtxt(last_changed, for_path)
        return last_changed


    def _write_lastchangedtxt(self, last_changed, for_path):
        #time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(getmtime(join(for_path, i)))) for i in files
        txt = "\n".join([f'{key}: {val}' for key, val in sorted(last_changed.items(), key=lambda x: x[0]) if key != self.LASTCHANGED_NAME])
        self._local_write(join(for_path, self.LASTCHANGED_NAME), txt)
        return join(for_path, self.LASTCHANGED_NAME)


    def _local_write(selff, fname, txt):
        try:
            with open(fname, 'w') as ofile:
                ofile.write(txt)
        except UnicodeEncodeError as e:
            warnings.warn(f'There is a UnicodeDecodeError - I cannot write the following: \n {txt}')
            raise e


    def _get_remote_last_changed_txt(self, component, modelversion):
        '''gets the last_changes.txt file from the remote-server. used in _get_new_files_to_updown_load()'''
        try:
            return self.repo.get_file(join(self.repopath, component, str(modelversion), self.LASTCHANGED_NAME)).get_content().decode('UTF-8')
        except python_seafile.exceptions.DoesNotExist:
            return ''


    def _get_new_files_to_updown_load(self, base_path, modelversions, direction='up'):
        '''Compares the local last_changes.txt to the remote one and returns a list of all filepaths, for which either the local one is newer than the uploaded one
           or there isn't even a remote correspondance.'''
        #TODO So far, I don't delete files that are on `to` but not on `from_` -> no syncing!
        assert direction in ['up', 'down']
        all_toupdowns = {}
        # for subdir in os.listdir(base_path):
        #     if not isdir(join(base_path, subdir)):
        #         continue
        #     if not subdir in modelversions:
        #         continue
        for subdir in modelversions.keys():
            if modelversions[subdir] is None:
                continue
            to_updown = []
            from_ = self._create_lastchanges(join(base_path, subdir))
            to = make_dict(self._get_remote_last_changed_txt(subdir, modelversions[subdir]))
            if direction == 'down':
                if not subdir in [i.name for i in self.repo.get_dir(self.repopath).entries if i.isdir]:
                    logger.critical(f"You are trying to get the model `{subdir}`, but a model of that name does not exist on the Seafile-Repository!")
                    time.sleep(4)
                tmp = from_
                from_ = to
                to = tmp
            for key, from_time in from_.items():
                to_time = to.get(key, datetime.strptime("2000-01-01 00:00:00", "%Y-%m-%d %H:%M:%S"))
                if to_time < from_time:
                    to_updown.append(key)
            all_toupdowns[subdir] = {"version": modelversions[subdir], "files": to_updown, "from_lasttimes": from_, "to_lasttimes": to}
        return all_toupdowns

    _get_new_files_to_upload = partialmethod(_get_new_files_to_updown_load, direction='up')
    _get_new_files_to_download = partialmethod(_get_new_files_to_updown_load, direction='down')

    def _upload_local_files(self, base_dir, componentname, content, overwrite_version=False, write_lastchanged=True):
        '''uploads all files that are listed in to_upload from the base_dir to the remote root.'''
        version = str(content["version"])
        # basepath = join(componentname, str(content["version"]))
        if componentname in [i.name for i in self.root.ls(force_refresh=True) if isinstance(i, python_seafile.files.SeafDir)]:
            r_basedir = self.repo.get_dir(join(self.root.path, componentname))
        else:
            r_basedir = self.root.mkdir(componentname)
        if version in [i.name for i in r_basedir.ls(force_refresh=True) if isinstance(i, python_seafile.files.SeafDir)]:
            if overwrite_version:
                r_basedir = self.repo.get_dir(join(r_basedir.path, version))
                logger.warning(f"Version {version} for {componentname} already exists! Overwriting...")
            else:
                raise NoOverwriteException(f"There exists already a version {version} of model `{componentname}` and `overwrite_version` is False!")
        else:
            r_basedir = r_basedir.mkdir(version)

        for fname in content["files"]:
            file = join(base_dir, componentname, fname)
            rpath = dirname(fname)
            curr_dir = r_basedir
            for n, pathpart in enumerate(rpath.split(self.REMOTE_SEP)):
                curr_ls = [i.name for i in curr_dir.ls(force_refresh=True) if isinstance(i, python_seafile.files.SeafDir)]
                if pathpart in curr_ls:
                    curr_dir = self.repo.get_dir(join(r_basedir.path, self.REMOTE_SEP.join(rpath.split(self.REMOTE_SEP)[:n+1])))
                else:
                    curr_dir = curr_dir.mkdir(pathpart)
            if overwrite_version:
                if any(curr_dir.path+self.REMOTE_SEP+i.name == r_basedir.path+self.REMOTE_SEP+fname for i in curr_dir.ls(force_refresh=True)):
                    resp = self.repo.get_file(r_basedir.path+self.REMOTE_SEP+fname).delete()
                    assert resp.status_code == 200
            logger.debug(f'Currently uploading {componentname}: {fname}')
            rmtfile = curr_dir.upload_local_file(file)
        #now save lastchanges remotely
        if write_lastchanged:
            lcfile = self._write_lastchangedtxt(content["from_lasttimes"], join(base_dir, componentname))
            lcdir = join(self.repopath, componentname, version)
            if self.LASTCHANGED_NAME in [i.name for i in self.repo.get_dir(lcdir).ls(force_refresh=True)]:
                resp = self.repo.get_file(join(lcdir, self.LASTCHANGED_NAME)).delete()
                assert resp.status_code == 200
            rmtlastchfile = self.repo.get_dir(lcdir).upload_local_file(lcfile)
            os.remove(lcfile)


    def _compare_local_allpossibleremote(self, modelname, local_lasttimes):
        """takes a local_lasttimes and modelname, and compares all remote versions of that model to the local ones.
        Returns the version if a remote version contains all of the local files with correct lasstimes, and None otherwise.
        If the result is not None that means the local versions are part of some version of the model as uploaded."""
        if modelname not in [i.name for i in self.root.entries if i.isdir]:
            return None
        for remote_vdir in self.repo.get_dir(join(self.root.path, modelname)).entries:
            if isinstance(remote_vdir, python_seafile.files.SeafDir):
                rmt_lasttimes = make_dict(self._get_remote_last_changed_txt(modelname, remote_vdir.name))
                rmt_subset = {key: val for key, val in rmt_lasttimes.items() if key in local_lasttimes.keys()}
                if rmt_subset == local_lasttimes:
                    return remote_vdir.name
        return None


    def _download_remote_files(self, modeldir, modelname, content, force_delete=False, overwrite_old=True):
        '''downloads all files of modelname from the remote root to the base_dir.
        if force_delete==True, it won't care if it deletes files that don't exist for this model-version (on a version-level)
        if overwrite_old=True, it will overwrite individual files (more fine granular!) with their remote correspondance, else it will add numbers to doubling filenames'''
        assert content["to_lasttimes"] == self._create_lastchanges(modeldir)
        assert content["from_lasttimes"] == make_dict(self._get_remote_last_changed_txt(modelname, content["version"]))
        to_del_files = set(content["to_lasttimes"].keys())- set(content["from_lasttimes"].keys())
        if to_del_files:
            remote_version = self._compare_local_allpossibleremote(modelname, content["to_lasttimes"])
            if remote_version is not None:
                logger.warning(f"There are local files of model `{modelname}` that will be deleted to create the model-version as requested: {to_del_files}")
                logger.warning(f"The remote files are available remotely in version {remote_version} of model `{modelname}`, so I will just remove them locally - you know now how to recover them from remote!")
            else:
                logger.error(f"There are files that would need to be deleted to create the model-version as requested, and these files are not backed up online: {to_del_files}")
                if not force_delete and input("Do you want REALLY to remove these files to download the new version? [y/n]").lower() != "y":
                    return False
            for i in to_del_files:
                os.remove(join(modeldir, i))
        for fname in content["files"]:
            orig_fname = fname
            file = join(modeldir, fname)
            # corresp_dir = repo.get_dir(REMOTE_SEP+dirname(fname))
            if not overwrite_old:
                file = add_number_until_unique(file)
                fname = join(dirname(fname), basename(file))
            if isfile(file):
                assert content["from_lasttimes"][fname] >= content["to_lasttimes"][fname]
                logger.debug(f'Currently downloading {fname} (overwriting local)')
            else:
                logger.debug(f'Currently downloading {fname}')
            if not isdir(dirname(file)):
                os.makedirs(dirname(file), exist_ok=True)
            file_cont = self.repo.get_file(join(self.root.path, modelname, str(content["version"]), orig_fname)).get_content()
            with open(file, 'wb') as ofile:
                ofile.write(file_cont)
            save_time = content["from_lasttimes"][fname].replace(tzinfo=timezone.utc).timestamp()
            os.utime(file, (save_time, save_time))
        logger.info(f"Downloaded everything for version {content['version']} of model `{modelname}`")
        return True

########################################################################################################################

def make_dict(string):
    '''convenience method to make a dict from the (local/remote) last_changes.txt-file mapping filename to change-date'''
    if not string:
        return {}
    return {line.split(":")[0]: datetime.strptime(":".join(line.split(":")[1:]).strip(), "%Y-%m-%d %H:%M:%S") for line in string.split('\n')}


def add_number_until_unique(file):
    path = dirname(file)
    filename = basename(file)
    orig_filename = basename(file)
    for i in range(2, 9999):
        if not os.path.exists(os.path.join(path, filename)):
            return filename
        tmp = os.path.splitext(orig_filename)
        filename = tmp[0]+' ('+str(i)+')'+tmp[1]
    raise Exception