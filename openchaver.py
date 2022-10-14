# import os
# import sys
# import time
from openchaver.__main__ import main # as openchaver_main

# if os.name == 'nt':
#     def main():
#         import win32serviceutil  # ServiceFramework and commandline helper
#         import win32service  # Events
#         import servicemanager
#         import win32timezone
#         import threading

        
#         class MyService:
#             """Silly little application stub"""
#             def stop(self):
#                 """Stop the service"""
#                 self.running = False

#             def run(self):
#                 """Main service loop. This is where work is done!"""
#                 self.running = True

#                 # Start the service on a new thread
#                 # die_event = threading.Event()
#                 # t = threading.Thread(target=openchaver_main,args=(die_event),daemon=True)
#                 # t.start()

#                 while self.running:
#                     time.sleep(5)
#                     servicemanager.LogInfoMsg("Service running...")
                
#                 # die_event.set()
#                 # t.join()





#         class MyServiceFramework(win32serviceutil.ServiceFramework):

#             _svc_name_ = 'openchaver'
#             _svc_display_name_ = 'OpenChaver'

#             def SvcStop(self):
#                 """Stop the service"""
#                 self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
#                 self.service_impl.stop()
#                 self.ReportServiceStatus(win32service.SERVICE_STOPPED)

#             def SvcDoRun(self):
#                 """Start the service; does not return until stopped"""
#                 self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
#                 self.service_impl = MyService()
#                 self.ReportServiceStatus(win32service.SERVICE_RUNNING)
#                 # Run the service
#                 self.service_impl.run()
        
#         if len(sys.argv) == 1:
#             servicemanager.Initialize()
#             servicemanager.PrepareToHostSingle(MyServiceFramework)
#             servicemanager.StartServiceCtrlDispatcher()
#         else:
#             win32serviceutil.HandleCommandLine(MyServiceFramework)
# else:
#     print('Unsupported OS')
#     exit(1)

if __name__ == '__main__':
    main()



    



