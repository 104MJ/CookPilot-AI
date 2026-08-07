"""Generation de recette via Mistral, a partir d'ingredients + profil."""

import json
import logging

from django.conf import settings
from mistralai.client import Mistral

logger = logging.getLogger("ai_engine")


class RecipeGenerationError(Exception):
    """Erreur lors de la generation (appel API ou reponse invalide)."""


def _build_prompt(ingredients, profile, taste_history=None):
    """Construit le prompt texte envoye a Mistral."""
    diet = profile.get("diet", "none")
    allergies = profile.get("allergies") or []
    skill_level = profile.get("skill_level", "beginner")
    time_available = profile.get("time_available_minutes", 30)

    # liste ingredients, avec flag peremption pour anti-gaspi
    ingredients_lines = []
    for ing in ingredients:
        line = ing["name"]
        if ing.get("expires_at"):
            line += " (perime bientot, a prioriser)"
        ingredients_lines.append(line)
    ingredients_text = ", ".join(ingredients_lines)

    # apprentissage des gouts : recettes aimees/pas aimees par le passe
    taste_section = ""
    if taste_history:
        liked = taste_history.get("liked") or []
        disliked = taste_history.get("disliked") or []
        if liked:
            taste_section += f"\n- L'utilisateur a aime : {', '.join(liked)}. Inspire-toi de ce style."
        if disliked:
            taste_section += f"\n- L'utilisateur n'a pas aime : {', '.join(disliked)}. Evite ce type de plat."

    return f"""Tu es un chef cuisinier. Propose UNE recette avec ces ingredients : {ingredients_text}.

Contraintes :
- Regime : {diet}
- Allergies a eviter : {', '.join(allergies) if allergies else 'aucune'}
- Niveau de cuisine : {skill_level}
- Temps disponible : {time_available} minutes
- Priorise les ingredients qui perissent bientot{taste_section}

Estime aussi les calories et macronutriments totaux de la recette (approximatif,
base sur ta connaissance nutritionnelle generale).

Explique aussi brievement (2-3 phrases max) les choix lies au profil : pourquoi
un ingredient a ete ecarte ou une quantite adaptee (regime, allergie, gout passe
aime/evite, peremption). Sois concret et nomme les ingredients/contraintes
concernes, pas de formule generique.

Reponds UNIQUEMENT en JSON, avec exactement ce format :
{{
  "title": "nom de la recette",
  "ingredients_used": [{{"name": "riz", "quantity": "200g"}}],
  "ingredients_missing": ["sel"],
  "steps": ["etape 1", "etape 2"],
  "total_calories": 450,
  "nutrition_breakdown": {{"protein_g": 20, "carbs_g": 60, "fat_g": 10, "fiber_g": 4}},
  "personalization_notes": "explication courte des choix lies au profil"
}}"""


def generate_recipe(ingredients, profile, taste_history=None):
    """
    Genere une recette via Mistral.

    ingredients : liste de dicts {"name": str, "expires_at": str|None}
    profile : dict (diet, allergies, skill_level, time_available_minutes)
    taste_history : dict optionnel {"liked": [titres], "disliked": [titres]}

    Retourne un dict (title, ingredients_used, ingredients_missing, steps,
    raw_response). Leve RecipeGenerationError si l'appel echoue.
    """
    client = Mistral(api_key=settings.MISTRAL_API_KEY)
    prompt = _build_prompt(ingredients, profile, taste_history)

    try:
        response = client.chat.complete(
            model=settings.MISTRAL_CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
    except Exception as exc:
        logger.error("Erreur appel Mistral : %s", exc)
        raise RecipeGenerationError("Echec de l'appel a Mistral") from exc

    raw_content = response.choices[0].message.content

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        logger.error("Reponse Mistral non-JSON : %s", raw_content)
        raise RecipeGenerationError("Reponse invalide du modele") from exc

    # champs manquants -> valeurs par defaut, pas de crash
    data.setdefault("ingredients_used", [])
    data.setdefault("ingredients_missing", [])
    data.setdefault("steps", [])
    data.setdefault("total_calories", None)
    data.setdefault("nutrition_breakdown", {})
    data.setdefault("personalization_notes", "")
    data["raw_response"] = raw_content
    return data
