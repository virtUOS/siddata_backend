#!/bin/bash
parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd "$parent_path"

sudo -u postgres psql -c 'DROP DATABASE siddata;'
sudo -u postgres psql -c 'CREATE DATABASE siddata;'
sudo -u postgres psql -c 'GRANT ALL PRIVILEGES ON DATABASE siddata TO siddata;'
python3 ../../siddata_backend/manage.py migrate
if test $? -eq 0
then
  python3 ../../siddata_backend/manage.py makemigrations
  if test $? -eq 0
  then
    echo "everything successful!!"
  else
    echo "makemigrations unsuccessful!"
  fi
else
  echo "migrate unsuccessful!"
fi
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('adm', 'no@mail.de', 'password')" | python ../../siddata_backend/manage.py shell