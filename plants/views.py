from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count
from .models import Plant, WateringRecommendation, ProtectionAdvice
from .forms import PlantForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login


# Регистрация
def register_view(request):
    if request.user.is_authenticated:
        messages.info(request, "Вы уже авторизованы!")
        return redirect('home')

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Вы успешно зарегистрировались!")
            return redirect('login')
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме.")
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
            messages.success(request, f"Добро пожаловать, {user.username}!")
            return redirect('plant_list')
        else:
            messages.error(request, "Неверные учетные данные.")

    return render(request, "registration/login.html")

# Главная страница (для гостей)
def home(request):
    plants = Plant.objects.all().select_related(
        'plant_type',
        'plant_type__category'
    )[:12]

    return render(request, "plants/base.html", {
        "plants": plants,
        "total_plants": Plant.objects.count(),
    })

# Список всех растений пользователя
@login_required
def plant_list(request):
    plants = Plant.objects.filter(owner=request.user)
    plant_count = plants.count()
    plants_by_category = plants.values('plant_type__category__name').annotate(category_count=Count('id'))

    return render(request, 'plants/plant_list.html', {
        'plants': plants,
        'plant_count': plant_count,
        'plants_by_category': plants_by_category,
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
        form = PlantForm(request.POST)
        if form.is_valid():
            plant = form.save(commit=False)
            plant.owner = request.user
            plant.save()
            return redirect('plant_list')
    else:
        form = PlantForm()
    return render(request, 'plants/add_plant.html', {'form': form})