from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Préférences et contraintes alimentaires de l'utilisateur, utilisées pour
    personnaliser les recettes générées par le moteur IA."""

    class Diet(models.TextChoices):
        NONE = "none", "Aucun régime particulier"
        VEGETARIAN = "vegetarian", "Végétarien"
        VEGAN = "vegan", "Végan"
        GLUTEN_FREE = "gluten_free", "Sans gluten"
        HALAL = "halal", "Halal"
        KOSHER = "kosher", "Casher"

    class SkillLevel(models.TextChoices):
        BEGINNER = "beginner", "Débutant"
        INTERMEDIATE = "intermediate", "Intermédiaire"
        ADVANCED = "advanced", "Avancé"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    diet = models.CharField(max_length=20, choices=Diet.choices, default=Diet.NONE)
    allergies = models.JSONField(default=list, blank=True)
    skill_level = models.CharField(
        max_length=20, choices=SkillLevel.choices, default=SkillLevel.BEGINNER
    )
    time_available_minutes = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profil de {self.user}"
