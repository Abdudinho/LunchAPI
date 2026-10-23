from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from common.permissions import IsAdmin
from .models import User
from .serializers import AdminUserSerializer, ProfileSerializer, RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        refresh = RefreshToken.for_user(user)
        return Response({"user": UserSerializer(user).data,
                         "access": str(refresh.access_token), "refresh": str(refresh)},
                        status=status.HTTP_201_CREATED)


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutView(APIView):
    @extend_schema(request=LogoutSerializer, responses={205: None}, summary="Refresh tokenni bekor qilish")
    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            return Response({"detail": "refresh token majburiy"}, status=400)
        try:
            rt = RefreshToken(token)
            if str(rt.get("user_id")) != str(request.user.id):
                return Response({"detail": "Token sizga tegishli emas"}, status=403)
            rt.blacklist()
        except TokenError:
            return Response({"detail": "Token yaroqsiz"}, status=400)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class ProfileView(generics.RetrieveUpdateAPIView):
    http_method_names = ["get", "put", "head", "options"]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    queryset = User.objects.order_by("id")
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ["role", "is_active"]
    search_fields = ["name", "email", "phone"]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    http_method_names = ["get", "put", "delete", "head", "options"]
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAdmin]

    def perform_destroy(self, instance):
        # Buyurtmalar tarixi saqlanishi uchun soft-delete
        instance.is_active = False
        instance.save(update_fields=["is_active"])
