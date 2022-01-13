#!/bin/bash
#argument 1 is the path

DIR=$1/$(date +'%Y-%m-%d')
mkdir $DIR
sudo -u postgres pg_dump siddata > $DIR/dump
cp /opt/siddata_backend/siddata_backend/siddata_backend/settings.py $DIR/settings.py.save
cp /opt/siddata_backend/siddata_backend/siddata_backend/config.py $DIR/config.py.save
cd /opt/siddata_backend
git rev-parse --verify HEAD > $DIR/commit_hash
git diff $(git rev-parse --verify HEAD) > $DIR/diffs.patch
#TODO also backup untracked files
cp /etc/apache2/mods-available/wsgi.conf $DIR/wsgi.conf
sudo cp -r /opt/siddata_backend/log $DIR/
cp -r /etc/apache2/sites-available $DIR/
cp /etc/apache2/mods-available $DIR/