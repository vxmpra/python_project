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
            super().__init__(*args, **kwargs)
            self.fields['plant_type'].queryset = PlantType.objects.all().order_by('name')

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
                return city