from django.db import models
from django.utils.html import mark_safe
# Create your models here.

class Image(models.Model):
    image = models.ImageField(upload_to='images/')
    is_nsfw = models.BooleanField(default=None, null=True, blank=True)

    keep = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.image.name
    
    def image_tag(self):
        return mark_safe('<img src="/media/%s" width="300" />' % (self.image))

    class Meta:
        ordering = ['-created']
    
