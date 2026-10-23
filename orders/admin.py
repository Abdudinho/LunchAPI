from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


admin.site.register(Order, list_display=("id", "user", "restaurant", "status", "total_amount"),
                    inlines=[OrderItemInline])
