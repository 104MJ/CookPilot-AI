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
