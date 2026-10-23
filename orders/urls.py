from django.urls import path

from . import views

urlpatterns = [
    path("orders", views.OrderListCreateView.as_view()),
    path("orders/my", views.MyOrdersView.as_view()),
    path("orders/<int:pk>", views.OrderDetailView.as_view()),
    path("orders/<int:pk>/status", views.OrderStatusView.as_view()),
    path("users/<int:user_id>/orders", views.UserOrdersView.as_view()),
    path("restaurants/<int:restaurant_id>/orders", views.RestaurantOrdersView.as_view()),
]
