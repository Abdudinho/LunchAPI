from rest_framework import serializers

from orders.models import Order
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "order", "amount", "payment_method", "status", "transaction_id", "created_at"]
        read_only_fields = fields


class PaymentCreateSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(choices=Payment.Method.choices)

    def validate(self, attrs):
        order = self.context["order"]
        if order.status == Order.Status.CANCELLED:
            raise serializers.ValidationError("Bekor qilingan buyurtma uchun to'lov yaratib bo'lmaydi.")
        if order.payments.exclude(status=Payment.Status.FAILED).exists():
            raise serializers.ValidationError("Bu buyurtma uchun to'lov allaqachon mavjud.")
        return attrs


class ConfirmSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["completed", "failed"], default="completed")
    transaction_id = serializers.CharField(required=False, allow_blank=True, max_length=128)
