from django.http import HttpResponse


from creep_app.models import Screenshot

def snap_active_window_service(request):
    """Snap Active Window Service"""
    Screenshot.snap_active()
    return HttpResponse("OK")

def snap_random_window_service(request):
    """Snap Random Window Service"""
    Screenshot.snap_random()
    return HttpResponse("OK")

def detect_service(request):
    """Detect Service"""
    Screenshot.run_detections()
    return HttpResponse("OK")

def clean_service(request):
    """Clean Service"""
    Screenshot.clean()
    return HttpResponse("OK")