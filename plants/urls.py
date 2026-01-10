from django.urls import path
from . import views

urlpatterns = [
    path('', views.plant_list, name='plant_list'),
    path('plant/<int:pk>/', views.plant_detail, name='plant_detail'),
    path('add/', views.add_plant, name='add_plant'),
    path("plant/<int:pk>/protection/", views.protection_detail, name="protection_detail"),
    path('plant/<int:pk>/watering/', views.watering_detail, name='watering_detail'),
]