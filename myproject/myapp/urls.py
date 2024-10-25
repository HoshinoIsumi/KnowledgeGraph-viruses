from django.urls import path
from .views import virus_list, virus_detail

urlpatterns = [
    path('viruses/', virus_list, name='virus_list'),
    path('viruses/<int:virus_id>/', virus_detail, name='virus_detail'),
]
