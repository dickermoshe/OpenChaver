import logging
import PySimpleGUI as sg
import requests

from .db import get_configuration_db
from .const import LOG_FILE, API_BASE_URL

logger = logging.getLogger(__name__)
sg.theme('Default1')

config_db = get_configuration_db()

if not config_db.is_configured:
    sg.popup("OpenChaver is not configured.\nGo to your account dashbord to add this device.\n", title="OpenChaver")
    exit()

else:
    logging_layout = [
                    [sg.Button('Upload Logs',key='upload_logs')],

                    ]

    layout = [  [sg.Text('Some text on Row 1'),],
                [sg.Frame('Logging', logging_layout,)],
                [sg.Text('Enter something on Row 2'), sg.InputText()],
                [sg.Button('Save'), sg.Button('Cancel')] ]

    # Create the Window
    window = sg.Window('OpenChaver', layout)
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        
        if event in (None, 'Cancel'):   # if user closes window or clicks cancel
            break
        
        elif event == 'upload_logs':
            logger.info(f"Uploading logs")
            log_dir = LOG_FILE.parent
            
            # Get all log files
            log_files = list(log_dir.glob("*.log"))
            
            # Sort by date
            log_files.sort(key=lambda x: x.stat().st_mtime)

            # Read all log files
            logs = []

            for log_file in log_files:
                try:
                    with open(log_file, "r",encoding='utf-8') as f:
                        logs.append(f.read())
                except:
                    continue

            # Join all logs
            logs = "\n".join(logs)

            # Upload logs
            try:
                r = requests.post(f"{API_BASE_URL}logs/",json={'log':'hgh','device_id':config_db.device_id},verify=False)
                if r.status_code == 200 or r.status_code == 201:
                    logger.info(f"Uploaded logs")
                    sg.popup("Logs uploaded successfully", title="OpenChaver")
                else:
                    logger.error(f"Failed to upload logs")
                    raise Exception
            except:
                sg.popup("Failed to upload logs", title="OpenChaver")
                raise