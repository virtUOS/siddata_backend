# Configuration of Siddata Django Servers

## Productive System
brain.siddata.de / vm561.rz.uos.de

## Test System
pinky.siddata.de / vm635.rz.uos.de

Operating System: Ubuntu 18.04 LTS
Apache Web Server 2.4

# Login via ssh
Im Terminal

    ssh username@pinky.siddata.de


Add user to sudoer group:
    
    sudo usermod -a -G vmusers Username


## Install Anaconda & Django Code
Follow instructions at Seafile
/siddata/Technik/siddata_entwicklungsumgebung/DOKU_backend_entwicklungsumgebung_einrichtung_(wip)_v1_ubuntu_linux_EN.md

# Uncomplicated Firewall (UFW)
Install UFW
    
    sudo apt-get install ufw

Block all incoming connections
    
    sudo ufw default deny incoming

Allow ssh connections
    
    sudo ufw allow ssh


Allow connections to port 443 (reserved for https)
   
    sudo ufw allow 443

Allow Apache 
    
    sudo ufw allow 8000

Show ufw status
    
    sudo ufw status verbose


## SSL Certificates
To get SSL certificate from Rechenzentrum, follow tutorial at
https://www.rz.uni-osnabrueck.de/Dienste/UNIOS-CA/index.htm 

### Apache2 Webserver
Install apache packages

    sudo apt-get install apache2 libapache2-mod-wsgi-py3 

### Configure mod-wsgi with Anaconda
Follow tutorial at: https://medium.com/@gevezex/ubuntu-anaconda-env-django-apache-mod-wsgi-howto-in-10-steps-c9008e1d8bfe
1. Activate conda environment
    
    > source activate django_py36

2. Make sure that static files are copied to staticfiles directory
    > python manage.py collectstatic
3. Install python mod-wsgi with pip
    > pip install mod-wsgi
4. Execute command "mod_wsgi-express"
First find out where it is located
    > which mod_wsgi-express
    # output of the above command:
    /opt/anaconda/envs/django_py36/bin/mod_wsgi-express
Call the command
    >  sudo /opt/anaconda/envs/django_py36/bin/mod_wsgi-express install-module
Output of the above command:
    > LoadModule wsgi_module "/usr/lib/apache2/modules/mod_wsgi-py36.cpython-36m-x86_64-linux-gnu.so"
    > WSGIPythonHome "/opt/anaconda/envs/django_py36"
Copy the output of the command into the file /etc/apache2/mods-available/wsgi.load
5. Enable wsgi mod in apache
    > a2enmod wsgi
6. Restart apache
    > sudo service apache2 restart

### Configure path to Django project
The file /etc/apache2/mods-available/wsgi.conf should look as follows:
    
    <IfModule mod_wsgi.c>
     
        # Django static files will be copied to /opt/siddata_backend/collected_apache_static
        Alias /static/ /opt/siddata_backend/collected_apache_static/
     
        <Directory /opt/siddata_backend/collected_apache_static>
        Require all granted
        </Directory>

        # Django configuration
        WSGIScriptAlias / /opt/siddata_backend/siddata_backend/siddata_backend/wsgi.py
        WSGIPythonHome /opt/anaconda/envs/django_py36
        WSGIPythonPath /opt/siddata_backend/siddata_backend
        # WSGIProcessGroup %{GLOBAL}

        WSGIDaemonProcess brain.siddata.de

        <Directory /opt/siddata_backend/siddata_backend/siddata_backend>
            <Files wsgi.py>
                Require all granted
            </Files>
        </Directory>


        #This config file is provided to give an overview of the directives,
        #which are only allowed in the 'server config' context.
        #For a detailed description of all avaiable directives please read
        #http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives



        #WSGISocketPrefix: Configure directory to use for daemon sockets.
        #
        #Apache's DEFAULT_REL_RUNTIMEDIR should be the proper place for WSGI's
        #Socket. In case you want to mess with the permissions of the directory,
        #you need to define WSGISocketPrefix to an alternative directory.
        #See http://code.google.com/p/modwsgi/wiki/ConfigurationIssues for more
        #information

            #WSGISocketPrefix /var/run/apache2/wsgi


        #WSGIPythonOptimize: Enables basic Python optimisation features.
        #
        #Sets the level of Python compiler optimisations. The default is '0'
        #which means no optimisations are applied.
        #Setting the optimisation level to '1' or above will have the effect
        #of enabling basic Python optimisations and changes the filename
        #extension for compiled (bytecode) files from .pyc to .pyo.
        #When the optimisation level is set to '2', doc strings will not be
        #generated and retained. This will result in a smaller memory footprint,
        #but may cause some Python packages which interrogate doc strings in some
        #way to fail. 

            #WSGIPythonOptimize 0


        #WSGIPythonPath: Additional directories to search for Python modules,
        #                overriding the PYTHONPATH environment variable.
        #
        #Used to specify additional directories to search for Python modules.
        #If multiple directories are specified they should be separated by a ':'.

            #WSGIPythonPath directory|directory-1:directory-2:...


        #WSGIPythonEggs: Directory to use for Python eggs cache.
        #
        #Used to specify the directory to be used as the Python eggs cache


        #directory for all sub interpreters created within embedded mode.
        #This directive achieves the same affect as having set the
        #PYTHON_EGG_CACHE environment variable.
        #Note that the directory specified must exist and be writable by the user
        #that the Apache child processes run as. The directive only applies to
        #mod_wsgi embedded mode. To set the Python eggs cache directory for
        #mod_wsgi daemon processes, use the 'python-eggs' option to the
        #WSGIDaemonProcess directive instead. 

            #WSGIPythonEggs directory



        #WSGIRestrictEmbedded: Enable restrictions on use of embedded mode.
        #
        #The WSGIRestrictEmbedded directive determines whether mod_wsgi embedded
        #mode is enabled or not. If set to 'On' and the restriction on embedded
        #mode is therefore enabled, any attempt to make a request against a
        #WSGI application which hasn't been properly configured so as to be
        #delegated to a daemon mode process will fail with a HTTP internal server
        #error response. 

            #WSGIRestrictEmbedded On|Off



        #WSGIRestrictStdin: Enable restrictions on use of STDIN.
        #WSGIRestrictStdout: Enable restrictions on use of STDOUT.
        #WSGIRestrictSignal: Enable restrictions on use of signal().
        #
        #Well behaved WSGI applications neither should try to read/write from/to
        #STDIN/STDOUT, nor should they try to register signal handlers. If your
        #application needs an exception from this rule, you can disable the
        #restrictions here.

 
            #WSGIRestrictStdin On
            #WSGIRestrictStdout On
            #WSGIRestrictSignal On



        #WSGIAcceptMutex: Specify type of accept mutex used by daemon processes.
        #
        #The WSGIAcceptMutex directive sets the method that mod_wsgi will use to
        #serialize multiple daemon processes in a process group accepting requests
        #on a socket connection from the Apache child processes. If this directive
        #is not defined then the same type of mutex mechanism as used by Apache for
        #the main Apache child processes when accepting connections from a client
        #will be used. If set the method types are the same as for the Apache
        #AcceptMutex directive.

            #WSGIAcceptMutex default



        #WSGIImportScript: Specify a script file to be loaded on process start. 
        #
        #The WSGIImportScript directive can be used to specify a script file to be
        #loaded when a process starts. Options must be provided to indicate the
        #name of the process group and the application group into which the script
        #will be loaded.

            #WSGIImportScript process-group=name application-group=name


        #WSGILazyInitialization: Enable/disable lazy initialisation of Python. 
        #
        #The WSGILazyInitialization directives sets whether or not the Python
        #interpreter is preinitialised within the Apache parent process or whether
        #lazy initialisation is performed, and the Python interpreter only
        #initialised in the Apache server processes or mod_wsgi daemon processes
        #after they have forked from the Apache parent process. 

            #WSGILazyInitialization On|Off

    </IfModule>

  


## Encryption with SSL
Path to private key, certificate and certificate chain
    SSLCertificateFile      /etc/ssl/certs/brain-certificate.pem
    SSLCertificateKeyFile   /etc/ssl/private/brain-certificate.key
    SSLCertificateChainFile /etc/ssl/certs/CA_UOS_chain.pem

### Webserver Gateway Interface (WSGI)
The following file /etc/apache2/sites-available/brain.conf should look like this:

    <VirtualHost *:80>
        ServerName brain.siddata.de
        ServerAlias vm561.rz.uni-osnabrueck.de vm561.rz.uos.de

        RedirectPermanent / https://brain.siddata.de/
    </VirtualHost>

    <VirtualHost *:443>
        ServerName brain.siddata.de
        ServerAlias vm561.rz.uni-osnabrueck.de vm561.rz.uos.de

        SSLEngine on
        SSLCertificateFile      /etc/ssl/certs/brain-certificate.pem
        SSLCertificateKeyFile   /etc/ssl/private/brain-certificate.key
        SSLCertificateChainFile /etc/ssl/certs/CA_UOS_chain.pem

        ErrorLog ${APACHE_LOG_DIR}/siddata_backend_error.log
        CustomLog ${APACHE_LOG_DIR}/siddata_backend.log combined

    </VirtualHost>


## Copy static files
For the apache to find the static files of the django project call:
    > python manage.py collectstatic
The directories are configured in settings.py

## Useful logs 
systemctl -xe
less /var/log/apache2/siddata_backend_error.log
less /var/log/apache2/error.log

