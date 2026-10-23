from django.urls import path

from . import views

urlpatterns = [
    path("orders/<int:pk>/payments", views.OrderPaymentsView.as_view()),
    path("payments/methods", views.PaymentMethodsView.as_view()),
    path("payments/<int:pk>/confirm", views.PaymentConfirmView.as_view()),
]
