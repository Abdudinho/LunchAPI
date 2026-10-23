from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsAdmin, IsChefOrAdmin, IsEmployeeOrAdmin, roles
from .filters import OrderFilter
from .models import Order
from .selectors import orders_for
from .serializers import (OrderCreateSerializer, OrderSerializer, OrderUpdateSerializer, StatusSerializer)
from .services import change_status

UPDATABLE = {
    "employee": {"delivery_address", "delivery_time", "special_instructions"},
    "chef": {"special_instructions"},
    "delivery": {"special_instructions"},
    "admin": {"delivery_address", "delivery_time", "special_instructions"},
}


@extend_schema_view(
    get=extend_schema(summary="Barcha buyurtmalar (admin)"),
    post=extend_schema(request=OrderCreateSerializer, responses={201: OrderSerializer}, summary="Buyurtma berish"),
)
class OrderListCreateView(generics.ListCreateAPIView):
    """GET - faqat admin; POST - xodim/admin."""
    filterset_class = OrderFilter
    ordering_fields = ["created_at", "total_amount"]

    def get_permissions(self):
        return [IsAdmin()] if self.request.method == "GET" else [IsEmployeeOrAdmin()]

    def get_serializer_class(self):
        return OrderSerializer if self.request.method == "GET" else OrderCreateSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        return orders_for(self.request.user)

    def create(self, request, *args, **kwargs):
        ser = OrderCreateSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        order = ser.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


@extend_schema(summary="Mening buyurtmalarim (rolga qarab)",
               description="Xodim: o'zi bergan buyurtmalar. Oshpaz: o'z restoranidagilar. "
                           "Yetkazuvchi: o'ziga tayinlanganlar. Admin: hammasi.")
class MyOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    filterset_class = OrderFilter
    ordering_fields = ["created_at", "total_amount"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        return orders_for(self.request.user)


@extend_schema_view(
    get=extend_schema(summary="Bitta buyurtma"),
    put=extend_schema(request=OrderUpdateSerializer, responses=OrderSerializer,
                      summary="Buyurtmani tahrirlash (manzil, vaqt, izoh)"),
    delete=extend_schema(summary="Buyurtmani o'chirish"),
)
class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderSerializer
    http_method_names = ["get", "put", "delete", "head", "options"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        return orders_for(self.request.user)

    def update(self, request, *args, **kwargs):
        order = self.get_object()
        role = request.user.role
        if role == "employee" and order.status != Order.Status.PENDING:
            raise PermissionDenied("Faqat 'pending' buyurtmani o'zgartirish mumkin.")
        allowed = UPDATABLE.get(role, set())
        data = {k: v for k, v in request.data.items() if k in allowed}
        ser = OrderUpdateSerializer(order, data=data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(OrderSerializer(self.get_object()).data)

    def destroy(self, request, *args, **kwargs):
        order = self.get_object()
        role = request.user.role
        if role == "employee":
            if order.status != Order.Status.PENDING:
                raise PermissionDenied("Faqat 'pending' buyurtmani o'chirish mumkin.")
        elif role != "admin":
            raise PermissionDenied()
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrderStatusView(APIView):
    """Oshpaz, yetkazuvchi va admin shu bitta endpoint orqali status o'zgartiradi."""
    permission_classes = [roles("chef", "delivery", "admin")]

    @extend_schema(request=StatusSerializer, responses=OrderSerializer,
                   summary="Buyurtma statusini o'zgartirish",
                   description="Oshpaz: confirmed, preparing, ready, cancelled. "
                               "Yetkazuvchi: delivering, delivered. Admin: istalgani.")
    def put(self, request, pk):
        order = get_object_or_404(orders_for(request.user), pk=pk)
        ser = StatusSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        order = change_status(order, ser.validated_data["status"], request.user)
        return Response(OrderSerializer(order).data)


@extend_schema(tags=["orders"], summary="Foydalanuvchining buyurtmalari (o'zi yoki admin)")
class UserOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsEmployeeOrAdmin]
    filterset_class = OrderFilter

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        uid = self.kwargs["user_id"]
        if self.request.user.role != "admin" and uid != self.request.user.id:
            raise PermissionDenied("Faqat o'z buyurtmalaringizni ko'rishingiz mumkin.")
        return orders_for(self.request.user).filter(user_id=uid)


@extend_schema(tags=["orders"], summary="Restoranga kelgan buyurtmalar (o'z oshpazi yoki admin)")
class RestaurantOrdersView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [IsChefOrAdmin]
    filterset_class = OrderFilter

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        return orders_for(self.request.user).filter(restaurant_id=self.kwargs["restaurant_id"])
