from django.contrib import admin

# Register your models here.
from .models import Screenshot


class ScreenshotAdmin(admin.ModelAdmin):
    list_display = ('title', 'excutable_name', 'screenshot_type','is_nsfw', 'is_profane', 'timestamp')
    search_fields = ('title', 'excutable_name')
    list_filter = ('screenshot_type', 'is_nsfw', 'is_profane', 'timestamp')

admin.site.register(Screenshot, ScreenshotAdmin)
