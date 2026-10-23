from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "phone", "role", "office_address", "created_at", "updated_at"]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    # Ochiq ro'yxatdan o'tishda admin roli berilmaydi
    role = serializers.ChoiceField(choices=["employee", "chef", "delivery"], default="employee")

    class Meta:
        model = User
        fields = ["name", "email", "phone", "password", "role", "office_address"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "phone", "role", "office_address"]
        read_only_fields = ["id", "email", "role"]


class AdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "name", "email", "phone", "role", "office_address", "is_active",
                  "password", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=["password"])
        return instance
