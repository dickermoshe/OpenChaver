import os
import time
import threading as th

from waitress import serve
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'openchaver.settings'
django.setup()

from openchaver.wsgi import application
from api.service import run_services

if __name__ == '__main__':
    # Run the services
    th.Thread(target=run_services).start()
    
    # Run server
    th.Thread(target=serve,args=(application,),kwargs=dict(port='8000')).start()

    while True:
        time.sleep(5)
        

    



