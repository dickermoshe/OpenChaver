def server():
    import time
    from .db import get_configuration_db

    configdb = get_configuration_db()
    if configdb.is_configured:
        time.sleep(60)
        return
    
    from flask import Flask, jsonify, request
    from marshmallow import Schema, fields
    import requests
    from .const import API_BASE_URL, LOCAL_SERVER_PORT

    app = Flask(__name__)

    class ConfigureRequest(Schema):
        device_id = fields.UUID(required=True)
    
    @app.route('/configure', methods=['POST'])
    def configure():
        data = request.get_json()
        
        errors = ConfigureRequest().validate(data)
        if errors:
            return jsonify(errors), 400
        try:
            r = requests.post(f"{API_BASE_URL}devices/register_device/",json=data,verify=False)
            if r.status_code != 200:
                raise Exception("Failed to register device")
        except:
            return jsonify({"error": "Failed to register device"}), 500

        
        success = configdb.save_device_id(data['device_id'])

        if success:
            return jsonify({'success': True})
        else:
            jsonify({"error": "Current device already configured."}), 500
    
    app.run(port=LOCAL_SERVER_PORT)