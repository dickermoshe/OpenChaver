from django.http import HttpResponse
from creep_app.models import Screenshot

def snap_active_window_service(request):
    """Snap Active Window Service"""
    Screenshot.snap_service(
        0,
        True,
        5,
        60,
        False
    )
    return HttpResponse("OK")

def snap_random_window_service(request):
    """Snap Random Window Service"""
    Screenshot.snap_service(
        [30,300],
        False,
        False,
        10,
        False
    )
    return HttpResponse("OK")

def detect_service(request):
    """Detect Service"""
    Screenshot.run_detections()
    return HttpResponse("OK")

def clean_service(request):
    """Clean Service"""
    Screenshot.clean()
    return HttpResponse("OK")