from django.contrib import admin

# Register your models here.
from .models import Screenshot
class ImageAdmin(admin.ModelAdmin):
    list_display = ['image_tag', 'is_nsfw', 'title' ,'created', 'updated']
    fields = ['image_tag']
    readonly_fields = ['image_tag']

    list_filter = ['is_nsfw',]
    search_fields = ['title', 'exec_name']

admin.site.register(Screenshot, ImageAdmin)
