# Django Auth App

A reusable Django authentication package that provides **login, logout, registration, and dashboard functionality** out-of-the-box.  
No need to rewrite authentication logic for every Django project—just install, migrate, and copy templates.

---

## Features

- Login, logout, and registration views  
- Dashboard and home page templates  
- Ready-to-use URLs  
- Easy template customization via management command  
- Works with any Django 4.x+ project  

---

## Installation

Install the package via pip:

```bash
pip install /path/to/django_auth_package
Add to INSTALLED_APPS in your settings.py:

INSTALLED_APPS = [
    ...
    'django_auth_app',
] 
```
Run migrations:
```
python manage.py migrate
```

## Copy Templates

To customize templates, copy them into your project:

python manage.py copy_templates


This will create:
```
myproject/templates/django_auth_app/
├─ login.html
├─ register.html
├─ dashboard.html
└─ home_page.html
```

You can now edit HTML/CSS as needed.
URLs

Include the app URLs in your project’s urls.py:
```
from django.urls import path, include

urlpatterns = [
    path('', include('django_auth_app.urls', namespace='django_auth_app')),
]
```
---
Available URLs:

- /login/ → Login page

- /register/ → Registration page

- /dashboard/ → Dashboard

- / → Home page
---
## Usage

Af---ter installation, your Django project will have fully functional authentication without writing a single line of authentication code. You can customize templates, add CSS, or integrate it with other apps seamlessly.