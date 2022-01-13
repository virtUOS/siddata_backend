# on the server:
# sudo su
#   apt install members
#   groupadd sidbackendusers
#   for u in $(members anaconda); do usermod -a -G sidbackendusers $u; done
#   usermod -a -G sidbackendusers www-data
# CTRL+D
# now we have a group that all allowed users + www-data are in, and we can allow write-access to critical dirs to this group

from os.path import join, isdir, isfile, abspath, dirname, splitext
import os
from pwd import getpwuid
from grp import getgrgid
import stat
import grp
import logging

BASE_DIR = abspath(join(dirname(__file__), '..'))
GROUPNAME = 'sidbackendusers'

nltk_dir = join(BASE_DIR, 'nltk_data')
data_dir = join(BASE_DIR, 'data')
log_dir = join(BASE_DIR, 'log')


def main():
    if getgrgid(os.stat(BASE_DIR).st_gid)[0] != GROUPNAME:
        logging.info("Changing group of the entire Siddata-dir..")
        chgrp(BASE_DIR, GROUPNAME)

    for dir in [nltk_dir, data_dir, log_dir]:
        logging.info(f"Curr Testing: {dir}")
        res = os.stat(dir)
        usr_rwx = bool(res.st_mode & stat.S_IRUSR) and bool(res.st_mode & stat.S_IWUSR) and bool(res.st_mode & stat.S_IXUSR)
        group_rwx = bool(res.st_mode & stat.S_IRGRP) and bool(res.st_mode & stat.S_IWGRP) and bool(res.st_mode & stat.S_IXGRP)
        other_none = not (bool(res.st_mode & stat.S_IROTH) or bool(res.st_mode & stat.S_IWOTH) or bool(res.st_mode & stat.S_IXOTH))

        # logging.info('user', getpwuid(res.st_uid).pw_name); # logging.info('group', getgrgid(res.st_gid)[0])
        # logging.info('User RWX:', usr_rwx); # logging.info('Group RWX:', group_rwx); # logging.info('Other None:', other_none)

        if not (usr_rwx and group_rwx and other_none):
            logging.info("Changing mods..")
            os.chmod(dir, 0o770)
        if getgrgid(res.st_gid)[0] != GROUPNAME:
            logging.info("Changing group..")
            chgrp(dir, GROUPNAME)



#https://stackoverflow.com/a/46862255/5122790
def chgrp(LOCATION,OWNER,recursive=False):
  gid = grp.getgrnam(OWNER).gr_gid
  if recursive:
      if os.path.isdir(LOCATION):
        os.chown(LOCATION,-1,gid)
        for curDir,subDirs,subFiles in os.walk(LOCATION):
          for file in subFiles:
            absPath = os.path.join(curDir,file)
            os.chown(absPath,-1,gid)
          for subDir in subDirs:
            absPath = os.path.join(curDir,subDir)
            os.chown(absPath,-1,gid)
      else:
       os.chown(LOCATION,-1,gid)
  else:
    os.chown(LOCATION,-1,gid)



if __name__ == '__main__':
    main()
