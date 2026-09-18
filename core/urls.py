from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/create-room/', views.create_room, name='create_room'),
    path('api/signal/<str:room_id>/', views.signal, name='signal'),
    path('manifest.json', views.manifest, name='manifest'),
    path('sw.js', views.sw, name='sw'),
]