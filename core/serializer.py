from rest_framework import serializers

from .models import Screenshot

class ScreenshotSerializer(serializers.ModelSerializer):

    class Meta:
        model = Screenshot
        fields = '__all__'
        read_only_fields = ('id', 'timestamp', 'is_nsfw', 'is_profane', 'nsfw_detection',)
