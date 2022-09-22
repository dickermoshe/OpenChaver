from django.urls import path
from creep_app import views

urlpatterns =[
    path('single_service', views.single_service),
]