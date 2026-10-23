from rest_framework import serializers

from users.models import User
from .models import MenuItem, Restaurant


class RestaurantSerializer(serializers.ModelSerializer):
    """Oshpaz uchun: owner va is_active o'zgartirilmaydi."""

    class Meta:
        model = Restaurant
        fields = ["id", "name", "description", "phone", "address", "working_hours",
                  "is_active", "owner", "created_at"]
        read_only_fields = ["id", "is_active", "owner", "created_at"]


class RestaurantAdminSerializer(RestaurantSerializer):
    owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role="chef"),
                                               required=False, allow_null=True)

    class Meta(RestaurantSerializer.Meta):
        read_only_fields = ["id", "created_at"]


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ["id", "restaurant", "name", "description", "price", "category",
                  "image_url", "is_available", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_restaurant(self, restaurant):
        user = self.context["request"].user
        if user.role == "chef" and restaurant.owner_id != user.id:
            raise serializers.ValidationError("Bu restoran sizga tegishli emas.")
        return restaurant

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Narx 0 dan katta bo'lishi kerak.")
        return value
