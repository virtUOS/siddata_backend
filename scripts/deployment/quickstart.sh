#!/bin/bash
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"
#https://stackoverflow.com/a/24112741/5122790

# this script activates the environment, if not done yet, installs the requirements, checks for folder-permissions
# and then applies migrations. Further it creates a superuser if "-su" is given as arg and starts the server if "-start" is given as arg.
# If it's supposed to be run on a productive server, where you may need sudo-python, you can run it with "-sudo",
# however (TODO) I am not sure if then it can automatically activate the environment.

#see https://www.freecodecamp.org/news/django-in-the-wild-tips-for-deployment-survival-9b491081c2e4/

#see first comments in server_set_permissions.py on how to create the correct group etc
#git pull ...

# TODO if you're on pinky/brain, compare the settings.py with the settings_default.py if there are new changes you need to incorporate

if [[ "$*" == *-sudo* ]] #if "-sudo" is an argument
then
  echo "Using sudo-python!"
  python_ex='sudo $(which python)'
  pip_ex='sudo $(which python) -m pip'
else
  python_ex='python'
  pip_ex='pip'
fi


### activating conda-env ###
if [ -z "$CONDA_PREFIX" ]
then
      echo "\$CONDA_PREFIX is empty"
      exit
fi
pythonbin=$(which python)

if [[ $pythonbin != *"django_py3"* ]]; then
  echo "activating conda-env.."
  source $CONDA_PREFIX/etc/profile.d/conda.sh
  conda activate django_py36
  if test $? -eq 1
  then
    conda activate django_py37
  fi
  pythonbin=$(which python)
fi

if [[ $pythonbin != *"django_py3"* ]]; then
  echo "Having Problems activating the environment. Do you have a django_py37 or django_py36 Conda-Env?"
  exit
fi

### installing requirements ###
eval "$pip_ex install --upgrade pip"
eval "$pip_ex install -r ../../requirements.txt"
#source .envrc

### checking permissions
eval "$python_ex ./check_permissions.py"
if test $? -eq 1
then
  echo "Wrong permissions!"
  exit 1
fi

### Migrating & starting server ###
echo "Migrating..."
eval "$python_ex ../../siddata_backend/manage.py migrate"
eval "$python_ex ../../siddata_backend/manage.py collectstatic"
#eval "$python_ex ../siddata_backend/manage.py loaddata example-django/fixtures/quickstart.json"

if [[ "$*" == *-createsu* ]] #if "-createsu" is an argument (DO NOT (!!!!!!) DO THIS ON PRODUCTIVE MACHINES!!!!)
then
  echo "Creating super-user 'adm', I really really hope you're not on a productive machine!"
  #eval "$python_ex ../siddata_backend/manage.py createsuperuser --username adm --email no@mail.de --noinput"
  echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('adm', 'no@mail.de', 'password')" | python ../siddata_backend/manage.py shell
  #on pinky this may be `sudo echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('adm', 'no@mail.de', 'password')" | sudo $(which python) ../siddata_backend/manage.py shell`
fi

if [[ "$*" == *-start* ]] #if "-start" is an argument
then
  echo "Starting Backend-Server.."
  eval "$python_ex ../siddata_backend/manage.py runserver 0.0.0.0:8000 --noreload"
fi



