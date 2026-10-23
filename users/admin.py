from django.contrib import admin
from .models import User

admin.site.register(User, list_display=("id", "name", "email", "role", "is_active"))
