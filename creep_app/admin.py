from django.contrib import admin

# Register your models here.
from .models import Screenshot

def reset_is_nsfw(modeladmin, request, queryset):
    queryset.update(is_nsfw=None)

class ImageAdmin(admin.ModelAdmin):
    list_display = ['image_tag', 'is_nsfw', 'title' ,'created', 'updated']
    fields = ['image_tag', 'is_nsfw', 'title' ,'image','keep']
    readonly_fields = ['image_tag']

    list_filter = ['is_nsfw',]
    search_fields = ['title', 'exec_name']
    actions = [reset_is_nsfw]

admin.site.register(Screenshot, ImageAdmin)



