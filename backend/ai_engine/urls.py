"""Routes de l'app ai_engine."""

from django.urls import path

from .views import RecipeRatingView, SessionDetailView, SessionListCreateView

urlpatterns = [
    path("sessions/", SessionListCreateView.as_view(), name="session-list-create"),
    path("sessions/<int:pk>/", SessionDetailView.as_view(), name="session-detail"),
    path("recipes/<int:pk>/rating/", RecipeRatingView.as_view(), name="recipe-rating"),
]
