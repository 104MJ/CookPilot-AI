"""Tests pour le modele Profile et la vue profil."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Profile

User = get_user_model()


class ProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword123"
        )

    def test_profile_creation(self):
        profile, _ = Profile.objects.get_or_create(user=self.user)
        profile.diet = Profile.Diet.VEGETARIAN
        profile.allergies = ["arachides", "lactose"]
        profile.skill_level = Profile.SkillLevel.INTERMEDIATE
        profile.time_available_minutes = 25
        profile.save()

        self.assertEqual(profile.user.username, "testuser")
        self.assertEqual(profile.diet, Profile.Diet.VEGETARIAN)
        self.assertIn("arachides", profile.allergies)
        self.assertEqual(profile.time_available_minutes, 25)
        self.assertEqual(str(profile), "Profil de testuser")


class ProfileViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="test", password="test1234")
        self.client.force_authenticate(user=self.user)

    def test_profile_auto_created_with_defaults(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["diet"], "none")
        self.assertEqual(response.data["skill_level"], "beginner")
        self.assertEqual(response.data["time_available_minutes"], 30)
        self.assertEqual(response.data["allergies"], [])

    def test_patch_updates_profile(self):
        response = self.client.patch(
            reverse("profile"),
            {
                "diet": "vegetarian",
                "allergies": ["arachides", "gluten"],
                "skill_level": "advanced",
                "time_available_minutes": 45,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["diet"], "vegetarian")
        self.assertEqual(response.data["allergies"], ["arachides", "gluten"])

        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.diet, "vegetarian")
        self.assertEqual(profile.skill_level, "advanced")
        self.assertEqual(profile.time_available_minutes, 45)

    def test_patch_partial_update(self):
        response = self.client.patch(
            reverse("profile"), {"diet": "vegan"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["diet"], "vegan")
        self.assertEqual(response.data["skill_level"], "beginner")  # inchange

    def test_patch_invalid_diet_rejected(self):
        response = self.client.patch(
            reverse("profile"), {"diet": "carnivore"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_invalid_time_rejected(self):
        response = self.client.patch(
            reverse("profile"), {"time_available_minutes": -5}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_allergies_must_be_list(self):
        response = self.client.patch(
            reverse("profile"), {"allergies": "gluten"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("profile"))
        # SessionAuthentication en premier -> pas de WWW-Authenticate -> 403 (pas 401)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
