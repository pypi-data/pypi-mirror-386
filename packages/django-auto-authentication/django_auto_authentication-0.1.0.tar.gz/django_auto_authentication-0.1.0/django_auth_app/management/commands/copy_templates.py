import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
import django_auth_app

class Command(BaseCommand):
    help = "Copy django_auth_app templates into the project templates folder for customization"

    def handle(self, *args, **kwargs):
        # Source templates folder inside the app
        src = os.path.join(os.path.dirname(django_auth_app.__file__), 'templates', 'django_auth_app')

        if not os.path.exists(src):
            self.stdout.write(self.style.ERROR(f"Source templates folder not found: {src}"))
            return

        # Destination templates folder in the project
        dest = os.path.join(settings.BASE_DIR, 'templates', 'django_auth_app')

        if not os.path.exists(dest):
            os.makedirs(dest)

        # Copy files
        for filename in os.listdir(src):
            full_file_name = os.path.join(src, filename)
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, dest)

        self.stdout.write(self.style.SUCCESS(f"Templates copied to {dest} successfully!"))
