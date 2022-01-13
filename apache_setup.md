# Set up in pinky

Read this document before starting and configuring website in apache web server: [HTTPD - Apache2 Web Server](https://ubuntu.com/server/docs/web-servers-apache)


create config file for site-available (generally `/etc/apache2/sites-available/`): `siddata-pinky.conf`:

```

<VirtualHost *:80>
	# ServerAdmin webmaster@localhost
	# DocumentRoot /mnt/d/virtUOS/workspace/apache_local_backend

    ServerName pinky.siddata.de
    ServerAlias vm635.rz.uni-osnabrueck.de vm635.rz.uos.de
	
    RedirectPermanent / https://pinky.siddata.de/

</VirtualHost>

<VirtualHost *:443>
    ServerName pinky.siddata.de
    ServerAlias vm635.rz.uni-osnabrueck.de vm635.rz.uos.de

    SSLEngine on
    SSLCertificateFile      /etc/ssl/certs/pinky-certificate.pem
    SSLCertificateKeyFile   /etc/ssl/private/pinky-certificate.key
    SSLCertificateChainFile /etc/ssl/certs/CA_UOS_chain.pem

    ErrorLog ${APACHE_LOG_DIR}/siddata_error.log
    CustomLog ${APACHE_LOG_DIR}/siddata_access.log combined
    
    <Directory /opt/siddata_backend/siddata_backend/siddata_backend>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    WSGIDaemonProcess siddata_backend python-path=/opt/anaconda3/envs/siddata_36
    WSGIProcessGroup siddata_backend
    WSGIScriptAlias / /opt/siddata_backend/siddata_backend/siddata_backend/wsgi.py

</VirtualHost>

# vim: syntax=apache ts=4 sw=4 sts=4 sr noet

```


### updates in `apache2.conf`

- add below xml in the file (update the value in Directory tag):
	```
	<Directory /mnt/d/virtUOS/workspace/apache_local_backend>
	Options Indexes FollowSymLinks
	AllowOverride None
	Require all granted
	</Directory>
	```

this will allow apache to access backend repository, provide the parent directory of the folder where repository is placed.

- Add below line in apache2.conf file at the end of file:

```
WSGIApplicationGroup %{GLOBAL}
```

- Format for `mods-available/wsgi.conf`:

	```
	<IfModule mod_wsgi.c>


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
	```


- run below command to get content for `mods-available/wsgi.load` file:
```
mod_wsgi-express module-config
```
in siddata_37 python env it returns: 

```
LoadModule wsgi_module "/home/student/d/dpathak/miniconda3/envs/siddata_37/lib/python3.7/site-packages/mod_wsgi/server/mod_wsgi-py37.cpython-37m-x86_64-linux-gnu.so"
WSGIPythonHome "/home/student/d/dpathak/miniconda3/envs/siddata_37"
```

copy this and add same in `wsgi.load` file.


- provide access to following directories to `www-data`:
    - check log files and look for errors, and provide access if required to files/directory to `www-data` user.
