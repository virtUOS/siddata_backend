Rollout

# Use SSH to log into the Server
- open local terminal (or PuTTY on Windows)
- `ssh your_username@brain.siddata.de`
- enter your LDAP-Passwort 
- If Login doesn't work, it's probably that the user is not in the necessary group and thus doesn't have rights - Users with Admin-rights for the server can do that (fweber,sebosada,tthelen,eludwig).

## Ensure your user has the correct rights
- run the command `groups`. It should tell you that at least you are in the groups: `gitusers anaconda sudoers vmusers`
    - If you aren't, ask a user with Admin-rights to add you to those (fweber,sebosada,tthelen,eludwig).

# Ensure you have conda
- run the command `which conda`. If it doesn't return anything, you need to install conda. If not, proceed with activating the environment.
    - To install conda, run `cd /tmp && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && bash ./Miniconda3-latest-Linux-x86_64.sh`
    - Say `yes` when it asks you to run `conda init`
    - Then you need to log out of your session (`CTRL+D` on Linux) and reconnect.

# activate Anaconda Environment
- Use SSH to log into Pinky/Brain
- TODO
- `conda activate /opt/anaconda/envs/django_py36`
- if that doesn't work, it may be because the User doesn't have the rights to use Anaconda - Users with Admin-rights can give those (fweber,sebosada,tthelen,eludwig).

# navigate to the project directory
- `cd /opt/siddata_backend`

# update the repository 
- ensure that the `master` branch is active 
    - `git branch` should highlight the correct branch in green
- pull newest commits `sudo git pull`

## get the settings
- Make sure your `settings.py` and `config.py`, which are not updated via git, contain what you want it to contain (enabled apps, configs, ...)

# update the database
- apply new migrations: 
    - `cd` to `/opt/siddata_backend/siddata_backend`
    - run `sudo which python` to check which `python` the `su` (superuser) uses. If the result is something like `/usr/bin/python`, and not something like `/opt/anaconda/envs/django_py36/bin/python`, you have to run `sudo $(which python)` everytime you want to run your anaconda-python as `su`.
    - `sudo $(which python) manage.py migrate`

## Delete the Database **(!! ONLY IF YOU KNOW WHAT YOU'RE DOING!!)**
- Before you delete the datebase, make sure to create a backup! `sudo -u postgres pg_dump siddata > ~/pinky_dump_$(date +'%Y-%m-%d') && cp /opt/siddata_backend/siddata_backend/siddata_backend/settings.py ~//settings.py.save_$(date +'%Y-%m-%d')`
- As long as we are still in testing-mode or you are on Pinky **and know what you're doing**, you can delete the database using `sudo $(which python) manage.py flush`

# Restart apache
- All the previous changes will only be applied after restarting apache: `sudo service apache2 restart`

# Admin-View of the Backend
- in Browser: "brain.siddata.de"
- login there as Admin, with passwort from Keepass (only certain users have the rights for this)

# Test functionality
- Start test-system under https://studip3g-test.rz.uos.de/studip/siddata/index.php?logout=true&set_language=de_DE
- or https://studip3g-test.rz.uni-osnabrueck.de/studip/siddata/plugins.php/siddataplugin/siddata/index
    * "https://studip3g-test.rz.uos.de" tests with pinky
    * "https://studip-test.uos.de" is supposed to test with brain
    * The backend server itself is available at "https://brain.siddata.de/backend/home"
- log in there 
    - for example as user "test1" with password "siddata"
    - or as "test_autor" with password "testing"
- navigate to the Siddata-Plugin using the brain-icon in the upper right.
 
## Initialize
- Wait a little or manually ensure that all Cron-Jobs run before you test via the Frontend, to ensure you won't get exceptional cases.

## Log-Files
- There are two log-files:
    - at `/var/log/apache2/siddata_backend_error.log`
    - at `/opt/siddata_backend/log/siddata_app.log`
