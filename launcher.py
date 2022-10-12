import os
import time
import threading as th

from waitress import serve
import django
from django.core.management import execute_from_command_line

os.environ['DJANGO_SETTINGS_MODULE'] = 'openchaver.settings'
django.setup()

from openchaver.wsgi import application
from api.service import run_services

if __name__ == '__main__':

    # Run migrations
    execute_from_command_line(['manage.py','migrate'])

    # Run the services
    th.Thread(target=run_services).start()

    # Run server on localhost:8000
    th.Thread(target=serve,args=(application,),kwargs=dict(port='8000',host='127.0.0.1')).start()

    while True:
        time.sleep(5)


    



