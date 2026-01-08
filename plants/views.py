from django.shortcuts import render, get_object_or_404, redirect
from .models import Plant, WateringRecommendation, ProtectionAdvice
from .forms import PlantForm
from django.contrib.auth.decorators import login_required


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
    return render(request, 'plants/plant_list.html', {'plants': plants})

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

