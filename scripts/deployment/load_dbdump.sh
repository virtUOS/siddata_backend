#!/bin/bash
#to backup dump + settings:
# sudo -u postgres pg_dump siddata > pinky_dump_$(date +'%Y-%m-%d') && cp /opt/siddata_backend/siddata_backend/siddata_backend/settings.py ./settings.py.save_$(date +'%Y-%m-%d')

has_user=$(sudo -i -u postgres psql -c '\du' | grep "siddata")
if [[ "$has_user" == *siddata* ]]
then
  echo "Correct user exists already!"
else
  sudo -u postgres psql -U postgres -c "CREATE USER siddata WITH PASSWORD 'siddata';"
fi
sudo -u postgres psql -U postgres -c " SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'siddata' AND pid <> pg_backend_pid(); "
sudo -u postgres psql -U postgres -c "DROP DATABASE siddata; "
sudo -u postgres psql -U postgres -c "DROP SCHEMA public CASCADE; "
sudo -u postgres psql -U postgres -c " CREATE SCHEMA public; "
sudo -u postgres psql -U postgres -c " CREATE DATABASE siddata; "
sudo -u postgres psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE siddata TO siddata;"
if [[ "$1" == *.bz2 ]]
then
  bzip2 -d $1
  name=${1:0:-4}
else
  name=$1
fi
echo $name
sudo -u postgres psql siddata < $name