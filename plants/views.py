import os
import requests
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count
from .models import Plant, WateringRecommendation, ProtectionAdvice, PlantType, PlantCategory
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
    API_KEY = os.environ.get('OPENWEATHER_API_KEY')

    context = {"plant": plant, "map_url": ""}

    try:
        data = requests.get(
            f"http://api.openweathermap.org/data/2.5/weather?q={plant.city}&appid={API_KEY}&units=metric&lang=ru",
            timeout=5
        ).json()

        lat, lon = data['coord']['lat'], data['coord']['lon']
        context.update({
            "temperature": round(data['main']['temp'], 1),
            "humidity": data['main']['humidity'],
            "precipitation": data.get('rain', {}).get('1h', 0),
            "weather_description": data['weather'][0]['description'],
            "season": ["зима", "весна", "лето", "осень"][(timezone.now().month % 12) // 3],
            "lat": lat, "lon": lon,
            "map_url": f"https://static-maps.yandex.ru/1.x/?ll={lon},{lat}&z=10&l=map&pt={lon},{lat},pm2rdm&size=600,400",
        })
    except Exception as e:
        print(f"Ошибка: {e}")
        context.update({
            "temperature": "—", "humidity": "—", "precipitation": "—",
            "weather_description": "Нет данных", "season": "—",
            "lat": 55.7558, "lon": 37.6173,
            "map_url": "https://static-maps.yandex.ru/1.x/?ll=37.6173,55.7558&z=10&l=map&pt=37.6173,55.7558,pm2rdm&size=600,400",
        })

    return render(request, "plants/watering_detail.html", context)