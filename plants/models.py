from django.db import models
from django.contrib.auth.models import User


""" Модель категории растения """
class PlantCategory(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название")

    class Meta:
        verbose_name = "Категория растения"
        verbose_name_plural = "Категории растений"

    def __str__(self):
        return self.name


""" Модель типа растения """
class PlantType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название")
    category = models.ForeignKey(
        PlantCategory,
        on_delete=models.CASCADE,
        related_name="plant_types",
        verbose_name="Категория"
    )
    description = models.TextField(blank=True, verbose_name="Описание")
    image = models.ImageField(
        upload_to='plant_types/',
        blank=True,
        null=True,
        verbose_name="Фото растения"
    )

    class Meta:
        verbose_name = "Тип растения"
        verbose_name_plural = "Типы растений"

    def __str__(self):
        return self.name


""" Модель растения """
class Plant(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    plant_type = models.ForeignKey(PlantType, on_delete=models.CASCADE, verbose_name="Тип растения")
    city = models.CharField(max_length=100, verbose_name="Город")

    class Meta:
        verbose_name = "Растение"
        verbose_name_plural = "Растения"

    def __str__(self):
        return f"{self.plant_type.name} ({self.city})"


""" Модель рекомендаций по поливу """
class WateringRecommendation(models.Model):
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, verbose_name="Растение")
    date = models.DateField(verbose_name="Дата")
    water_amount = models.FloatField(help_text="Количество воды в литрах",verbose_name="Количество воды")
    note = models.TextField(blank=True, verbose_name="Рекомендация")

    class Meta:
        verbose_name = "Рекомендация по поливу"
        verbose_name_plural = "Рекомендации по поливу"

    def __str__(self):
        return f"{self.plant.plant_type.name} - {self.date}"


""" Модель рекомендаций по защите растения """
class ProtectionAdvice(models.Model):
    plant_type = models.ForeignKey(PlantType, on_delete=models.CASCADE, verbose_name="Тип растения")
    pest_or_disease = models.CharField(max_length=100, verbose_name="Вредитель/Болезнь")
    recommendation = models.TextField(verbose_name="Рекомендация")

    class Meta:
        verbose_name = "Совет по защите"
        verbose_name_plural = "Советы по защите"

    def __str__(self):
        return f"{self.plant_type.name} - {self.pest_or_disease}"


""" Модель погодных данных """
class Weather(models.Model):
    city = models.CharField(max_length=100, verbose_name="Город")
    date = models.DateField(verbose_name="Дата")
    temperature = models.FloatField(help_text="Температура в °C", verbose_name="Температура")
    humidity = models.FloatField(help_text="Влажность в %", verbose_name="Влажность")
    precipitation = models.FloatField(help_text="Осадки в мм", verbose_name="Осадки")
    description = models.CharField(max_length=100, blank=True, verbose_name="Описание погоды")
    latitude = models.FloatField(null=True, blank=True, verbose_name="Широта")
    longitude = models.FloatField(null=True, blank=True, verbose_name="Долгота")

    class Meta:
        verbose_name = "Погодные данные"
        verbose_name_plural = "Погодные данные"

    def __str__(self):
        return f"{self.city} - {self.date}"