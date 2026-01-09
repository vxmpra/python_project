import requests
import os
from django import forms
from .models import Plant, PlantType


class PlantForm(forms.ModelForm):
    class Meta:
        model = Plant
        fields = ['plant_type', 'city']
        widgets = {
            'plant_type': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Москва'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['plant_type'].queryset = PlantType.objects.all().order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        plant_type = cleaned_data.get('plant_type')
        city = cleaned_data.get('city')

        if self.user and plant_type and city:
            city_normalized = city.strip()

            duplicate = Plant.objects.filter(
                owner=self.user,
                plant_type=plant_type,
                city__iexact=city_normalized
            ).exists()

            if duplicate:
                raise forms.ValidationError(
                    f'У вас уже есть в каталоге "{plant_type.name}" в городе {city_normalized}'
                )

        return cleaned_data

    def clean_city(self):
        city = self.cleaned_data.get('city', '').strip()

        if not city:
            raise forms.ValidationError("Введите название города")

        API_KEY = os.environ.get('OPENWEATHER_API_KEY')
        if not API_KEY:
            return city

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&lang=ru"

        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                return data['name']
            else:
                raise forms.ValidationError(f"Город '{city}' не найден")
        except:
            raise forms.ValidationError("Не удалось найти город")