"""Vue API : saisie manuelle d'ingredients -> recette generee."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import History, Recipe
from .recipe_generator import RecipeGenerationError, generate_recipe


class GenerateRecipeView(APIView):
    """POST /api/recipes/generate/ : ingredients -> recette (MVP saisie manuelle)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        ingredients = request.data.get("ingredients")
        if not ingredients:
            return Response(
                {"error": "Le champ 'ingredients' est requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = request.user.profile
        profile_data = {
            "diet": profile.diet,
            "allergies": profile.allergies,
            "skill_level": profile.skill_level,
            "time_available_minutes": profile.time_available_minutes,
        }

        # session creee avant l'appel IA, pour tracer meme en cas d'echec
        history = History.objects.create(
            user=request.user,
            manual_ingredients=ingredients,
            status=History.Status.PROCESSING,
        )

        try:
            result = generate_recipe(ingredients, profile_data)
        except RecipeGenerationError:
            history.status = History.Status.FAILED
            history.save(update_fields=["status"])
            return Response(
                {"error": "Generation impossible pour le moment. Reessaie plus tard."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        recipe = Recipe.objects.create(
            history=history,
            title=result["title"],
            ingredients_used=result["ingredients_used"],
            ingredients_missing=result["ingredients_missing"],
            steps=result["steps"],
            raw_response=result["raw_response"],
        )

        history.status = History.Status.DONE
        history.save(update_fields=["status"])

        return Response(
            {
                "history_id": history.id,
                "status": history.status,
                "recipe": {
                    "id": recipe.id,
                    "title": recipe.title,
                    "ingredients_used": recipe.ingredients_used,
                    "ingredients_missing": recipe.ingredients_missing,
                    "steps": recipe.steps,
                },
            },
            status=status.HTTP_201_CREATED,
        )
