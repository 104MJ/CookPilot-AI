"""Vues API : sessions d'analyse frigo + notation des recettes.

Contrat aligne sur static/js/api.js (mock frontend) :
  POST /api/sessions/         -> cree une session, lance le traitement
  GET  /api/sessions/         -> liste les sessions de l'utilisateur
  GET  /api/sessions/<id>/    -> detail d'une session (statut + recettes)
  POST /api/recipes/<id>/rating/ -> note une recette (-1 / 1)
"""

import json
import logging

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import History, Recipe
from .recipe_generator import RecipeGenerationError, generate_recipe

logger = logging.getLogger("ai_engine")

QUOTA_ERROR_MESSAGE = "Quota de l'API IA dépassé. Réessayez dans quelques minutes."
DETECTION_ERROR_MESSAGE = (
    "Aucun ingrédient reconnaissable sur cette photo. Essayez la saisie manuelle."
)


def serialize_recipe(recipe):
    """Recipe -> dict, format attendu par le frontend."""
    return {
        "id": recipe.id,
        "title": recipe.title,
        "ingredients_used": recipe.ingredients_used,
        "ingredients_missing": recipe.ingredients_missing,
        "steps": recipe.steps,
        "rating": recipe.rating,
        "total_calories": recipe.total_calories,
        "nutrition_breakdown": recipe.nutrition_breakdown,
        "personalization_notes": recipe.personalization_notes,
    }


def serialize_session(history, request):
    """History -> dict, format attendu par le frontend."""
    photo_url = request.build_absolute_uri(history.photo.url) if history.photo else None
    return {
        "id": history.id,
        "status": history.status,
        "photo_url": photo_url,
        "error_message": history.error_message,
        "detected_ingredients": history.detected_ingredients,
        "manual_ingredients": history.manual_ingredients,
        "created_at": history.created_at.isoformat(),
        "recipes": [serialize_recipe(r) for r in history.recipes.all()],
    }


def _parse_manual_ingredients(request):
    """Lit manual_ingredients depuis le body (JSON string ou liste)."""
    raw = request.data.get("manual_ingredients")
    if not raw:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            raw = [raw]
    return [{"name": name, "expires_at": None} for name in raw]


class SessionListCreateView(APIView):
    """GET /api/sessions/ et POST /api/sessions/."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        sessions = History.objects.filter(user=request.user).order_by("-created_at")
        return Response([serialize_session(s, request) for s in sessions])

    def post(self, request):
        photo = request.FILES.get("photo")
        manual_ingredients = _parse_manual_ingredients(request)

        if not photo and not manual_ingredients:
            return Response(
                {"error": "Fournissez une photo ou des ingrédients manuels."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        history = History.objects.create(
            user=request.user,
            photo=photo,
            manual_ingredients=manual_ingredients,
            status=History.Status.PROCESSING,
        )

        # ingredients manuels prioritaires ; sinon detection photo
        if manual_ingredients:
            ingredients_for_recipe = manual_ingredients
        else:
            ingredients_for_recipe = self._run_detection(history)
            if ingredients_for_recipe is None:
                return Response(
                    serialize_session(history, request), status=status.HTTP_201_CREATED
                )

        return self._generate_and_respond(history, ingredients_for_recipe, request)

    def _run_detection(self, history):
        """Detection YOLOv8 sur la photo. None si echec (history deja marque failed)."""
        try:
            from .vision import detect_ingredients  # import tardif : torch est lourd
        except ImportError as exc:
            logger.error("Module vision indisponible : %s", exc)
            history.status = History.Status.FAILED
            history.error_message = DETECTION_ERROR_MESSAGE
            history.save(update_fields=["status", "error_message"])
            return None

        try:
            names = detect_ingredients(history.photo.path)
        except Exception as exc:
            logger.error("Erreur detection YOLOv8 : %s", exc)
            names = []

        if not names:
            history.status = History.Status.FAILED
            history.error_message = DETECTION_ERROR_MESSAGE
            history.save(update_fields=["status", "error_message"])
            return None

        detected = [{"name": n, "expires_at": None} for n in names]
        history.detected_ingredients = detected
        history.save(update_fields=["detected_ingredients"])
        return detected

    def _get_taste_history(self, user):
        """Recettes aimees/pas aimees par le passe, pour personnaliser la generation."""
        liked = list(
            Recipe.objects.filter(history__user=user, rating=1)
            .order_by("-created_at")
            .values_list("title", flat=True)[:5]
        )
        disliked = list(
            Recipe.objects.filter(history__user=user, rating=-1)
            .order_by("-created_at")
            .values_list("title", flat=True)[:5]
        )
        return {"liked": liked, "disliked": disliked}

    def _generate_and_respond(self, history, ingredients, request):
        """Appelle Mistral, cree la Recipe, met a jour le statut."""
        profile = request.user.profile
        profile_data = {
            "diet": profile.diet,
            "allergies": profile.allergies,
            "skill_level": profile.skill_level,
            "time_available_minutes": profile.time_available_minutes,
        }
        taste_history = self._get_taste_history(request.user)

        try:
            result = generate_recipe(ingredients, profile_data, taste_history)
        except RecipeGenerationError:
            history.status = History.Status.FAILED
            history.error_message = QUOTA_ERROR_MESSAGE
            history.save(update_fields=["status", "error_message"])
            return Response(
                serialize_session(history, request), status=status.HTTP_201_CREATED
            )

        # calories/macros : estimees par Mistral directement (voir _build_prompt)
        Recipe.objects.create(
            history=history,
            title=result["title"],
            ingredients_used=result["ingredients_used"],
            ingredients_missing=result["ingredients_missing"],
            steps=result["steps"],
            raw_response=result["raw_response"],
            total_calories=result.get("total_calories"),
            nutrition_breakdown=result.get("nutrition_breakdown") or {},
            personalization_notes=result.get("personalization_notes") or "",
        )
        history.status = History.Status.DONE
        history.save(update_fields=["status"])

        return Response(serialize_session(history, request), status=status.HTTP_201_CREATED)


class SessionDetailView(APIView):
    """GET /api/sessions/<id>/."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        history = get_object_or_404(History, pk=pk, user=request.user)
        return Response(serialize_session(history, request))


class RecipeRatingView(APIView):
    """POST /api/recipes/<id>/rating/  {"value": -1|1|null}."""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        recipe = get_object_or_404(Recipe, pk=pk, history__user=request.user)
        value = request.data.get("value")
        if value not in (-1, 1, None):
            return Response(
                {"error": "value doit etre -1, 1 ou null"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        recipe.rating = value
        recipe.save(update_fields=["rating"])
        return Response(serialize_recipe(recipe))
