from django.urls import path
from creep_app import views

urlpatterns =[
    path('clean', views.clean_service),
    path('detect', views.detect_service),
    path('snap_active', views.snap_active_window_service),
    path('snap_random', views.snap_random_window_service),
]