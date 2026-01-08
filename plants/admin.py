from django.contrib import admin
from .models import PlantCategory, PlantType, Plant, WateringRecommendation, ProtectionAdvice, Weather

@admin.register(PlantCategory)
class PlantCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(PlantType)
class PlantTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ('plant_type', 'city', 'owner')
    list_filter = ('plant_type__category', 'city')
    search_fields = ('plant_type__name', 'city', 'owner__username')

@admin.register(WateringRecommendation)
class WateringRecommendationAdmin(admin.ModelAdmin):
    list_display = ('plant', 'date', 'water_amount')
    list_filter = ('date',)
    search_fields = ('plant__plant_type__name', 'note')

@admin.register(ProtectionAdvice)
class ProtectionAdviceAdmin(admin.ModelAdmin):
    list_display = ('plant_type', 'pest_or_disease')
    search_fields = ('plant_type__name', 'pest_or_disease')

@admin.register(Weather)
class WeatherAdmin(admin.ModelAdmin):
    list_display = ('city', 'date', 'temperature', 'humidity', 'precipitation')
    list_filter = ('city', 'date')
    search_fields = ('city',)