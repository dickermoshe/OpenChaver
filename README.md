# OpenChaver
`python -m openchaver` will start the services.



The working services are:
- [x] `scheduler` - Sends events to the `screenshot` service.
- [x] `screenshot` - Takes screenshots of the active window. Sends the screenshot to the `storage` service.
- [x] `storage` - Stores the screenshots in the `sqlite` database.

TODO:
- [ ] Add a `upload` service to upload the screenshots to the remote server.
- [ ] Add a `keystroke` service that will send events to the `screenshot` service if NSFW text is detected.
- [ ] Add a `idle` service that will pause the `screenshot` service if the user is idle.

- [ ] Create the remote backend server that will send reports and alerts to the chaver.
- [ ] Create the installation script that will install the application.
- [ ] Create the uninstallation script that will uninstall the application.
- [ ] Create the update script that will update the application.
- [ ] Create the configuration script that will configure the application.
- [ ] Create the documentation for the application.
- [ ] Create the tests for the application.
- [ ] Create the watchdog for the application.


As you can see, there is a lot to do. If you want to help, please contact me.




