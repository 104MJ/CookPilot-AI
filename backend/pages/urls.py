from django.urls import path

from . import views

app_name = "pages"

urlpatterns = [
    path("", views.scan, name="scan"),
    path("sessions/<int:session_id>/", views.result, name="result"),
    path("history/", views.history, name="history"),
    path("profile/", views.profile, name="profile"),
]
