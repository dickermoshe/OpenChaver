# OpenChaver  

TODO:

- [ ] Create the uninstallation script that will uninstall the application.
- [ ] Create UI
- [ ] Create Taskbar Icon
- [ ] Create the installation script that will install the application.
- [ ] Create the update script that will update the application.
- [ ] Create the documentation for the application.
- [ ] Create the tests for the application.


As you can see, there is a lot to do. If you want to help, please contact me.

To run with python
```
pip install -r requirements.txt
python manage.py setup
```

## Braakdown

This program is used to monitor computer activty. It will only be stored locally. The program will be able to monitor the following:
1. Program usage
2. Internet usage
3. Computer usage
4. Sceenshots

It will do this by running a Windows Service. Being that a service cant access the local user session, it will run quick one time processes as the active user sessions to get usage info.  
A seperate service is used to watchdog the main service. If the main service is not running, it will restart it. This is to ensure that the service is always running. The main service watches the watchdog as well.  

The program will use a local server for the user interface. The user interface will be able to view the data that is being collected. In the future we will add port forwarding to the server so that the user can access the data from anywhere.  

The program will also have a taskbar icon that will allow the user to access the user interface.  