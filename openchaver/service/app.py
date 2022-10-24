import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from playhouse.dataset import DataSet

import datetime
from random import choice
from marshmallow import Schema, fields

from ..const import DB_PATH, LOCAL_SERVER_PORT
from .api import api
from ..logger import handle_error


@handle_error
def run_app():
    logger = logging.getLogger(__name__)
    logger.info('Starting the OpenChaver Server')

    db_url = f'sqlite:///{DB_PATH}'
    logger.info(f'Initializing: {db_url}')
    ds = DataSet(db_url)
    ds.close()

    app = Flask(__name__)
    CORS(app)

    class ConfigureRequest(Schema):
        device_id = fields.UUID(required=True)

    # These function open and close the DB connection
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
        app.logger.info('Received a configure request')
        data = request.get_json()

        errors = ConfigureRequest().validate(data)
        if errors:
            app.logger.error(f'Invalid request: {errors}')
            return jsonify(errors), 400

        device_id = data['device_id']
        app.logger.info(f'Configuring device: {device_id}')

        # Check if device exists
        device_table = ds['devices']
        try:
            device = device_table.find_one()
        except:
            device = None

        if device:
            app.logger.error(f'Device already configured: {device}')
            return jsonify({'error': 'Device is already configured.'}), 400

        # Register device
        status, json = api(f'/devices/{device_id}/register_device/')
        if status:
            app.logger.info(f'Registered device: {device_id}')
            device_table.insert(device_id=device_id)
            return jsonify({'success': True})
        else:
            app.logger.error('Could not register device')
            return jsonify(json), 400

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
        app.logger.info('Received a screenshot request')
        data = request.get_json()

        errors = ScreenshotRequest().validate(data)
        if errors:
            app.logger.error(f'Invalid request: {errors}')
            return jsonify(errors), 400

        screenshot_table = ds['screenshots']
        screenshot_table.insert(**data)
        return jsonify({'success': True})

    @app.route('/alive', methods=['GET'])
    def alive():
        return jsonify({'success': True})  # 200 OK

    @app.route('/upload', methods=['GET'])
    def upload_screenshot():
        app.logger.info('Received an upload request')

        screenshot_table = ds['screenshots']
        try:
            device_id = ds['devices'].find_one()['device_id']
        except:  # noqa: E722
            app.logger.error('Device is not configured')
            return jsonify({'error': 'Device is not configured.'}), 400

        if not screenshot_table.find_one():
            app.logger.info('No screenshots to upload')
            return jsonify({'success': True})

        # Get a random single screenshot
        screenshot = dict(choice(screenshot_table.all()))
        id = screenshot.pop('id')
        status, json = api(f'/devices/{device_id}/add_screenshot/',
                           method='POST',
                           data=screenshot)
        if status:
            screenshot_table.delete(id=id)
            app.logger.info(f'Uploaded screenshot: {id}')
            return jsonify({'success': True})
        else:
            app.logger.error(f'Could not upload screenshot: {id} - {json}')
            return jsonify(json), 400

    @app.route('/cleanup', methods=['GET'])
    def cleanup():
        """Delete all screenshots older than 7 days"""
        app.logger.info('Received a cleanup request')
        screenshot_table = ds['screenshots']

        for screenshot in screenshot_table:
            created = screenshot['created']
            # Parse the date as ISO 8601
            created = datetime.datetime.fromisoformat(created)
            if (datetime.datetime.now() - created).days > 7:
                app.logger.info(f'Deleting screenshot: {screenshot["id"]}')
                screenshot_table.delete(screenshot['id'])

        return jsonify({'success': True})

    app.run(port=LOCAL_SERVER_PORT)
