from django.contrib.auth import get_user_model
from django.test import TestCase
from accounts.models import Profile

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
