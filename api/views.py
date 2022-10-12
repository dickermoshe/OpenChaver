from typing import Type
import requests
from django.conf  import settings

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.decorators import api_view

from .service import run_services
from .models import Configuration

class ConfigureSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    device_id = serializers.UUIDField()

class DeConfigureSerializer(serializers.Serializer):
    code = serializers.UUIDField()


@api_view(["POST"],)
def configure(request: Request):
    serializer = ConfigureSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        r = requests.post(settings.API_URL + '/devices/configure', data=serializer.validated_data,verify=False)
        if r.status_code == 200:
            
            if Configuration.is_configurated:
                return Response({'message': 'Device already configurated'}, status=400)
            
            config : Configuration = Configuration.get_solo()
            config.user_id = serializer.validated_data['user_id']
            config.device_id = serializer.validated_data['device_id']
            config.save()
            
            return Response(status=200, data=r.json())
        else:
            return Response(status=400, data=r.json())

    except:
        return Response(status=500, data={'error': 'Could not connect to Internet'})

@api_view(["POST"],)
def deconfigure(request: Request):
    serializer = DeConfigureSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        r = requests.post(settings.API_URL + '/devices/deconfigure', data=serializer.validated_data,verify=False)
        if r.status_code == 200:
            
            if not Configuration.is_configurated:
                return Response({'message': 'Device is not Configured'}, status=400)
            
            Configuration.get_solo().delete()

            return Response(status=200, data=r.json())
        else:
            return Response(status=400, data=r.json())

    except:
        return Response(status=500, data={'error': 'Could not connect to Internet'})

@api_view(["GET"],)
def monitor(request: Request):
    run_services()
    return Response(status=200)