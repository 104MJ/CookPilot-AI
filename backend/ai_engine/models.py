from django.conf import settings
from django.db import models


class History(models.Model):
    """Une session d'analyse de frigo : photo (ou saisie manuelle) + ingrédients
    détectés par YOLOv8. Sert de point d'entrée au pipeline IA."""

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        PROCESSING = "processing", "En cours"
        DONE = "done", "Terminé"
        FAILED = "failed", "Échec"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fridge_sessions",
    )
    photo = models.ImageField(upload_to="fridge_photos/", blank=True, null=True)
    # Chaque ingrédient : {"name": str, "expires_at": "YYYY-MM-DD" | null}
    # expires_at (optionnel, saisi par l'utilisateur) sert à prioriser les
    # recettes anti-gaspillage lors de la génération.
    detected_ingredients = models.JSONField(
        default=list,
        blank=True,
        help_text='Liste [{"name": str, "expires_at": "YYYY-MM-DD"|null}] issue de YOLOv8.',
    )
    manual_ingredients = models.JSONField(
        default=list,
        blank=True,
        help_text='Même format que detected_ingredients, saisi manuellement en fallback.',
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session #{self.pk} ({self.user})"


class Recipe(models.Model):
    """Recette générée par Mistral à partir d'une History.
    Correspond au modèle "Result" attendu par le cahier des charges
    (historique des générations IA)."""

    history = models.ForeignKey(
        History, on_delete=models.CASCADE, related_name="recipes"
    )
    title = models.CharField(max_length=255)
    ingredients_used = models.JSONField(default=list, blank=True)
    ingredients_missing = models.JSONField(default=list, blank=True)
    steps = models.JSONField(default=list, blank=True)
    raw_response = models.TextField(blank=True)
    rating = models.SmallIntegerField(null=True, blank=True)  # -1 dislike, 1 like
    total_calories = models.PositiveIntegerField(null=True, blank=True)
    nutrition_breakdown = models.JSONField(default=dict, blank=True)
    # explique les choix lies au profil (allergies exclues, regime, gouts passes...)
    personalization_notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
