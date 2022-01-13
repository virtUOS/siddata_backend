#https://www.thegeekdiary.com/understanding-basic-file-permissions-and-ownership-in-linux/
#check if this user and www-data can write into the relevant directories, suggest using chgrp otherwise

from os.path import join, isdir, isfile, abspath, dirname, splitext
import os
import tempfile
import errno
import sys
import grp, pwd
import stat
import socket


if "uni-osnabrueck.de" in socket.gethostname():
    #then its's pinky or brain (latter I hope)
    ALSO_TEST_FOR = 'www-data'
else:
    ALSO_TEST_FOR = None

BASE_DIR = abspath(join(dirname(__file__), '..'))
sys.path.append(BASE_DIR)
sys.path.append(join(BASE_DIR, 'siddata_backend'))

def main():
    nltk_dir = join(BASE_DIR, 'nltk_data')
    data_dir = join(BASE_DIR, 'data')
    log_dir = join(BASE_DIR, 'log')

    if ALSO_TEST_FOR:
        test_groups = get_groups(ALSO_TEST_FOR)
        for dir in (BASE_DIR, nltk_dir, data_dir, log_dir):
            res = os.stat(dir)
            group = grp.getgrgid(res.st_gid)[0]
            assert group in test_groups, f'The user "{ALSO_TEST_FOR}" cannot write into {dir}! Use chgrp to change the group of that dir to one of her groups ({str(test_groups)})'
            assert bool(res.st_mode & stat.S_IRGRP) and bool(res.st_mode & stat.S_IWGRP) and bool(res.st_mode & stat.S_IXGRP), f'The directory {dir} needs group-permissions to RWX!'
            #https://stackoverflow.com/questions/21797372/django-errno-13-permission-denied-var-www-media-animals-user-uploads says RW would be enough, but with that you cannot enter dirs..

    for dir in (nltk_dir, data_dir, log_dir):
        assert test_dir_perm(dir), f'My User cannot write into the path {dir}! Does it have the correct User-permissions?'

    test_nltk()


def get_groups(uname):
    groups = [g.gr_name for g in grp.getgrall() if uname in g.gr_mem]
    gid = pwd.getpwnam(uname).pw_gid
    groups.append(grp.getgrgid(gid).gr_name)
    return groups


def test_nltk():
    import nltk
    import sys
    sys.path.append(join(dirname(__file__), "..", "..", "siddata_backend"))
    from bert_app.bert_utils import download_nltk_dependencies
    nltk_dir = join(BASE_DIR, 'nltk_data')
    download_nltk_dependencies(nltk_dir)
    assert isdir(nltk_dir)
    nltk.data.path = [nltk_dir] + nltk.data.path
    from nltk.corpus import stopwords
    from nltk.text import TextCollection
    _ = stopwords.words("english") + stopwords.words("german")
    _ = nltk.word_tokenize('This is a text')
    TextCollection('This is a text')


def test_dir_perm(dir):
    res = True
    if not isdir(dir):
        os.makedirs(dir)
    res = res and os.access(dir, os.W_OK | os.R_OK | os.X_OK) #https://stackoverflow.com/a/2113511/5122790 for dirs you need the execute-permission as well.
    res = res and is_writable(dir)
    return res


def is_writable(path):
    try:
        testfile = tempfile.TemporaryFile(dir = path)
        testfile.close()
    except (OSError, IOError) as e:
        if e.errno == errno.EACCES or e.errno == errno.EEXIST:  # 13, 17
            return False
        e.filename = path
        raise
    return True


if __name__ == '__main__':
    exit(main())
