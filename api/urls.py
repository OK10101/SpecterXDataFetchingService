from django.urls import path
from . import views

urlpatterns = [
    path('fetch-upload/', views.fetch_and_upload_file, name='fetch_and_upload_file'),
    path('policies/', views.get_policies, name='get_policies'),
    path('files/<str:file_id>/policy/', views.set_file_policy, name='set_file_policy'),
    path('share/', views.share_file, name='share_file'),
    path('files/multiple_link/', views.get_multiple_link, name='get_multiple_link'),
    path('health/', views.health_check, name='health_check'),
]