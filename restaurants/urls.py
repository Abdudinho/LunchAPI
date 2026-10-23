from django.urls import path

from . import views

urlpatterns = [
    path("restaurants", views.RestaurantListCreateView.as_view()),
    path("restaurants/<int:pk>", views.RestaurantDetailView.as_view()),
    path("restaurants/<int:pk>/menu", views.RestaurantMenuView.as_view()),
    path("menu/categories", views.MenuCategoriesView.as_view()),
    path("menu/items", views.MenuItemListCreateView.as_view()),
    path("menu/items/<int:pk>", views.MenuItemDetailView.as_view()),
]
