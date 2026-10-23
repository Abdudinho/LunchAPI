from django.contrib import admin
from .models import Payment

admin.site.register(Payment, list_display=("id", "order", "amount", "payment_method", "status"))
