from django.urls import path
from . import auth_views

app_name = "django_auth_app"

urlpatterns = [
    path('', auth_views.home, name='home'),
    path('login/', auth_views.user_login, name='login'),
    path('logout/', auth_views.user_logout, name='logout'),
    path('register/', auth_views.register, name='register'),
    path('dashboard/', auth_views.dashboard, name='dashboard'),
]
