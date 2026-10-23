from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import roles
from orders.models import Order
from orders.selectors import orders_for
from orders.serializers import OrderSerializer
from users.models import User


class AssignSerializer(serializers.Serializer):
    courier = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role="delivery", is_active=True))


class AssignCourierView(APIView):
    permission_classes = [roles("admin")]

    @extend_schema(tags=["delivery"], request=AssignSerializer, responses=OrderSerializer,
                   summary="Buyurtmaga yetkazuvchi tayinlash (admin)")
    def put(self, request, pk):
        order = get_object_or_404(orders_for(request.user), pk=pk)
        if order.status in (Order.Status.DELIVERED, Order.Status.CANCELLED, Order.Status.PENDING):
            return Response({"detail": f"'{order.status}' holatdagi buyurtmaga yetkazuvchi tayinlab bo'lmaydi."},
                            status=400)
        ser = AssignSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        order.courier = ser.validated_data["courier"]
        order.save(update_fields=["courier", "updated_at"])
        return Response(OrderSerializer(order).data)


TRACK = inline_serializer("TrackResponse", {
    "order_id": serializers.IntegerField(),
    "status": serializers.CharField(),
    "courier": inline_serializer("TrackCourier", {"id": serializers.IntegerField(), "name": serializers.CharField(),
                                                  "phone": serializers.CharField()}, allow_null=True),
    "delivery_address": serializers.CharField(),
    "delivery_time": serializers.DateTimeField(allow_null=True),
    "updated_at": serializers.DateTimeField(),
})


class TrackView(APIView):
    @extend_schema(tags=["delivery"], responses=TRACK, summary="Buyurtmani kuzatish (holat va yetkazuvchi)")
    def get(self, request, pk):
        order = get_object_or_404(orders_for(request.user), pk=pk)
        c = order.courier
        return Response({
            "order_id": order.id,
            "status": order.status,
            "courier": {"id": c.id, "name": c.name, "phone": c.phone} if c else None,
            "delivery_address": order.delivery_address,
            "delivery_time": order.delivery_time,
            "updated_at": order.updated_at,
        })
