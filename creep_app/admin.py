from django.contrib import admin

# Register your models here.
from .models import Image
class ImageAdmin(admin.ModelAdmin):
    list_display = ['image_tag', 'is_nsfw', 'created', 'updated']
    fields = ['image_tag']
    readonly_fields = ['image_tag']

admin.site.register(Image, ImageAdmin)
