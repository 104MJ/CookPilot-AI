"""Tests pour les vues sessions/recipes."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Profile

from .models import History, Recipe
from .recipe_generator import RecipeGenerationError


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
        self.assertEqual(len(response.data), 1)

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
