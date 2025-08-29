from django.urls import path
from . import views

urlpatterns = [
    path('fetch-upload/', views.fetch_and_upload_file, name='fetch_and_upload_file'),
    path('health/', views.health_check, name='health_check'),
]