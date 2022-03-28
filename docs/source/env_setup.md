# Environment setup

The Siddata project was developed in two main components: the Django-based backend, and the Stud.IP-integrated frontend. 
For developing in the backend, you will probably need some frontend to test the backend behavior. 
The Stud.IP frontend can be found [here](https://github.com/virtUOS/siddata_studip_plugin). 
Refer to the frontend's documentation for setting it up. 

## Backend setup
For setting up the backend follow these steps:
1. Clone the repository.
2. Create a virtual python environment with python version 3.7.
3. Install the packages from requirements.txt and requirements-dev.txt.
4. Install [PostgreSQL](https://www.postgresql.org/download/) and get your PostgreSQL server running.
5. In PostgreSQL, create a database called "siddata" and a user which has all privileges on that database. [This tutorial](https://www.postgresqltutorial.com/install-postgresql-linux/) might help.
6. Create a settings.py file. For that purpose you can just copy the settings_default.py. 
7. Fill out your settings.py file:
   - Enter a random secret key for development purposes. 
   - Enter allowed hostnames for the development server.
   - Enter your database credentials in `DATABASES`.
   - If you have a seafile server holding trained models, enter the corresponding credentials in the seafile-model-downloader section. Otherwise, comment out `'apps.bert_app.apps.BertAppConfig'` in `INSTALLED_APPS`.
   - [Optional] If you want to collect udemy courses, create a udemy client and fill the corresponding credentials in `MOOC_CLIENTS`.
   - [Optional] If you want the email service to work, fill the `EMAIL_` variables. 
   - [Optional] Enter your name and email address to `ADMINS` if you want to receive admin reports as emails.
8. Migrate the database: `python manage.py migrate`
9. Run the server and check if everything works: `python manage.py runserver`
10. Create a superuser in order to manage your database via the web interface: `python manage.py createsuperuser`

## Troubleshooting:
- If you get an import error, check your `settings.BASE_DIR` variable. The path has to be like `/path/to/your/project/siddata_backend`. It has to contain the project directory at the end. If this isn't the case, adjust the setting of `BASE_DIR` accordingly.