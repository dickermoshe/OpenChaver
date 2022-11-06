from django.urls import path

from rest_framework import routers
from .views import ScreenshotViewSet

router = routers.DefaultRouter()
router.register(r'screenshots', ScreenshotViewSet)

urlpatterns = router.urls
