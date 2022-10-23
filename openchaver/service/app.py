import logging

from flask import Flask, jsonify, request

from playhouse.dataset import DataSet
import datetime
from marshmallow import Schema, fields

from ..const import DB_PATH
from .api import api

ds = DataSet( 'sqlite:///' + str( DB_PATH ) )
ds.close()

app = Flask(__name__)

logger = logging.getLogger(__name__)

class ConfigureRequest(Schema):
    device_id = fields.UUID(required=True)

@app.before_request
def before_request():
    ds.connect()


@app.after_request
def after_request(response):
    ds.close()
    return response

class ConfigConfigureRequest(Schema):
    device_id = fields.UUID(required=True)
@app.route('/configure', methods=['POST'])
def configure():
    data = request.get_json()
    
    errors = ConfigureRequest().validate(data)
    if errors:
        return jsonify(errors), 400
    
    device_id = data['device_id']

    # Check if device exists
    status, json = api(f'/devices/{device_id}/register_device/')
    if not status:
        if len(json.keys()) == 0:
            return jsonify({'error': 'Cant connect to OpenChaver server.'}), 400
        else:
            return jsonify({'error': json['error']}), 400
    else:
        try:
            device_table = ds['devices']
            device = device_table.find_one()
            if device:
                print(dict(device))
                return jsonify({'error': 'Device is already configured.'}), 400
            else:
                device_table.insert(device_id=device_id)
                return jsonify({'success': True})
        except:
            logger.exception('Failed to save device to database')
            return jsonify({'error': 'Failed to save device to database'}), 400


class ScreenshotRequest(Schema):
    title = fields.String(required=True)
    exec_name = fields.String(required=True)
    base64_image = fields.String(required=True)
    profane = fields.Boolean(required=True)
    nsfw = fields.Boolean(required=True)
    nsfw_detections = fields.Dict(required=True)
    created = fields.DateTime(required=True)
@app.route('/screenshot', methods=['POST'])
def screenshot():
    data = request.get_json()
    
    errors = ScreenshotRequest().validate(data)
    if errors:
        return jsonify(errors), 400
    
    try:
        screenshot_table = ds['screenshots']
        # add screenshot to database using dict
        screenshot_table.insert(**data)
        return jsonify({'success': True})
    except:
        logger.exception('Failed to save screenshot to database')
        return jsonify({'error': 'Failed to save screenshot to database'}), 400

@app.route('/alive', methods=['GET'])
def alive():
    return jsonify({'success': True}) # 200 OK

@app.route('/upload', methods=['GET'])
def upload_screenshot():
    screenshot_table = ds['screenshots']
    
    try:
        device_id = ds['devices'].find_one()['device_id']
    except:
        return jsonify({'error': 'Device is not configured.'}), 400
    
    screenshot = screenshot_table.find_one()
    if not screenshot:
        return jsonify({'error': 'No screenshots to upload.'}), 400
    else:
        # Remove the id
        screenshot = dict(screenshot)
        id = screenshot.pop('id')

        if screenshot:
            status, json = api(f'/devices/{device_id}/add_screenshot/', method='POST', data=screenshot)
            if status:
                screenshot_table.delete(id)
                return jsonify({'success': True})
            else:
                return jsonify(json), 400

@app.route('/cleanup', methods=['GET'])
def cleanup():
    """Delete all screenshots older than 7 days"""
    screenshot_table = ds['screenshots']
    
    for screenshot in screenshot_table:
        created = screenshot['created']
        # Parse the date as ISO 8601
        created = datetime.datetime.fromisoformat(created)
        if (datetime.datetime.now() - created).days > 7:
            screenshot_table.delete(screenshot['id'])
    return jsonify({'success': True})