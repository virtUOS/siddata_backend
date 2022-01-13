""" Configuration file with default values. Please enter
 your data and rename the file to config.py to activate it."""

DATABASES = {
    'default': {
        #postgressql
        'ENGINE': 'django.db.backends.postgresql',
         'NAME': 'siddata', # or custom database name
         'USER': 'siddata', # or custom user name
         'PASSWORD': 'enter password here',
         'HOST': 'localhost',
         #'PORT': '',
    }
}

