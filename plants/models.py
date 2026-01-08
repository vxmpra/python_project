from django.db import models
from django.contrib.auth.models import User


""" Модель категории растения """
class PlantCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


""" Модель типа растения """
class PlantType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(
        PlantCategory,
        on_delete=models.CASCADE,
        related_name="plant_types"
    )
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


""" Модель растения """
class Plant(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    plant_type = models.ForeignKey(PlantType, on_delete=models.CASCADE)
    city = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.plant_type.name} ({self.city})"


""" Модель рекомендаций по поливу """
class WateringRecommendation(models.Model):
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)
    date = models.DateField()
    water_amount = models.FloatField(help_text="Количество воды в литрах")
    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.plant.name} - {self.date}"


""" Модель рекомендаций по защите растения """
class ProtectionAdvice(models.Model):
    plant_type = models.ForeignKey(PlantType, on_delete=models.CASCADE)
    pest_or_disease = models.CharField(max_length=100)
    recommendation = models.TextField()

    def __str__(self):
        return f"{self.plant_type.name} - {self.pest_or_disease}"


""" Модель погодных данных """
class Weather(models.Model):
    city = models.CharField(max_length=100)
    date = models.DateField()
    temperature = models.FloatField(help_text="Температура в °C")
    humidity = models.FloatField(help_text="Влажность в %")
    precipitation = models.FloatField(help_text="Осадки в мм")

    def __str__(self):
        return f"{self.city} - {self.date}"