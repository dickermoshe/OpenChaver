# OpenChaver  

```
# Run the services
python openchaver.py

OR

# Build an Executable
python -m nuitka .\openchaver.py --standalone --onefile --enable-plugin=numpy --include-data-dir=`"${pwd}\openchaver\nsfw_model`"=nsfw_model
```

The working services are:
- [x] `scheduler` - Sends events to the `screenshot` service.
- [x] `screenshot` - Takes screenshots of the active window. Sends the screenshot to the `storage` service.
- [x] `storage` - Stores the screenshots in the `sqlite` database.
- [x] Add a `idle` service that will pause the `screenshot` service if the user is idle.
- [x] ~~Add a `keystroke` service that will send events to the `screenshot` service if NSFW text is detected.~~ (Window Defender treats this as a virus. Any workarounds will be unstable.)


TODO:
- [ ] Create the uninstallation script that will uninstall the application.
- [ ] Create the configuration script that will configure the application.
- [ ] Add a `upload` service to upload the screenshots to the remote server.
- [ ] Create the remote backend server that will send reports and alerts to the chaver. -> [openchaver-server](https://github.com/dickermoshe/OpenChaver-Server)
- [ ] Create the installation script that will install the application.
- [ ] Create the update script that will update the application.
- [ ] Create the documentation for the application.
- [ ] Create the tests for the application.
- [ ] Create the watchdog for the application.


As you can see, there is a lot to do. If you want to help, please contact me.


## Breakdown

```
db.py - The database module. It contains the `db` class that is used by the models to store and retrieve data from the database.

detect.py - The detection module. This contains a bunch of functions that are ran as threads. Look at service.py to see how they are used.

dog.py - the watchdog module.

models.py - The models module. This contains the `ConfigurationModel` and `ScreenshotModel` models that are used to store and retrieve data from the database.

nsfw.py - The NSFW module. This contains the `OpenNsfw` and `NudeNet` that is used to detect NSFW content in images.

profanity.py - The profanity module. This checks for not nice words in the text.

server.py - The server module. For the main openchaver site to communicate with the client application.

service.py - The service module.  This does the following:
    1. It creates the `scheduler` service that will send events to the `screenshot` service.
    
    2. It creates the `screenshot` service that will take screenshots of the active window.
    
    3. It creates the `idle` service that will pause the `screenshot` service if the user is idle.

    4. It creates the `upload` service that will upload the screenshots to the backend server.

    5. It creates the `watchdog` service that will check the status of the application and send alerts to the chaver if evasive action is detected.

window.py - The window module. This contains the `Window` class that is used to get the active window and take screenshots of it.
```