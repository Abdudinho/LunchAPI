from django.urls import path

from . import views

urlpatterns = [
    path("orders/<int:pk>/courier", views.AssignCourierView.as_view()),
    path("orders/<int:pk>/track", views.TrackView.as_view()),
]
