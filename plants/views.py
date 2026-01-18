from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Plant, WateringRecommendation, ProtectionAdvice, PlantType
from .forms import PlantForm
from .utils import simple_watering, get_weather_data, get_5day_forecast


# Регистрация
def register_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()

    return render(request, "registration/register.html", {"form": form})


# Вход
def login_view(request):
    if request.user.is_authenticated:
        return redirect('plant_list')

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('plant_list')
    else:
        form = AuthenticationForm()

    return render(request, "registration/login.html", {'form': form})


# Выход
def logout_view(request):
    logout(request)
    return redirect('home')


# Удаление растения
@login_required
def delete_plant(request, pk):
    plant = get_object_or_404(Plant, pk=pk, owner=request.user)

    if request.method == 'POST':
        plant.delete()
        return redirect('plant_list')

    return redirect('plant_list')


# Главная страница (для гостей)
def home(request):
    plant_types = PlantType.objects.select_related('category').only(
        'name', 'category__name'
    ).order_by('name')[:30]

    stats = PlantType.objects.aggregate(
        total_plants=Count('id'),
        total_categories=Count('category', distinct=True)
    )

    return render(request, "plants/base.html", {
        "plant_types": plant_types,
        "total_plants": stats['total_plants'],
        "total_categories": stats['total_categories'],
    })


# Список всех растений пользователя
@login_required
def plant_list(request):
    plants = Plant.objects.filter(
        owner=request.user
    ).select_related(
        'plant_type__category'
    ).order_by(
        'plant_type__category__name',
        'plant_type__name',
        'city'
    )

    plant_count = plants.count()

    return render(request, 'plants/plant_list.html', {
        'plants': plants,
        'plant_count': plant_count,
    })


# Детали растения
@login_required
def plant_detail(request, pk):
    plant = get_object_or_404(
        Plant.objects.select_related('plant_type__category', 'owner'),
        pk=pk,
        owner=request.user
    )

    waterings = WateringRecommendation.objects.filter(
        plant=plant
    ).order_by('-date')[:3]

    advices = ProtectionAdvice.objects.filter(
        plant_type=plant.plant_type
    ).order_by('pest_or_disease')

    advices_count = advices.count()

    return render(request, 'plants/plant_detail.html', {
        'plant': plant,
        'waterings': waterings,
        'advices': advices,
        'advices_count': advices_count,
    })


# Добавление нового растения
@login_required
def add_plant(request):
    if request.method == 'POST':
        form = PlantForm(request.POST, user=request.user)
        if form.is_valid():
            plant = form.save(commit=False)
            plant.owner = request.user
            plant.save()
            return redirect('plant_list')
    else:
        form = PlantForm(user=request.user)

    return render(request, 'plants/add_plant.html', {'form': form})


# Рекомендации по защите растения от вредителей и болезней
@login_required
def protection_detail(request, pk):
    plant = get_object_or_404(
        Plant.objects.select_related('plant_type'),
        pk=pk,
        owner=request.user
    )

    protection_list = ProtectionAdvice.objects.filter(
        plant_type=plant.plant_type
    )

    return render(request, "plants/protection_detail.html", {
        "plant": plant,
        "protection_list": protection_list
    })


# Рекомендации по поливу
@login_required
def watering_detail(request, pk):
    plant = get_object_or_404(
        Plant.objects.select_related('plant_type'),
        pk=pk,
        owner=request.user
    )

    today = timezone.now().date()

    # Текущая погода
    weather_data = get_weather_data(plant.city)

    if not weather_data.get('has_data', False):
        return render(request, "plants/watering_detail.html", {
            "plant": plant,
            "error": "Не удалось получить данные о погоде. Попробуйте позже."
        })

    # Определение сезона
    month = timezone.now().month
    season_number = (month % 12) // 3
    seasons = ["зима", "весна", "лето", "осень"]
    season_name = seasons[season_number]

    # Текущая рекомендация
    water, note = simple_watering(
        plant,
        weather_data['temperature'],
        weather_data['humidity'],
        weather_data['precipitation']
    )

    # Сохранение рекомендации в БД, если её еще нет
    if weather_data['temperature'] is not None:
        exists = WateringRecommendation.objects.filter(
            plant=plant,
            date=today
        ).exists()
        if not exists:
            WateringRecommendation.objects.create(
                plant=plant,
                date=today,
                water_amount=water,
                note=note[:100]
            )

    # 5-дневный прогноз
    forecast_data = get_5day_forecast(plant.city)
    forecast = []

    for day in forecast_data:
        water_forecast, recommendation = simple_watering(
            plant,
            day['avg_temp'],
            50,
            day['total_rain']
        )

        day['water_amount'] = water_forecast
        day['recommendation'] = recommendation
        forecast.append(day)

    return render(request, "plants/watering_detail.html", {
        "plant": plant,
        "temperature": weather_data['temperature'],
        "humidity": weather_data['humidity'],
        "precipitation": weather_data['precipitation'],
        "weather_description": weather_data['description'],
        "season": season_name,
        "lat": weather_data['lat'],
        "lon": weather_data['lon'],
        "water_per_sqm": water,
        "watering_note": note,
        "forecast": forecast,
    })