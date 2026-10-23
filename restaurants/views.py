from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import SAFE_METHODS, AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MenuItem
from .selectors import visible_menu_items, visible_restaurants
from .serializers import MenuItemSerializer, RestaurantAdminSerializer, RestaurantSerializer


class RestaurantPermission(BasePermission):
    """GET - hamma; POST/DELETE - admin; PUT/PATCH - admin yoki o'z restorani oshpazi."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        if not (u and u.is_authenticated):
            return False
        if request.method in ("PUT", "PATCH"):
            return u.role in ("admin", "chef")
        return u.role == "admin"

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or request.user.role == "admin":
            return True
        return obj.owner_id == request.user.id


class MenuItemPermission(BasePermission):
    """GET - hamma; yozish - admin yoki o'z restorani oshpazi."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        return bool(u and u.is_authenticated and u.role in ("admin", "chef"))

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or request.user.role == "admin":
            return True
        return obj.restaurant.owner_id == request.user.id


class RestaurantSerializerMixin:
    def get_serializer_class(self):
        u = self.request.user
        if u.is_authenticated and u.role == "admin":
            return RestaurantAdminSerializer
        return RestaurantSerializer

    def get_queryset(self):
        return visible_restaurants(self.request.user)


class RestaurantListCreateView(RestaurantSerializerMixin, generics.ListCreateAPIView):
    permission_classes = [RestaurantPermission]
    filterset_fields = ["is_active"]
    search_fields = ["name", "description", "address"]


class RestaurantDetailView(RestaurantSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ["get", "put", "delete", "head", "options"]
    permission_classes = [RestaurantPermission]

    def perform_destroy(self, instance):
        # Buyurtmalar tarixi saqlanishi uchun soft-delete
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class RestaurantMenuView(generics.ListAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return MenuItem.objects.none()
        restaurant = get_object_or_404(visible_restaurants(self.request.user), pk=self.kwargs["pk"])
        return visible_menu_items(self.request.user).filter(restaurant=restaurant)


class MenuCategoriesView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(responses={200: {"type": "array", "items": {"type": "string"}}}, summary="Menyu kategoriyalari")
    def get(self, request):
        cats = (visible_menu_items(request.user).exclude(category="")
                .values_list("category", flat=True).distinct().order_by("category"))
        return Response(list(cats))


class MenuItemListCreateView(generics.ListCreateAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [MenuItemPermission]
    filterset_fields = {"restaurant": ["exact"], "category": ["exact"], "is_available": ["exact"],
                        "price": ["gte", "lte"]}
    search_fields = ["name", "description"]
    ordering_fields = ["price", "name", "created_at"]

    def get_queryset(self):
        return visible_menu_items(self.request.user)


class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ["get", "put", "delete", "head", "options"]
    serializer_class = MenuItemSerializer
    permission_classes = [MenuItemPermission]

    def get_queryset(self):
        return visible_menu_items(self.request.user)
