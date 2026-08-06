"""Generation de recette via Mistral, a partir d'ingredients + profil."""

import json
import logging

from django.conf import settings
from mistralai.client import Mistral

logger = logging.getLogger("ai_engine")


class RecipeGenerationError(Exception):
    """Erreur lors de la generation (appel API ou reponse invalide)."""


def _build_prompt(ingredients, profile):
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

    return f"""Tu es un chef cuisinier. Propose UNE recette avec ces ingredients : {ingredients_text}.

Contraintes :
- Regime : {diet}
- Allergies a eviter : {', '.join(allergies) if allergies else 'aucune'}
- Niveau de cuisine : {skill_level}
- Temps disponible : {time_available} minutes
- Priorise les ingredients qui perissent bientot

Reponds UNIQUEMENT en JSON, avec exactement ce format :
{{
  "title": "nom de la recette",
  "ingredients_used": [{{"name": "riz", "quantity": "200g"}}],
  "ingredients_missing": ["sel"],
  "steps": ["etape 1", "etape 2"]
}}"""


def generate_recipe(ingredients, profile):
    """
    Genere une recette via Mistral.

    ingredients : liste de dicts {"name": str, "expires_at": str|None}
    profile : dict (diet, allergies, skill_level, time_available_minutes)

    Retourne un dict (title, ingredients_used, ingredients_missing, steps,
    raw_response). Leve RecipeGenerationError si l'appel echoue.
    """
    client = Mistral(api_key=settings.MISTRAL_API_KEY)
    prompt = _build_prompt(ingredients, profile)

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
    data["raw_response"] = raw_content
    return data
