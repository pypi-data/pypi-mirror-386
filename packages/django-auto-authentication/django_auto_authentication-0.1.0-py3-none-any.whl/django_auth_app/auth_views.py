from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

# Register view
def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        User.objects.create_user(username=username, email=email, password=password)
        return redirect("django_auth_app:login")
    return render(request, "django_auth_app/register.html")

# Login view
def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("django_auth_app:dashboard")
    return render(request, "django_auth_app/login.html")

# Logout view
def user_logout(request):
    logout(request)
    return redirect("django_auth_app:login")

# Dashboard view
def dashboard(request):
    return render(request, "django_auth_app/dashboard.html")

# Home page
def home(request):
    return render(request, "django_auth_app/home_page.html")
