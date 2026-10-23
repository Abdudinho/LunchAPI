from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdmin, IsEmployeeOrAdmin, roles
from orders.selectors import orders_for
from .models import Payment
from .serializers import ConfirmSerializer, PaymentCreateSerializer, PaymentSerializer


class OrderPaymentsView(APIView):
    """GET - buyurtma to'lovlari; POST - buyurtma uchun to'lov yaratish."""

    def get_permissions(self):
        cls = IsEmployeeOrAdmin if self.request.method == "POST" else roles("employee", "chef", "admin")
        return [cls()]

    @extend_schema(tags=["payments"], responses=PaymentSerializer(many=True), summary="Buyurtma to'lovlari")
    def get(self, request, pk):
        order = get_object_or_404(orders_for(request.user), pk=pk)
        return Response(PaymentSerializer(order.payments.all(), many=True).data)

    @extend_schema(tags=["payments"], request=PaymentCreateSerializer, responses={201: PaymentSerializer},
                   summary="Buyurtma uchun to'lov yaratish")
    def post(self, request, pk):
        order = get_object_or_404(orders_for(request.user), pk=pk)
        ser = PaymentCreateSerializer(data=request.data, context={"order": order})
        ser.is_valid(raise_exception=True)
        payment = Payment.objects.create(order=order, amount=order.total_amount,
                                         payment_method=ser.validated_data["payment_method"])
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentConfirmView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(request=ConfirmSerializer, responses=PaymentSerializer, summary="To'lovni tasdiqlash (admin)")
    def put(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        if payment.status != Payment.Status.PENDING:
            return Response({"detail": "To'lov allaqachon qayta ishlangan."}, status=400)
        ser = ConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        payment.status = ser.validated_data["status"]
        payment.transaction_id = ser.validated_data.get("transaction_id", payment.transaction_id)
        payment.save(update_fields=["status", "transaction_id"])
        return Response(PaymentSerializer(payment).data)


class PaymentMethodsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses=inline_serializer("PaymentMethod", {"value": serializers.CharField(),
                                                                 "label": serializers.CharField()}, many=True),
                   summary="To'lov usullari")
    def get(self, request):
        return Response([{"value": v, "label": l} for v, l in Payment.Method.choices])
