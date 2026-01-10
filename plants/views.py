import os
import requests
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count
from .models import Plant, WateringRecommendation, ProtectionAdvice, PlantType, PlantCategory, Weather
from .forms import PlantForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout


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
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('plant_list')

    return render(request, "registration/login.html")

# Выход
def logout_view(request):
    logout(request)
    return redirect('home')

# Главная страница (для гостей)
def home(request):
    plant_types = PlantType.objects.all().select_related('category')

    return render(request, "plants/base.html", {
        "plant_types": plant_types,
        "total_plants": PlantType.objects.count(),
        "total_categories": PlantCategory.objects.count(),
    })

# Список всех растений пользователя
@login_required
def plant_list(request):
    plants = Plant.objects.filter(owner=request.user).select_related(
        'plant_type',
        'plant_type__category'
    )
    plant_count = plants.count()

    plants_by_category_dict = {}
    for plant in plants:
        category_name = plant.plant_type.category.name
        if category_name not in plants_by_category_dict:
            plants_by_category_dict[category_name] = []
        plants_by_category_dict[category_name].append(plant)

    plants_by_category = plants.values('plant_type__category__name').annotate(category_count=Count('id'))

    return render(request, 'plants/plant_list.html', {
        'plants': plants,
        'plant_count': plant_count,
        'plants_by_category': plants_by_category,
        'plants_by_category_dict': plants_by_category_dict,
    })

# Детали растения
@login_required
def plant_detail(request, pk):
    plant = get_object_or_404(Plant, pk=pk, owner=request.user)
    waterings = WateringRecommendation.objects.filter(plant=plant)
    advices = ProtectionAdvice.objects.filter(plant_type=plant.plant_type)
    return render(request, 'plants/plant_detail.html', {
        'plant': plant,
        'waterings': waterings,
        'advices': advices
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
    plant = get_object_or_404(Plant, pk=pk, owner=request.user)

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
    plant = get_object_or_404(Plant, pk=pk, owner=request.user)
    today = timezone.now().date()

    # данные из кэша
    cached_weather = Weather.objects.filter(city=plant.city, date=today).first()

    lat, lon = 55.7558, 37.6173

    if cached_weather:
        temp = cached_weather.temperature
        hum = cached_weather.humidity
        precip = cached_weather.precipitation
        weather_description = cached_weather.description or "Ясная погода"

        # координаты для карты
        try:
            coord_data = requests.get(
                f"https://api.openweathermap.org/geo/1.0/direct?q={plant.city}&limit=1&appid={os.environ.get('OPENWEATHER_API_KEY')}",
                timeout=2
            ).json()
            if coord_data:
                lat, lon = coord_data[0]['lat'], coord_data[0]['lon']
        except:
            pass
    else:
        # если нет кэша, запрашиваем данные у API
        try:
            data = requests.get(
                f"https://api.openweathermap.org/data/2.5/weather?q={plant.city}&appid={os.environ.get('OPENWEATHER_API_KEY')}&units=metric&lang=ru",
                timeout=5
            ).json()

            lat, lon = data['coord']['lat'], data['coord']['lon']
            temp = round(data['main']['temp'], 1)
            hum = data['main']['humidity']
            precip = data.get('rain', {}).get('1h', 0) or data.get('snow', {}).get('1h', 0) or 0
            weather_description = data['weather'][0]['description']

            # сохраняем все данные в кэш
            Weather.objects.create(
                city=plant.city,
                date=today,
                temperature=temp,
                humidity=hum,
                precipitation=precip,
                description=weather_description
            )

        except Exception as e:
            print(f"Ошибка получения погоды: {e}")
            last_weather = Weather.objects.filter(city=plant.city).order_by('-date').first()
            if last_weather:
                temp = last_weather.temperature
                hum = last_weather.humidity
                precip = last_weather.precipitation
                weather_description = last_weather.description or "Ясная погода"
            else:
                return render(request, "plants/watering_detail.html", {
                    "plant": plant,
                    "map_url": f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&z=10&l=map&size=600,400",
                    "watering_note": "Не удалось получить данные о погоде",
                })

    water, note = simple_watering(plant, temp, hum, precip)

    already_exists = WateringRecommendation.objects.filter(
        plant=plant,
        date=today
    ).exists()

    if not already_exists:
        WateringRecommendation.objects.create(
            plant=plant,
            date=today,
            water_amount=water,
            note=note[:100]
        )

    return render(request, "plants/watering_detail.html", {
        "plant": plant,
        "temperature": temp,
        "humidity": hum,
        "precipitation": precip,
        "weather_description": weather_description,
        "season": ["зима", "весна", "лето", "осень"][(timezone.now().month % 12) // 3],
        "map_url": f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&z=10&l=map&size=600,400",
        "water_per_sqm": water,
        "watering_note": note,
    })

# Расчет полива (по факторам: тип растения, температура, влажность, осадки)
def simple_watering(plant, temp, hum, precip):

    # запреты на полив
    if temp < 5:
        return 0, f"Слишком холодно ({temp}°C) - полив не требуется"
    if precip > 5:
        return 0, f"Сильный дождь ({precip} мм) - полив не нужен"

    # тип растения
    base_norms = {
        "Овощ": 2.0,
        "Зелень": 1.5,
        "Дерево": 5.0,
        "Цветок": 0.5,
    }
    base = base_norms.get(plant.plant_type.name, 1.0)

    # температура: чем жарче тем больше полив
    tf = 1.5 if temp > 30 else 1.3 if temp > 25 else 0.7 if temp < 15 else 1.0

    # влажность: чем суше тем больше полив
    hf = 0.7 if hum > 70 else 1.3 if hum < 30 else 1.0

    # осадки: дождь уменьшает полив
    rf = 0.3 if precip > 2 else 0.7 if precip > 0 else 1.0

    # расчет
    water = round(max(0.1, base * tf * hf * rf), 1)


    # рекомендации
    if temp > 30:
        note = f"Жарко: требуется {water} л/м² (полив увеличен)"
    elif temp < 15:
        note = f"Прохладно: требуется {water} л/м² (полив уменьшен)"
    elif precip > 0:
        note = f"Дождь: требуется {water} л/м² (полив уменьшен)"
    else:
        note = f"Нормально: требуется {water} л/м² (стандартный полив)"

    return water, note