import requests
import os
from django.utils import timezone
from .models import Weather


#Расчёт полива по факторам: тип растения, температура, влажность, осадки
def simple_watering(plant, temp, hum, precip):
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
        note = (
            f"На улице жарко ({temp}°C). "
            f"Почва быстро теряет влагу, поэтому полив следует увеличить. "
            f"Рекомендуется внести около {water} л/м², желательно утром или вечером, "
            f"чтобы снизить испарение и избежать перегрева корней."
        )
    elif temp < 15:
        note = (
            f"Погода прохладная ({temp}°C). "
            f"Испарение воды замедлено, а потребность растения во влаге снижена. "
            f"Достаточно умеренного полива — примерно {water} л/м², "
            f"чтобы избежать переувлажнения почвы."
        )
    elif precip > 0:
        note = (
            f"Недавно прошли осадки ({precip} мм). "
            f"Почва уже получила часть необходимой влаги, "
            f"поэтому норму полива можно сократить. "
            f"Рекомендуемое количество воды — около {water} л/м²."
        )
    else:
        note = (
            f"Погодные условия благоприятные для роста растения. "
            f"Температура и влажность находятся в норме, осадки отсутствуют. "
            f"Рекомендуется стандартный режим полива — примерно {water} л/м²."
        )

    return water, note


# Проверка и нормализация названия города через API
def validate_city_name(city_name):
    # проверяем что город не пустой
    if not city_name or not city_name.strip():
        return None

    api_key = os.environ.get('OPENWEATHER_API_KEY')
    if not api_key:
        return city_name.strip()

    try:
        response = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&lang=ru",
            timeout=3
        )

        # если город найден, возвращаем название
        if response.status_code == 200:
            data = response.json()
            return data['name']
        return None

    except (requests.RequestException, KeyError):

        return None


# Получение данных о погоде через API
def get_weather_data(city):
    today = timezone.now().date()

    # проверяем кэш в БД
    cached_weather = Weather.objects.filter(
        city=city,
        date=today
    ).first()

    if cached_weather:
        # берем координаты из БД или по умолчанию
        lat = cached_weather.latitude or 55.7558
        lon = cached_weather.longitude or 37.6173

        return {
            'temperature': cached_weather.temperature,
            'humidity': cached_weather.humidity,
            'precipitation': cached_weather.precipitation,
            'description': cached_weather.description or "Ясная погода",
            'lat': lat,
            'lon': lon,
            'from_cache': True,
            'has_data': True
        }

    # API запрос (если нет в кэше)
    try:
        api_key = os.environ.get('OPENWEATHER_API_KEY')
        data = requests.get(
            f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru",
            timeout=5
        ).json()

        lat = data['coord']['lat']
        lon = data['coord']['lon']
        temp = round(data['main']['temp'], 1)
        hum = data['main']['humidity']
        precip = data.get('rain', {}).get('1h', 0) or data.get('snow', {}).get('1h', 0) or 0
        description = data['weather'][0]['description']

        # сохраняем ВСЁ в БД
        Weather.objects.create(
            city=city,
            date=today,
            temperature=temp,
            humidity=hum,
            precipitation=precip,
            description=description,
            latitude=lat,
            longitude=lon
        )

        return {
            'temperature': temp,
            'humidity': hum,
            'precipitation': precip,
            'description': description,
            'lat': lat,
            'lon': lon,
            'from_cache': False,
            'has_data': True
        }

    except Exception as e:
        # ищем последние доступные данные для этого города
        last_weather = Weather.objects.filter(city=city).order_by('-date').first()
        if last_weather:
            lat = last_weather.latitude or 55.7558
            lon = last_weather.longitude or 37.6173

            return {
                'temperature': last_weather.temperature,
                'humidity': last_weather.humidity,
                'precipitation': last_weather.precipitation,
                'description': last_weather.description or "Ясная погода",
                'lat': lat,
                'lon': lon,
                'from_cache': True,
                'has_data': True,
                'outdated': True
            }

        # если ничего нет, то данные по умолчанию
        return {
            'temperature': 20,
            'humidity': 50,
            'precipitation': 0,
            'description': "Нет данных",
            'lat': 55.7558,
            'lon': 37.6173,
            'from_cache': False,
            'has_data': False
        }