from django.contrib.auth import get_user_model
from django.test import TestCase
from ai_engine.models import History, Recipe

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


"""Tests pour la vue de generation de recette."""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Profile

from .models import History, Recipe
from .recipe_generator import RecipeGenerationError


class GenerateRecipeViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test", password="test1234")
        Profile.objects.create(user=self.user, diet="vegetarian")
        self.client.force_authenticate(user=self.user)

    @patch("ai_engine.views.generate_recipe")
    def test_generate_recipe_success(self, mock_generate):
        mock_generate.return_value = {
            "title": "Riz aux legumes",
            "ingredients_used": [{"name": "riz", "quantity": "200g"}],
            "ingredients_missing": ["sel"],
            "steps": ["Cuire le riz"],
            "raw_response": "{}",
        }

        response = self.client.post(
            reverse("generate-recipe"),
            {"ingredients": [{"name": "riz", "expires_at": None}]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["recipe"]["title"], "Riz aux legumes")
        self.assertEqual(History.objects.count(), 1)
        self.assertEqual(Recipe.objects.count(), 1)
        self.assertEqual(History.objects.first().status, History.Status.DONE)

    @patch("ai_engine.views.generate_recipe")
    def test_generate_recipe_mistral_error(self, mock_generate):
        mock_generate.side_effect = RecipeGenerationError("boom")

        response = self.client.post(
            reverse("generate-recipe"),
            {"ingredients": [{"name": "riz"}]},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(History.objects.first().status, History.Status.FAILED)

    def test_generate_recipe_missing_ingredients(self):
        response = self.client.post(reverse("generate-recipe"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
