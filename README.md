# OpenChaver  

```
# Run the services
python openchaver.py

OR

# Build an Executable
python -m nuitka .\openchaver.py --standalone --output-dir=build --enable-plugin=numpy
```

TODO:
- [x] `scheduler` - Sends events to the `screenshot` service.
- [x] `screenshot` - Takes screenshots of the active window. Sends the screenshot to the `storage` service.
- [x] `storage` - Stores the screenshots in the `sqlite` database.
- [x] Add a `idle` service that will pause the `screenshot` service if the user is idle.
- [x] ~~Add a `keystroke` service that will send events to the `screenshot` service if NSFW text is detected.~~ (Window Defender treats this as a virus. Any workarounds will be unstable.)
- [ ] Create the uninstallation script that will uninstall the application.
- [x] ~~Create the configuration script that will configure the application.~~ (Done by Website)
- [x] Add a `upload` service to upload the screenshots to the remote server.
- [x] Create the remote backend server that will send reports and alerts to the chaver. -> [openchaver-server](https://github.com/dickermoshe/OpenChaver-Server)
- [x] Create the installation script that will install the application.
- [ ] Create the update script that will update the application.
- [ ] Create the documentation for the application.
- [ ] Create the tests for the application.
- [ ] Create the watchdog for the application.


As you can see, there is a lot to do. If you want to help, please contact me.

Checkout releases for the latest binaries.
