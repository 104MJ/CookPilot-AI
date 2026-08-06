"""Routes de l'app ai_engine."""

from django.urls import path

from .views import GenerateRecipeView

urlpatterns = [
    path("recipes/generate/", GenerateRecipeView.as_view(), name="generate-recipe"),
]
