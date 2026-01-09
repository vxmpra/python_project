from django.contrib import admin
from plants import views
from plants.views import home
from django.urls import path, include
from django.contrib.auth import views as auth_views
from plants import views as plant_views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('plants/', include('plants.urls')),
    path('logout/', plant_views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html', next_page='plant_list'), name='login'),
]
