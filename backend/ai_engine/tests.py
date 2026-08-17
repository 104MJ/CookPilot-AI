"""Tests pour les modeles et les vues de l'app ai_engine."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Profile

from .models import History, Recipe
from .recipe_generator import RecipeGenerationError
from .vision import detect_ingredients

User = get_user_model()


class AIEngineModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="chefuser",
            password="chefpassword123"
        )

    def test_history_and_recipe_creation(self):
        history = History.objects.create(
            user=self.user,
            detected_ingredients=[{"name": "tomate", "expires_at": "2026-08-10"}],
            manual_ingredients=[{"name": "lait", "expires_at": None}],
            status=History.Status.DONE
        )
        self.assertEqual(history.user.username, "chefuser")
        self.assertEqual(len(history.detected_ingredients), 1)

        recipe = Recipe.objects.create(
            history=history,
            title="Omelette Tomate-Fromage",
            ingredients_used=["tomate", "oeuf"],
            steps=["Battre les oeufs", "Cuire les tomates", "Servir chaud"],
            rating=1,
            total_calories=350
        )
        self.assertEqual(recipe.title, "Omelette Tomate-Fromage")
        self.assertEqual(recipe.total_calories, 350)
        self.assertEqual(recipe.rating, 1)
        self.assertEqual(str(recipe), "Omelette Tomate-Fromage")


class SessionViewsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test", password="test1234")
        Profile.objects.get_or_create(user=self.user, defaults={"diet": "vegetarian"})
        self.client.force_authenticate(user=self.user)

    @patch("ai_engine.views.generate_recipe")
    def test_create_session_manual_success(self, mock_generate):
        mock_generate.return_value = {
            "title": "Riz aux legumes",
            "ingredients_used": [{"name": "riz", "quantity": "200g"}],
            "ingredients_missing": ["sel"],
            "steps": ["Cuire le riz"],
            "raw_response": "{}",
        }

        response = self.client.post(
            reverse("session-list-create"),
            {"manual_ingredients": '["riz"]'},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "done")
        self.assertEqual(response.data["recipes"][0]["title"], "Riz aux legumes")
        self.assertEqual(History.objects.count(), 1)
        self.assertEqual(Recipe.objects.count(), 1)

    @patch("ai_engine.views.generate_recipe")
    def test_create_session_includes_nutrition(self, mock_generate):
        mock_generate.return_value = {
            "title": "Riz aux legumes",
            "ingredients_used": [{"name": "riz", "quantity": "200g"}],
            "ingredients_missing": [],
            "steps": ["Cuire le riz"],
            "total_calories": 420,
            "nutrition_breakdown": {"protein_g": 10, "carbs_g": 80, "fat_g": 5, "fiber_g": 2},
            "raw_response": "{}",
        }

        response = self.client.post(
            reverse("session-list-create"), {"manual_ingredients": '["riz"]'}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe_data = response.data["recipes"][0]
        self.assertEqual(recipe_data["total_calories"], 420)
        self.assertEqual(recipe_data["nutrition_breakdown"]["protein_g"], 10)

    @patch("ai_engine.views.generate_recipe")
    def test_create_session_includes_personalization_notes(self, mock_generate):
        mock_generate.return_value = {
            "title": "Riz aux legumes",
            "ingredients_used": [{"name": "riz", "quantity": "200g"}],
            "ingredients_missing": [],
            "steps": ["Cuire le riz"],
            "personalization_notes": "Pas de lait ajoute (allergie signalee).",
            "raw_response": "{}",
        }

        response = self.client.post(
            reverse("session-list-create"), {"manual_ingredients": '["riz"]'}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        recipe_data = response.data["recipes"][0]
        self.assertEqual(
            recipe_data["personalization_notes"], "Pas de lait ajoute (allergie signalee)."
        )

    @patch("ai_engine.views.generate_recipe")
    def test_create_session_mistral_error(self, mock_generate):
        mock_generate.side_effect = RecipeGenerationError("boom")

        response = self.client.post(
            reverse("session-list-create"),
            {"manual_ingredients": '["riz"]'},
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "failed")
        self.assertTrue(response.data["error_message"])

    def test_create_session_missing_input(self):
        response = self.client.post(reverse("session-list-create"), {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("ai_engine.views.generate_recipe")
    def test_get_session_detail(self, mock_generate):
        mock_generate.return_value = {
            "title": "Riz aux legumes",
            "ingredients_used": [],
            "ingredients_missing": [],
            "steps": [],
            "raw_response": "{}",
        }
        create_resp = self.client.post(
            reverse("session-list-create"), {"manual_ingredients": '["riz"]'}
        )
        session_id = create_resp.data["id"]

        response = self.client.get(reverse("session-detail", args=[session_id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], session_id)

    @patch("ai_engine.views.generate_recipe")
    def test_list_sessions(self, mock_generate):
        mock_generate.return_value = {
            "title": "Riz aux legumes",
            "ingredients_used": [],
            "ingredients_missing": [],
            "steps": [],
            "raw_response": "{}",
        }
        self.client.post(reverse("session-list-create"), {"manual_ingredients": '["riz"]'})

        response = self.client.get(reverse("session-list-create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

    @patch("ai_engine.views.generate_recipe")
    def test_rate_recipe(self, mock_generate):
        mock_generate.return_value = {
            "title": "Riz aux legumes",
            "ingredients_used": [],
            "ingredients_missing": [],
            "steps": [],
            "raw_response": "{}",
        }
        create_resp = self.client.post(
            reverse("session-list-create"), {"manual_ingredients": '["riz"]'}
        )
        recipe_id = create_resp.data["recipes"][0]["id"]

        response = self.client.post(
            reverse("recipe-rating", args=[recipe_id]), {"value": 1}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["rating"], 1)

    @patch("ai_engine.views.generate_recipe")
    def test_taste_history_influences_next_generation(self, mock_generate):
        mock_generate.return_value = {
            "title": "Riz aux legumes",
            "ingredients_used": [],
            "ingredients_missing": [],
            "steps": [],
            "raw_response": "{}",
        }

        # premiere recette, notee positivement
        first_resp = self.client.post(
            reverse("session-list-create"), {"manual_ingredients": '["riz"]'}
        )
        recipe_id = first_resp.data["recipes"][0]["id"]
        self.client.post(
            reverse("recipe-rating", args=[recipe_id]), {"value": 1}, format="json"
        )

        # deuxieme recette : generate_recipe doit recevoir l'historique des gouts
        self.client.post(reverse("session-list-create"), {"manual_ingredients": '["riz"]'})

        last_call_args = mock_generate.call_args
        taste_history = last_call_args.args[2]
        self.assertIn("Riz aux legumes", taste_history["liked"])


class DetectIngredientsFilterTests(TestCase):
    """detect_ingredients() doit ignorer les classes bruitees du dataset fusionne."""

    class _FakeBox:
        def __init__(self, class_id):
            self.cls = [class_id]

    class _FakeResult:
        def __init__(self, names, boxes):
            self.names = names
            self.boxes = boxes

    @patch("ai_engine.vision._get_model")
    def test_filters_numeric_and_undefined_classes(self, mock_get_model):
        names = {0: "tomate", 1: "11", 2: "undefined", 3: "oignon"}
        boxes = [self._FakeBox(class_id) for class_id in names]
        mock_get_model.return_value.predict.return_value = [
            self._FakeResult(names, boxes)
        ]

        result = detect_ingredients("fake/path.jpg")

        self.assertEqual(result, ["oignon", "tomate"])
