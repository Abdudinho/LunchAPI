from django.contrib import admin
from .models import MenuItem, Restaurant

admin.site.register(Restaurant, list_display=("id", "name", "owner", "is_active"))
admin.site.register(MenuItem, list_display=("id", "name", "restaurant", "price", "is_available"))
