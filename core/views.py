from rest_framework.viewsets import ModelViewSet
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta

from .models import Screenshot
from .serializer import ScreenshotSerializer

class ScreenshotViewSet(ModelViewSet):
    queryset = Screenshot.objects.all()
    serializer_class = ScreenshotSerializer
    parser_classes = (MultiPartParser ,FormParser)

    def create(self, request, *args, **kwargs):
        # Create a new screenshot
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        # Run the screenshot through the post_process
        screenshot = Screenshot.objects.get(id=serializer.data['id'])
        screenshot = screenshot.post_process()
        
        if screenshot:
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['post'],serializer_class=None)
    def clean(self, request):
        # Delete screenshots older than 7 days
        screenshots = Screenshot.objects.filter(timestamp__lte=timezone.now() - timedelta(days=7))
        for screenshot in screenshots:
            if screenshot.image_file:
                screenshot.image_file.delete()
            screenshot.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



