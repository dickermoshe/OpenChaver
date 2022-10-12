from flask import Flask, jsonify, request
from marshmallow import Schema, fields

app = Flask(__name__)

class ConfigureRequest(Schema):
    user_id = fields.UUID(required=True)
    device_id = fields.UUID(required=True)

@app.route('/configure', methods=['POST'])
def configure():
    data = request.get_json()
    
    errors = ConfigureRequest().validate(data)
    if errors:
        return jsonify(errors), 400
    
    from .models import ConfigurationModel
    success = ConfigurationModel().set(data['user_id'],data['device_id'])

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

def server():
    app.run()