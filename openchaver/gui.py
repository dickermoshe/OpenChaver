import PySimpleGUI as sg
import re
import requests
from . import API_BASE_URL, BASE_URL
from .db import ConfigDB
from .config import uninstall


def configure_gui():
    """Configure the client computer"""
    layout = [  [sg.Titlebar('OpenChaver Configuration')],
                [sg.Text('OpenChaver Configuration',justification='center',size=(30,1),font=("Helvetica", 18))],
                [sg.Text('Please enter your Device ID to setup your device. You can find your Device ID on your accounts Dashboard.',justification='center',size=(45,3))],
                [sg.Text('Device ID', size=(15, 1),pad=((10,10),(0,20))), sg.Input(visible=True, key='-Device ID-',pad=((10,10),(0,20)),)],
                [sg.Submit(), sg.Cancel()] ]
    
    window = sg.Window('Window Title', layout,finalize=True,size=(400,200),element_justification='center')
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        elif event == 'Submit':
            device_id = values['-Device ID-']
            
            # Check if its valid
            data = {
                'device_id': device_id,
            }
            try:
                r = requests.post(API_BASE_URL+f"devices/register_device/", data=data)
            except:
                sg.popup("Error connecting to server")
                continue
            if r.status_code == 200:
                db = ConfigDB()
                if not db.configured:
                    d = r.json()
                    device = {
                        "user": d["user"],
                        "device_name": d["name"],
                        "device_id": device_id,
                    }
                    db.save_device(device)
                    sg.popup("Device registered successfully")
                    window.close()
                    break
                else:
                    sg.popup("Device already registered")
                    continue
            else:
                sg.popup("Invalid device ID.")
                continue
    window.close()

def uninstall_gui(device_id):
    """Configure the client computer"""
    layout = [  [sg.Titlebar('OpenChaver Uninstall')],
                [sg.Text('OpenChaver Uninstall',justification='center',size=(30,1),font=("Helvetica", 18))],
                [sg.Text('Please enter your Uninstall Code to Uninstall OpenChaver your device. You can find your Uninstall Code on your accounts Dashboard.',justification='center',size=(45,3))],
                [sg.Text('Uninstall Code', size=(15, 1),pad=((10,10),(0,20))), sg.Input(visible=True, key='-Uninstall Code-',pad=((10,10),(0,20)),)],
                [sg.Submit(), sg.Cancel()] ]
    
    window = sg.Window('Window Title', layout,finalize=True,size=(400,200),element_justification='center')
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        elif event == 'Submit':
            uninstall_code = values['-Uninstall Code-']
            
            # Check if its valid
            data={
                "device_id":device_id,
                "uninstall_code": uninstall_code,
                }
            try:
                r = requests.post(API_BASE_URL+f"devices/register_device/", data=data)
            except:
                sg.popup("Error connecting to server")
                continue
            if r.status_code == 200:
                uninstall()
            else:
                sg.popup("Invalid Uninstall Code.")
                continue
    window.close()


