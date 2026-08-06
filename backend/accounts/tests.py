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
        profile = Profile.objects.create(
            user=self.user,
            diet=Profile.Diet.VEGETARIAN,
            allergies=["arachides", "lactose"],
            skill_level=Profile.SkillLevel.INTERMEDIATE,
            time_available_minutes=25
        )
        self.assertEqual(profile.user.username, "testuser")
        self.assertEqual(profile.diet, Profile.Diet.VEGETARIAN)
        self.assertIn("arachides", profile.allergies)
        self.assertEqual(profile.time_available_minutes, 25)
        self.assertEqual(str(profile), "Profil de testuser")
