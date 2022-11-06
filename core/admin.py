from django.contrib import admin

# Register your models here.
from .models import Screenshot
# IMport the html template
from django.utils.html import format_html

class ScreenshotAdmin(admin.ModelAdmin):
    list_display = ('title', 'excutable_name', 'screenshot_type','is_nsfw', 'is_profane', 'timestamp')
    search_fields = ('title', 'excutable_name')
    list_filter = ('screenshot_type', 'is_nsfw', 'is_profane', 'timestamp')
    
    # Show the image in the admin from the base64 string
    readonly_fields = ('image',)

    def image(self, obj):

        if obj.base64_image:
            return format_html('<img src="data:image/png;base64,{}" style="max-width: 300px; max-height: 300px;"/>', obj.base64_image)
        return None



admin.site.register(Screenshot, ScreenshotAdmin)
