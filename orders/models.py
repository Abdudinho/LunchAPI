from django.conf import settings
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        CONFIRMED = "confirmed"
        PREPARING = "preparing"
        READY = "ready"
        DELIVERING = "delivering"
        DELIVERED = "delivered"
        CANCELLED = "cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    restaurant = models.ForeignKey("restaurants.Restaurant", on_delete=models.PROTECT, related_name="orders")
    courier = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                related_name="deliveries", limit_choices_to={"role": "delivery"})
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True)
    delivery_address = models.TextField()
    delivery_time = models.DateTimeField(null=True, blank=True)
    special_instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    # Menyu o'chirilsa ham buyurtma tarixi qolishi uchun SET_NULL + nom/narx snapshot
    menu_item = models.ForeignKey("restaurants.MenuItem", null=True, on_delete=models.SET_NULL, related_name="+")
    name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    special_notes = models.TextField(blank=True)
