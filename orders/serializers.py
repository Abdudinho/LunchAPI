from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from restaurants.models import MenuItem, Restaurant
from users.models import User
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "menu_item", "name", "quantity", "price", "special_notes"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    courier_name = serializers.CharField(source="courier.name", read_only=True, default=None)

    class Meta:
        model = Order
        fields = ["id", "user", "user_name", "restaurant", "restaurant_name", "courier", "courier_name",
                  "total_amount", "status", "delivery_address", "delivery_time", "special_instructions",
                  "items", "created_at", "updated_at"]
        read_only_fields = fields


class OrderItemInputSerializer(serializers.Serializer):
    menu_item = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.select_related("restaurant"))
    quantity = serializers.IntegerField(min_value=1, max_value=100)
    special_notes = serializers.CharField(required=False, allow_blank=True, default="")


class OrderCreateSerializer(serializers.Serializer):
    restaurant = serializers.PrimaryKeyRelatedField(queryset=Restaurant.objects.filter(is_active=True))
    items = OrderItemInputSerializer(many=True, allow_empty=False)
    delivery_address = serializers.CharField(required=False, allow_blank=True)
    delivery_time = serializers.DateTimeField(required=False, allow_null=True)
    special_instructions = serializers.CharField(required=False, allow_blank=True, default="")
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True), required=False)

    def _target_user(self, attrs):
        actor = self.context["request"].user
        return attrs.get("user") if actor.role == "admin" and attrs.get("user") else actor

    def validate(self, attrs):
        restaurant = attrs["restaurant"]
        for it in attrs["items"]:
            mi = it["menu_item"]
            if mi.restaurant_id != restaurant.id:
                raise serializers.ValidationError(f"'{mi.name}' bu restoranga tegishli emas.")
            if not mi.is_available:
                raise serializers.ValidationError(f"'{mi.name}' hozir mavjud emas.")
        dt = attrs.get("delivery_time")
        if dt and dt <= timezone.now():
            raise serializers.ValidationError({"delivery_time": "Yetkazish vaqti kelajakda bo'lishi kerak."})
        address = attrs.get("delivery_address") or self._target_user(attrs).office_address
        if not address:
            raise serializers.ValidationError({"delivery_address": "Manzil kiriting."})
        attrs["delivery_address"] = address
        return attrs

    @transaction.atomic
    def create(self, vd):
        order = Order.objects.create(
            user=self._target_user(vd), restaurant=vd["restaurant"],
            delivery_address=vd["delivery_address"], delivery_time=vd.get("delivery_time"),
            special_instructions=vd.get("special_instructions", ""))
        total = Decimal("0")
        for it in vd["items"]:
            mi = it["menu_item"]
            OrderItem.objects.create(order=order, menu_item=mi, name=mi.name, quantity=it["quantity"],
                                     price=mi.price, special_notes=it["special_notes"])
            total += mi.price * it["quantity"]
        order.total_amount = total
        order.save(update_fields=["total_amount"])
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["delivery_address", "delivery_time", "special_instructions"]

    def validate_delivery_time(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("Yetkazish vaqti kelajakda bo'lishi kerak.")
        return value


class StatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
