"""
WSGI config for siddata_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/howto/deployment/wsgi/

The paths set in this file are system-specific as python paths may differ.
On the server brain.siddata.py in the repository at /opt/siddata_backend this 
file is excluded in .git/info/exclude and therefore will not be pulled.

"""

import os

# this import has to happen *after* the paths are set
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'siddata_backend.settings')

application = get_wsgi_application()
