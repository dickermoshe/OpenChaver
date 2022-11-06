from rest_framework.viewsets import ModelViewSet

from .models import Screenshot
from .serializer import ScreenshotSerializer

class ScreenshotViewSet(ModelViewSet):
    queryset = Screenshot.objects.all()
    serializer_class = ScreenshotSerializer


